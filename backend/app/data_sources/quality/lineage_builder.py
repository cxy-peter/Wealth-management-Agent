from __future__ import annotations

from typing import Any

from backend.app.data_sources.source_registry import lookup_lineage


def lineage_for_evidence(evidence_id: str) -> dict[str, Any]:
    lineage = lookup_lineage(evidence_id)
    if lineage is None:
        return {"evidence_id": evidence_id, "found": False, "message": "evidence_id not found in local sample stores"}
    return {"evidence_id": evidence_id, "found": True, **lineage}

