from __future__ import annotations

from typing import Any

from backend.app.data_sources.base import REQUIRED_SOURCE_FIELDS


def check_required_metadata(records: list[dict[str, Any]]) -> dict[str, Any]:
    failures = []
    for index, row in enumerate(records, 1):
        missing = [field for field in REQUIRED_SOURCE_FIELDS if not row.get(field)]
        if missing:
            failures.append({"row_index": index, "missing_fields": missing, "evidence_id": row.get("evidence_id")})
    return {"valid": not failures, "failure_count": len(failures), "failures": failures[:50]}

