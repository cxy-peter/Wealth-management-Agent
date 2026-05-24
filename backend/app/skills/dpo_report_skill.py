from __future__ import annotations

from backend.app.models.dpo_report_adapter import DPOReportAdapter
from backend.app.skills.skill_registry import SKILLS

SKILL_SPEC = SKILLS["dpo_report_skill"]


def run(tool_outputs: dict, task_type: str = "weekly_product_summary") -> dict:
    return DPOReportAdapter().generate_report(tool_outputs, task_type=task_type)
