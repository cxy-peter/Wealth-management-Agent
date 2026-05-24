"""FastAPI entrypoint for the wealth research assistant."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.app.agents.workflow import ResearchRequest, run_workflow
from backend.app.evaluation import run_evaluation
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

ROOT = Path(__file__).resolve().parents[2]

app = FastAPI(title="wealth-research-agent", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
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


class ReviewRequest(BaseModel):
    reviewer: str | None = None
    comment: str | None = None
    report_markdown: str | None = None


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "wealth-research-agent",
        "data_mode": "sample/mock",
        "workflow": "LangGraph with deterministic fallbacks",
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
