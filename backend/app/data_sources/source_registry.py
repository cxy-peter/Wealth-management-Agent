from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.data_sources.base import REQUIRED_SOURCE_FIELDS, parse_date, staleness_days
from backend.app.utils.pandas_runtime import disable_optional_pandas_accelerators

disable_optional_pandas_accelerators()

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data"

SOURCE_FILE_CONFIG = [
    {
        "source_type": "synthetic_weekly_snapshot",
        "source_name": "Synthetic weekly product snapshot",
        "source_url_or_file": "data/weekly/product_weekly_snapshot.csv",
        "confidence_level": "medium",
        "parser_version": "weekly_snapshot_parser.v1",
    },
    {
        "source_type": "synthetic_weekly_snapshot",
        "source_name": "Synthetic peer product metrics",
        "source_url_or_file": "data/benchmark/peer_product_metrics.csv",
        "confidence_level": "medium",
        "parser_version": "peer_metrics_parser.v1",
    },
    {
        "source_type": "public_market_report",
        "source_name": "Public market report sample",
        "source_url_or_file": "data/public/market_reports/wealth_market_sample.json",
        "confidence_level": "medium",
        "parser_version": "market_report_adapter.v1",
    },
    {
        "source_type": "official_disclosure_sample",
        "source_name": "CITIC wealth disclosure sample",
        "source_url_or_file": "data/public/official_disclosure/citic_wealth_disclosures.json",
        "confidence_level": "medium",
        "parser_version": "citic_wealth_adapter.v1",
    },
    {
        "source_type": "official_public_nav",
        "source_name": "BOC public NAV adapter sample",
        "source_url_or_file": "https://www.bocwm.cn/",
        "confidence_level": "high",
        "parser_version": "boc_nav_adapter.v1",
    },
    {
        "source_type": "registry_lookup_sample",
        "source_name": "Financial product registry lookup sample",
        "source_url_or_file": "manual_check_required:financial_product_registry",
        "confidence_level": "medium",
        "parser_version": "registry_lookup_adapter.v1",
    },
    {
        "source_type": "public_reference_rate_api",
        "source_name": "US Treasury / reference rate adapter sample",
        "source_url_or_file": "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/daily_treasury_rates",
        "confidence_level": "high",
        "parser_version": "us_treasury_adapter.v1",
    },
    {
        "source_type": "manual_upload",
        "source_name": "Manual upload staging",
        "source_url_or_file": "data/uploads/upload_index.json",
        "confidence_level": "user_supplied",
        "parser_version": "manual_upload_parser.v1",
    },
]


def list_data_sources() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in SOURCE_FILE_CONFIG:
        path = ROOT / item["source_url_or_file"]
        rows.append(
            {
                **item,
                "adapter_status": "available" if path.exists() else "sample_missing",
                "record_count": _count_records(path),
            }
        )
    return rows


def _count_records(path: Path) -> int:
    if not path.exists():
        return 0
    if path.suffix.lower() == ".csv":
        try:
            return int(len(pd.read_csv(path)))
        except Exception:
            return 0
    if path.suffix.lower() == ".jsonl":
        return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    if path.suffix.lower() == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return 0
        if isinstance(payload, list):
            return len(payload)
        if isinstance(payload, dict):
            for key in ["records", "items", "reports"]:
                if isinstance(payload.get(key), list):
                    return len(payload[key])
            return 1
    return 0


def _csv_freshness(path: Path, config: dict[str, Any]) -> dict[str, Any]:
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        return {**config, "record_count": 0, "adapter_status": "failed", "error_type": exc.__class__.__name__, "missing_fields": []}

    latest_as_of = ""
    for column in ["as_of_date", "report_date", "nav_date"]:
        if column in frame and not frame.empty:
            parsed = pd.to_datetime(frame[column], errors="coerce").dropna()
            if not parsed.empty:
                latest_as_of = parsed.max().strftime("%Y-%m-%d")
                break
    missing = [field for field in REQUIRED_SOURCE_FIELDS if field not in frame.columns]
    return {
        "source_type": config["source_type"],
        "source_name": config["source_name"],
        "source_url_or_file": config["source_url_or_file"],
        "record_count": int(len(frame)),
        "latest_as_of_date": latest_as_of,
        "latest_fetched_at": str(frame["fetched_at"].max()) if "fetched_at" in frame and not frame.empty else "",
        "staleness_days": staleness_days(latest_as_of) if latest_as_of else 9999,
        "confidence_level": str(frame["confidence_level"].dropna().iloc[-1]) if "confidence_level" in frame and frame["confidence_level"].notna().any() else config["confidence_level"],
        "adapter_status": "available",
        "missing_fields": missing,
        "parser_version": str(frame["parser_version"].dropna().iloc[-1]) if "parser_version" in frame and frame["parser_version"].notna().any() else config["parser_version"],
    }


def _json_freshness(path: Path, config: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {**config, "record_count": 0, "adapter_status": "failed", "error_type": exc.__class__.__name__, "missing_fields": []}
    records = payload if isinstance(payload, list) else payload.get("records") or payload.get("items") or payload.get("reports") or [payload]
    latest = ""
    if records:
        candidates = [parse_date(row.get("as_of_date") or row.get("report_period") or row.get("published_at")) for row in records if isinstance(row, dict)]
        candidates = [item for item in candidates if item is not None]
        latest = max(candidates).isoformat() if candidates else ""
    fields = set().union(*(set(row) for row in records if isinstance(row, dict))) if records else set()
    missing = [field for field in REQUIRED_SOURCE_FIELDS if field not in fields]
    return {
        "source_type": config["source_type"],
        "source_name": config["source_name"],
        "source_url_or_file": config["source_url_or_file"],
        "record_count": len(records),
        "latest_as_of_date": latest,
        "latest_fetched_at": max((str(row.get("fetched_at", "")) for row in records if isinstance(row, dict)), default=""),
        "staleness_days": staleness_days(latest) if latest else 9999,
        "confidence_level": config["confidence_level"],
        "adapter_status": "available",
        "missing_fields": missing,
        "parser_version": config["parser_version"],
    }


def collect_freshness() -> list[dict[str, Any]]:
    freshness: list[dict[str, Any]] = []
    for config in SOURCE_FILE_CONFIG:
        path = ROOT / config["source_url_or_file"]
        if not path.exists():
            freshness.append(
                {
                    "source_type": config["source_type"],
                    "source_name": config["source_name"],
                    "source_url_or_file": config["source_url_or_file"],
                    "record_count": 0,
                    "latest_as_of_date": "",
                    "latest_fetched_at": "",
                    "staleness_days": 9999,
                    "confidence_level": config["confidence_level"],
                    "adapter_status": "sample_missing",
                    "missing_fields": REQUIRED_SOURCE_FIELDS,
                    "parser_version": config["parser_version"],
                }
            )
        elif path.suffix.lower() == ".csv":
            freshness.append(_csv_freshness(path, config))
        else:
            freshness.append(_json_freshness(path, config))
    return freshness


def _row_metadata(row: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    as_of = str(row.get("as_of_date") or row.get("report_date") or row.get("nav_date") or row.get("published_at") or "")
    return {
        "source_type": row.get("source_type") or config["source_type"],
        "source_name": row.get("source_name") or config["source_name"],
        "source_url_or_file": row.get("source_url_or_file") or config["source_url_or_file"],
        "fetched_at": row.get("fetched_at") or "",
        "as_of_date": as_of[:10],
        "staleness_days": int(row.get("staleness_days") or staleness_days(as_of)),
        "confidence_level": row.get("confidence_level") or config["confidence_level"],
        "evidence_id": row.get("evidence_id"),
        "parser_version": row.get("parser_version") or config["parser_version"],
    }


def lookup_lineage(evidence_id: str) -> dict[str, Any] | None:
    for config in SOURCE_FILE_CONFIG:
        path = ROOT / config["source_url_or_file"]
        if not path.exists() or path.suffix.lower() != ".csv":
            continue
        try:
            frame = pd.read_csv(path)
        except Exception:
            continue
        evidence_columns = [column for column in frame.columns if column == "evidence_id" or column.endswith("_evidence_id")]
        for column in evidence_columns:
            matches = frame[frame[column].astype(str) == str(evidence_id)]
            if not matches.empty:
                row = matches.iloc[0].to_dict()
                metadata = _row_metadata(row, config)
                metadata["matched_column"] = column
                metadata["payload_preview"] = {key: row.get(key) for key in list(row)[:18]}
                return metadata

    for config in SOURCE_FILE_CONFIG:
        path = ROOT / config["source_url_or_file"]
        if not path.exists() or path.suffix.lower() != ".json":
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        records = payload if isinstance(payload, list) else payload.get("records") or payload.get("items") or payload.get("reports") or [payload]
        for row in records:
            if isinstance(row, dict) and str(row.get("evidence_id")) == str(evidence_id):
                metadata = _row_metadata(row, config)
                metadata["payload_preview"] = {key: row.get(key) for key in list(row)[:18]}
                return metadata
    return None


def refresh_demo(as_of_date: str | None = None, base_date: str | None = None, seed: int = 20260709, n_products: int = 96) -> dict[str, Any]:
    from backend.app.data_sources.synthetic.next_week_generator import generate_next_week_snapshot

    return generate_next_week_snapshot(as_of_date=as_of_date, base_date=base_date, seed=seed, n_products=n_products)
