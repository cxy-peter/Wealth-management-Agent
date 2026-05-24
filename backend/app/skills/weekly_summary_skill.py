from __future__ import annotations

from backend.app.skills.skill_registry import SKILLS
from backend.app.weekly_report.generators.weekly_report_generator import weekly_summary

SKILL_SPEC = SKILLS["weekly_summary_skill"]


def run(report_date: str | None = None, filters: dict | None = None) -> dict:
    return weekly_summary(report_date, filters)
