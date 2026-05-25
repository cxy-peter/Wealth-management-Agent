from __future__ import annotations

from backend.app.skills.skill_registry import SKILLS

SKILL_SPEC = SKILLS["data_upload_skill"]


def run(dataset_scope: str, target_schema: str, row_count: int = 0, upload_id: str | None = None) -> dict:
    evidence_id = f"ev_upload_skill_{upload_id or dataset_scope}_{target_schema}"
    return {
        "upload_id": upload_id or "browser_or_api_upload",
        "dataset_scope": dataset_scope,
        "target_schema": target_schema,
        "row_count": row_count,
        "quality_report": {
            "dataset_scope_required": bool(dataset_scope),
            "target_schema": target_schema,
            "status": "pass" if dataset_scope and target_schema else "needs_mapping",
        },
        "evidence_ids": [evidence_id],
    }
