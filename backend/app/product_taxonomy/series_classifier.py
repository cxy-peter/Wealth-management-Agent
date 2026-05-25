from __future__ import annotations

from typing import Any

from backend.app.product_taxonomy.manual_override_store import apply_overrides
from backend.app.product_taxonomy.taxonomy_rules import classify_by_rules
from backend.app.weekly_report.parsers.weekly_snapshot_parser import frame_records, load_weekly_snapshot


def classify_products(products: list[dict[str, Any]] | None = None, report_date: str | None = None, apply_manual: bool = True) -> dict[str, Any]:
    rows = products if products is not None else frame_records(load_weekly_snapshot(report_date))
    classified = [{**row, **classify_by_rules(row)} for row in rows]
    if apply_manual:
        classified = apply_overrides(classified)
    low_confidence = [row for row in classified if float(row.get("confidence") or 0) < 0.75 or row.get("suggested_series_id") == "unclassified"]
    return {
        "report_date": report_date,
        "count": len(classified),
        "classified_products": classified,
        "low_confidence_products": low_confidence,
        "evidence_ids": [row.get("evidence_id") for row in classified if row.get("evidence_id")][:20]
    }

