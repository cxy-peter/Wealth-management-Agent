from __future__ import annotations

from typing import Any

from backend.app.data_sources.source_registry import collect_freshness


def freshness_report() -> dict[str, Any]:
    rows = collect_freshness()
    stale = [row for row in rows if row.get("staleness_days", 9999) > 30]
    missing = [row for row in rows if row.get("missing_fields")]
    return {
        "sources": rows,
        "stale_source_count": len(stale),
        "sources_with_missing_metadata": len(missing),
        "data_mode": "sample/mock with explicit source metadata",
    }

