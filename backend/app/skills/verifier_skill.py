from __future__ import annotations

from backend.app.skills.skill_registry import SKILLS
from backend.app.weekly_report.weekly_report_verifier import verify_weekly_report

SKILL_SPEC = SKILLS["verifier_skill"]


def run(report: dict) -> dict:
    return verify_weekly_report(report)
