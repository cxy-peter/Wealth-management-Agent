from __future__ import annotations

from typing import Any

from backend.app.nav_compare.nav_compare_engine import compare_nav_series
from backend.app.weekly_report.parsers.weekly_snapshot_parser import load_nav_weekly


def five_product_compare(product_codes: list[str], range_weeks: int = 13) -> dict[str, Any]:
    selected = [str(code) for code in product_codes[:5] if code]
    series = {}
    for code in selected:
        nav = load_nav_weekly(code).tail(range_weeks)
        if not nav.empty:
            series[code] = nav[["nav_date", "nav", "benchmark_nav"]].rename(columns={"nav_date": "date"})
    return {
        "product_codes": selected,
        "range_weeks": range_weeks,
        "comparison": compare_nav_series(series),
        "source_type": "synthetic_weekly_snapshot",
        "evidence_ids": [f"ev_nav_compare_{code}" for code in selected],
    }
