from __future__ import annotations

from backend.app.skills.skill_registry import SKILLS
from backend.app.weekly_report.generators.benchmark_report_generator import channel_benchmark

SKILL_SPEC = SKILLS["channel_benchmark_skill"]


def run(product_type: str | None = None, channel: str | None = None) -> dict:
    return channel_benchmark(product_type=product_type, channel=channel)
