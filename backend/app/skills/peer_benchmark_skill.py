from __future__ import annotations

from backend.app.skills.skill_registry import SKILLS
from backend.app.weekly_report.generators.benchmark_report_generator import peer_benchmark

SKILL_SPEC = SKILLS["peer_benchmark_skill"]


def run(product_code: str, report_date: str | None = None) -> dict:
    return peer_benchmark(product_code, report_date)
