"""FastAPI entrypoint for the wealth research assistant."""
from __future__ import annotations

import base64
import csv
import io
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.app.agents.workflow import ResearchRequest, run_workflow
from backend.app.data_sources.manual_upload.excel_ingestor import preview_excel
from backend.app.data_sources.manual_upload.pdf_ingestor import preview_pdf
from backend.app.data_sources.manual_upload.ppt_ingestor import preview_ppt
from backend.app.data_sources.manual_upload.schema_mapper import suggest_mapping
from backend.app.data_sources.quality.data_quality_checker import check_required_metadata
from backend.app.data_sources.quality.freshness_checker import freshness_report
from backend.app.data_sources.quality.lineage_builder import lineage_for_evidence
from backend.app.data_sources.source_registry import list_data_sources, refresh_demo
from backend.app.evaluation import run_evaluation
from backend.app.external_verification.external_verification_agent import run_external_verification
from backend.app.benchmark.reference_rate_engine import compare_product_to_reference, load_reference_rates
from backend.app.product_taxonomy.manual_override_store import create_override, list_overrides
from backend.app.product_taxonomy.series_classifier import classify_products
from backend.app.product_taxonomy.series_compare import compare_series
from backend.app.product_taxonomy.series_performance import compute_series_performance
from backend.app.skills.skill_executor import execute_skill_harness
from backend.app.storage import (
    add_human_review,
    get_latest_report,
    get_run,
    list_events,
    list_tool_calls,
    update_run,
)
from backend.app.tools.data_loader import load_product_nav, load_product_risk_events, load_products
from backend.app.tools.product_benchmark import filter_products, peer_summary, product_detail
from backend.app.weekly_report.generators.benchmark_report_generator import (
    channel_benchmark,
    peer_benchmark,
    top_peers,
    weekly_product_detail,
)
from backend.app.weekly_report.generators.dpo_pair_generator import dpo_trace_sample
from backend.app.weekly_report.generators.weekly_report_generator import (
    generate_weekly_report,
    weekly_products,
    weekly_summary,
)
from backend.app.weekly_report.parsers.weekly_snapshot_parser import list_report_dates
from backend.app.weekly_report.weekly_report_verifier import verify_weekly_report

ROOT = Path(__file__).resolve().parents[2]
UPLOAD_INDEX = ROOT / "data" / "uploads" / "upload_index.json"
UPLOAD_STORE: dict[str, dict[str, Any]] = {}


def _allowed_origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", "")
    configured = [item.strip() for item in raw.split(",") if item.strip()]
    return configured or ["http://127.0.0.1:5173", "http://localhost:5173"]


app = FastAPI(title="wealth-research-agent", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    symbol: str = Field("600519", description="Instrument or product code")
    company: str = Field("贵州茅台", description="Company/product display name")
    analysis_type: str = Field("full", description="full/risk/product")
    risk_preference: str = Field("balanced", description="balanced/conservative/strict")
    output_path: str | None = Field(None, description="Optional markdown report path")


class ProductBenchmarkRequest(BaseModel):
    asset_class: str | None = None
    risk_level: str | None = None
    channel: str | None = None
    duration_bucket: str | None = None
    liquidity_type: str | None = None
    strategy_type: str | None = None


class EvalRunRequest(BaseModel):
    output_path: str | None = None


class WeeklyReportRequest(BaseModel):
    report_date: str | None = None
    product_series: str | None = None
    product_type: str | None = None
    channel: str | None = None
    risk_level: str | None = None
    benchmark_status: str | None = None
    open_type: str | None = None


class PeerBenchmarkRequest(BaseModel):
    product_code: str
    report_date: str | None = None
    limit: int = 12


class ChannelBenchmarkRequest(BaseModel):
    product_type: str | None = None
    channel: str | None = None


class TopPeersRequest(BaseModel):
    product_type: str | None = None
    report_date: str | None = None
    limit: int = 20


class ReviewRequest(BaseModel):
    reviewer: str | None = None
    comment: str | None = None
    report_markdown: str | None = None


class DataUploadRequest(BaseModel):
    file_name: str
    dataset_scope: str = Field(..., description="own_company/full_market/reference_rates")
    import_mode: str = "merge_with_demo"
    delete_synthetic: bool = False
    content_base64: str | None = None
    text: str | None = None
    target_schema: str = "product_weekly_snapshot"


class ConfirmMappingRequest(BaseModel):
    target_schema: str
    mapping: dict[str, str]


class RefreshDemoRequest(BaseModel):
    as_of_date: str | None = None
    base_date: str | None = None
    seed: int = 20260709
    n_products: int = 96


class ManualSeriesOverrideRequest(BaseModel):
    product_code: str
    product_name: str | None = ""
    old_series_id: str | None = ""
    new_series_id: str
    action_type: str = "move"
    reason: str = "manual correction"


class SkillHarnessRequest(BaseModel):
    user_task: str = "生成产品周报"
    task_payload: dict[str, Any] = Field(default_factory=dict)


class ExternalVerificationRequest(BaseModel):
    product_code: str = "AF245408"
    registry_code: str | None = None
    uploaded_nav: float | None = None
    report_text: str = ""


def _write_upload_index() -> None:
    UPLOAD_INDEX.parent.mkdir(parents=True, exist_ok=True)
    UPLOAD_INDEX.write_text(json.dumps({"uploads": list(UPLOAD_STORE.values())}, ensure_ascii=False, indent=2), encoding="utf-8")


def _decode_upload(req: DataUploadRequest) -> bytes:
    if req.content_base64:
        return base64.b64decode(req.content_base64)
    if req.text is not None:
        return req.text.encode("utf-8-sig")
    return b""


def _preview_csv(content: bytes, sample_rows: int = 5) -> dict[str, Any]:
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for _, row in zip(range(sample_rows), reader):
        rows.append(dict(row))
    return {
        "parser_status": "parsed",
        "file_type": "csv",
        "sheets": [{"sheet_name": "csv", "columns": reader.fieldnames or [], "sample_rows": rows}],
    }


def _preview_upload(req: DataUploadRequest) -> dict[str, Any]:
    suffix = Path(req.file_name).suffix.lower()
    content = _decode_upload(req)
    if suffix == ".csv":
        return _preview_csv(content)
    if suffix in {".xlsx", ".xls"}:
        return preview_excel(content)
    if suffix in {".pptx", ".ppt"}:
        return preview_ppt(content)
    if suffix == ".pdf":
        return preview_pdf(content)
    return {"parser_status": "unsupported_or_optional", "file_type": suffix.lstrip("."), "sheets": []}


def _preview_columns(preview: dict[str, Any]) -> list[str]:
    sheets = preview.get("sheets") or []
    if sheets:
        return [str(column) for column in sheets[0].get("columns", [])]
    return []


DATASET_SCOPE_SCHEMAS = {
    "own_company": {"product_weekly_snapshot", "product_nav_weekly", "product_scale_history", "product_benchmark_status"},
    "full_market": {"peer_product_universe", "peer_product_metrics", "channel_peer_universe", "top_peer_products"},
    "reference_rates": {"reference_rates"},
}

IMPORT_MODES = {"merge_with_demo", "replace_synthetic_for_scope", "session_only", "clear_scope_then_import"}


def _validate_dataset_scope(dataset_scope: str, target_schema: str) -> None:
    allowed = DATASET_SCOPE_SCHEMAS.get(dataset_scope)
    if allowed is None:
        raise HTTPException(status_code=422, detail="dataset_scope must be own_company, full_market, or reference_rates")
    if target_schema not in allowed:
        raise HTTPException(status_code=422, detail=f"target_schema {target_schema} is not allowed for dataset_scope {dataset_scope}")


def _validate_import_mode(import_mode: str) -> None:
    if import_mode not in IMPORT_MODES:
        raise HTTPException(status_code=422, detail="import_mode must be merge_with_demo, replace_synthetic_for_scope, session_only, or clear_scope_then_import")


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "wealth-research-agent",
        "data_mode": "sample/mock",
        "workflow": "weekly product research workbench with deterministic fallbacks",
    }


@app.get("/api/data-sources")
def get_data_sources() -> dict[str, Any]:
    return {"sources": list_data_sources()}


@app.get("/api/data/freshness")
def get_data_freshness() -> dict[str, Any]:
    return freshness_report()


@app.get("/api/data/lineage/{evidence_id}")
def get_data_lineage(evidence_id: str) -> dict[str, Any]:
    lineage = lineage_for_evidence(evidence_id)
    if not lineage.get("found"):
        raise HTTPException(status_code=404, detail="evidence_id not found")
    return lineage


@app.post("/api/data/refresh-demo")
def post_data_refresh_demo(req: RefreshDemoRequest | None = None) -> dict[str, Any]:
    req = req or RefreshDemoRequest()
    return refresh_demo(as_of_date=req.as_of_date, base_date=req.base_date, seed=req.seed, n_products=req.n_products)


@app.post("/api/data/upload")
def post_data_upload(req: DataUploadRequest) -> dict[str, Any]:
    _validate_dataset_scope(req.dataset_scope, req.target_schema)
    _validate_import_mode(req.import_mode)
    upload_id = f"upload_{uuid.uuid4().hex[:12]}"
    preview = _preview_upload(req)
    columns = _preview_columns(preview)
    mapping = suggest_mapping(columns, req.target_schema)
    record = {
        "upload_id": upload_id,
        "dataset_scope": req.dataset_scope,
        "import_mode": req.import_mode,
        "delete_synthetic": req.delete_synthetic,
        "source_type": "manual_upload",
        "source_name": req.target_schema,
        "source_url_or_file": f"manual_upload:{req.file_name}",
        "fetched_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "confidence_level": "user_uploaded",
        "file_name": req.file_name,
        "target_schema": req.target_schema,
        "parser_version": "backend_upload_parser.v2",
        "as_of_date": None,
        "evidence_id": f"ev_upload_{upload_id}",
        "parser_status": preview.get("parser_status"),
        "schema_preview": preview,
        "mapping_preview": mapping,
        "synthetic_action": "scope_synthetic_disabled"
        if (req.delete_synthetic or req.import_mode in {"replace_synthetic_for_scope", "clear_scope_then_import"})
        else "kept_demo_synthetic",
    }
    UPLOAD_STORE[upload_id] = record
    _write_upload_index()
    return {
        "upload_id": upload_id,
        "dataset_scope": req.dataset_scope,
        "import_mode": req.import_mode,
        "delete_synthetic": req.delete_synthetic,
        "source_type": "manual_upload",
        "source_name": req.target_schema,
        "source_url_or_file": f"manual_upload:{req.file_name}",
        "fetched_at": record["fetched_at"],
        "confidence_level": "user_uploaded",
        "file_name": req.file_name,
        "parser_version": "backend_upload_parser.v2",
        "as_of_date": None,
        "evidence_id": f"ev_upload_{upload_id}",
        "parser_status": preview.get("parser_status"),
        "mapping_preview": mapping,
        "synthetic_action": record["synthetic_action"],
    }


@app.get("/api/data/upload/{upload_id}/schema-preview")
def get_upload_schema_preview(upload_id: str) -> dict[str, Any]:
    record = UPLOAD_STORE.get(upload_id)
    if record is None:
        raise HTTPException(status_code=404, detail="upload_id not found")
    return {
        "upload_id": upload_id,
        "dataset_scope": record.get("dataset_scope"),
        "source_type": record.get("source_type", "manual_upload"),
        "file_name": record["file_name"],
        "target_schema": record["target_schema"],
        "schema_preview": record["schema_preview"],
        "mapping_preview": record["mapping_preview"],
    }


@app.post("/api/data/upload/{upload_id}/confirm-mapping")
def post_upload_confirm_mapping(upload_id: str, req: ConfirmMappingRequest) -> dict[str, Any]:
    record = UPLOAD_STORE.get(upload_id)
    if record is None:
        raise HTTPException(status_code=404, detail="upload_id not found")
    _validate_dataset_scope(record.get("dataset_scope", ""), req.target_schema)
    record["target_schema"] = req.target_schema
    record["confirmed_mapping"] = req.mapping
    record["mapping_confirmed"] = True
    _write_upload_index()
    return {"upload_id": upload_id, "mapping_confirmed": True, "target_schema": req.target_schema}


@app.get("/api/data/upload/{upload_id}/quality-report")
def get_upload_quality_report(upload_id: str) -> dict[str, Any]:
    record = UPLOAD_STORE.get(upload_id)
    if record is None:
        raise HTTPException(status_code=404, detail="upload_id not found")
    preview = record.get("schema_preview", {})
    rows = []
    for sheet in preview.get("sheets", []):
        rows.extend(sheet.get("sample_rows", []))
    metadata_check = check_required_metadata(rows) if rows else {"valid": False, "failure_count": 0, "failures": []}
    mapping = record.get("mapping_preview", {})
    return {
        "upload_id": upload_id,
        "dataset_scope": record.get("dataset_scope"),
        "source_type": record.get("source_type", "manual_upload"),
        "parser_status": record.get("parser_status"),
        "target_schema": record.get("target_schema"),
        "missing_required_fields": mapping.get("missing_required_fields", []),
        "metadata_required": metadata_check,
        "quality_status": "pass" if not mapping.get("missing_required_fields") else "needs_mapping",
    }


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest) -> dict[str, Any]:
    output_path = req.output_path or str(Path("reports") / f"{req.symbol}_research_report.md")
    return run_workflow(
        ResearchRequest(
            symbol=req.symbol,
            company=req.company,
            analysis_type=req.analysis_type,
            risk_preference=req.risk_preference,
            output_path=output_path,
        )
    )


@app.post("/api/analyze/jobs")
def create_analyze_job(req: AnalyzeRequest) -> dict[str, Any]:
    return analyze(req)


@app.get("/api/analyze/jobs/{run_id}")
def get_analyze_job(run_id: str) -> dict[str, Any]:
    run = get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run_id not found")
    run["tool_call_count"] = len(list_tool_calls(run_id))
    run["event_count"] = len(list_events(run_id))
    return run


@app.get("/api/analyze/jobs/{run_id}/events")
def get_analyze_job_events(run_id: str) -> dict[str, Any]:
    if get_run(run_id) is None:
        raise HTTPException(status_code=404, detail="run_id not found")
    return {"run_id": run_id, "events": list_events(run_id), "tool_calls": list_tool_calls(run_id)}


@app.get("/api/reports/{run_id}")
def get_report(run_id: str) -> dict[str, Any]:
    report = get_latest_report(run_id)
    if report is None:
        raise HTTPException(status_code=404, detail="report not found")
    return {"run_id": run_id, **report}


@app.post("/api/product-benchmark")
def product_benchmark(req: ProductBenchmarkRequest) -> dict[str, Any]:
    filters = req.model_dump(exclude_none=True)
    return peer_summary(load_products(), filters=filters)


def _frame_records(frame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    copy = frame.copy()
    for column in copy.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
        copy[column] = copy[column].dt.strftime("%Y-%m-%d")
    return copy.to_dict(orient="records")


@app.get("/api/products")
def list_products(
    asset_class: str | None = None,
    risk_level: str | None = None,
    channel: str | None = None,
    duration_bucket: str | None = None,
    liquidity_type: str | None = None,
    strategy_type: str | None = None,
) -> dict[str, Any]:
    products = load_products()
    filters = {
        key: value
        for key, value in {
            "asset_class": asset_class,
            "risk_level": risk_level,
            "channel": channel,
            "duration_bucket": duration_bucket,
            "liquidity_type": liquidity_type,
            "strategy_type": strategy_type,
        }.items()
        if value
    }
    filtered = filter_products(products, **filters)
    summary = peer_summary(products, filters=filters)
    return {
        "count": int(len(filtered)),
        "filters": filters,
        "filter_options": summary.get("filter_options", {}),
        "products": _frame_records(filtered),
    }


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict[str, Any]:
    detail = product_detail(load_products(), product_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="product_id not found")
    return detail


@app.get("/api/products/{product_id}/nav")
def get_product_nav(product_id: str) -> dict[str, Any]:
    nav = load_product_nav(product_id)
    if nav.empty:
        raise HTTPException(status_code=404, detail="product nav not found")
    return {"product_id": product_id, "records": _frame_records(nav)}


@app.get("/api/products/{product_id}/risk-events")
def get_product_risk_events(product_id: str) -> dict[str, Any]:
    events = load_product_risk_events(product_id)
    return {"product_id": product_id, "records": _frame_records(events)}


def _weekly_filters(
    product_series: str | None = None,
    product_type: str | None = None,
    channel: str | None = None,
    risk_level: str | None = None,
    benchmark_status: str | None = None,
    open_type: str | None = None,
) -> dict[str, Any]:
    return {
        key: value
        for key, value in {
            "product_series": product_series,
            "product_type": product_type,
            "channel": channel,
            "risk_level": risk_level,
            "benchmark_status": benchmark_status,
            "open_type": open_type,
        }.items()
        if value
    }


@app.get("/api/weekly-report/dates")
def weekly_report_dates() -> dict[str, Any]:
    dates = list_report_dates()
    return {"dates": dates, "latest": dates[-1] if dates else None}


@app.get("/api/weekly-report/summary")
def get_weekly_report_summary(
    report_date: str | None = None,
    product_series: str | None = None,
    product_type: str | None = None,
    channel: str | None = None,
    risk_level: str | None = None,
    benchmark_status: str | None = None,
    open_type: str | None = None,
) -> dict[str, Any]:
    return weekly_summary(
        report_date,
        _weekly_filters(product_series, product_type, channel, risk_level, benchmark_status, open_type),
    )


@app.get("/api/weekly-report/products")
def get_weekly_report_products(
    report_date: str | None = None,
    product_series: str | None = None,
    product_type: str | None = None,
    channel: str | None = None,
    risk_level: str | None = None,
    benchmark_status: str | None = None,
    open_type: str | None = None,
) -> dict[str, Any]:
    return weekly_products(
        report_date,
        _weekly_filters(product_series, product_type, channel, risk_level, benchmark_status, open_type),
    )


@app.get("/api/weekly-report/products/{product_code}")
def get_weekly_report_product(product_code: str, report_date: str | None = None) -> dict[str, Any]:
    detail = weekly_product_detail(product_code, report_date)
    if detail is None:
        raise HTTPException(status_code=404, detail="product_code not found")
    return detail


@app.post("/api/weekly-report/generate")
def post_weekly_report_generate(req: WeeklyReportRequest) -> dict[str, Any]:
    result = generate_weekly_report(
        req.report_date,
        _weekly_filters(req.product_series, req.product_type, req.channel, req.risk_level, req.benchmark_status, req.open_type),
    )
    result["verification_result"] = verify_weekly_report(result)
    result["dpo_trace"] = dpo_trace_sample(limit=2)
    return result


@app.post("/api/benchmark/peer")
def post_benchmark_peer(req: PeerBenchmarkRequest) -> dict[str, Any]:
    return peer_benchmark(req.product_code, report_date=req.report_date, limit=req.limit)


@app.post("/api/benchmark/channel")
def post_benchmark_channel(req: ChannelBenchmarkRequest) -> dict[str, Any]:
    return channel_benchmark(product_type=req.product_type, channel=req.channel)


@app.post("/api/benchmark/top-peers")
def post_benchmark_top_peers(req: TopPeersRequest) -> dict[str, Any]:
    return top_peers(product_type=req.product_type, report_date=req.report_date, limit=req.limit)


@app.get("/api/product-taxonomy/classify")
def get_product_taxonomy_classify(report_date: str | None = None) -> dict[str, Any]:
    return classify_products(report_date=report_date)


@app.post("/api/product-taxonomy/override")
def post_product_taxonomy_override(req: ManualSeriesOverrideRequest) -> dict[str, Any]:
    override = create_override(
        product_code=req.product_code,
        product_name=req.product_name or "",
        old_series_id=req.old_series_id or "",
        new_series_id=req.new_series_id,
        action_type=req.action_type,
        reason=req.reason,
    )
    performance = compute_series_performance()
    return {"override": override, "series_performance": performance}


@app.get("/api/product-taxonomy/overrides")
def get_product_taxonomy_overrides() -> dict[str, Any]:
    rows = list_overrides()
    return {"count": len(rows), "overrides": rows}


@app.get("/api/product-taxonomy/series-performance")
def get_product_taxonomy_series_performance(report_date: str | None = None) -> dict[str, Any]:
    return compute_series_performance(report_date=report_date)


@app.get("/api/product-taxonomy/series-compare")
def get_product_taxonomy_series_compare(series_ids: str | None = None, report_date: str | None = None) -> dict[str, Any]:
    ids = [item.strip() for item in series_ids.split(",") if item.strip()] if series_ids else None
    return compare_series(ids, report_date=report_date)


@app.get("/api/reference-rates")
def get_reference_rates(as_of_date: str | None = None) -> dict[str, Any]:
    rates = load_reference_rates(as_of_date)
    return {
        "count": int(len(rates)),
        "source_type": "synthetic_reference_rates",
        "rates": _frame_records(rates),
    }


@app.post("/api/benchmark/reference-rate")
def post_reference_rate_benchmark(payload: dict[str, Any]) -> dict[str, Any]:
    product = payload.get("product") or {}
    return compare_product_to_reference(product, payload.get("as_of_date"))


@app.post("/api/skills/run")
def post_skill_harness(req: SkillHarnessRequest) -> dict[str, Any]:
    return execute_skill_harness(req.user_task, req.task_payload)


@app.post("/api/external-verification/run")
def post_external_verification(req: ExternalVerificationRequest) -> dict[str, Any]:
    return run_external_verification(
        req.product_code,
        registry_code=req.registry_code,
        uploaded_nav=req.uploaded_nav,
        report_text=req.report_text,
    )


@app.post("/api/eval/run")
def eval_run(req: EvalRunRequest | None = None) -> dict[str, Any]:
    output_path = req.output_path if req else None
    return run_evaluation(output_path=output_path)


@app.post("/api/reviews/{run_id}/approve")
def approve_review(run_id: str, req: ReviewRequest | None = None) -> dict[str, Any]:
    if get_run(run_id) is None:
        raise HTTPException(status_code=404, detail="run_id not found")
    add_human_review(run_id, "approve", reviewer=req.reviewer if req else None, comment=req.comment if req else None)
    update_run(run_id, status="approved")
    return {"run_id": run_id, "status": "approved"}


@app.post("/api/reviews/{run_id}/edit")
def edit_review(run_id: str, req: ReviewRequest) -> dict[str, Any]:
    if get_run(run_id) is None:
        raise HTTPException(status_code=404, detail="run_id not found")
    add_human_review(
        run_id,
        "edit",
        reviewer=req.reviewer,
        edited_report=req.report_markdown,
        comment=req.comment,
    )
    update_run(run_id, status="edited")
    return {"run_id": run_id, "status": "edited"}


@app.post("/api/reviews/{run_id}/reject")
def reject_review(run_id: str, req: ReviewRequest | None = None) -> dict[str, Any]:
    if get_run(run_id) is None:
        raise HTTPException(status_code=404, detail="run_id not found")
    add_human_review(run_id, "reject", reviewer=req.reviewer if req else None, comment=req.comment if req else None)
    update_run(run_id, status="rejected")
    return {"run_id": run_id, "status": "rejected"}


@app.post("/analyze")
def analyze_legacy(req: AnalyzeRequest) -> dict[str, Any]:
    return analyze(req)
