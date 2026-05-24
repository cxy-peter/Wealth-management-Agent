from __future__ import annotations

from backend.app.nav_compare.five_product_compare import five_product_compare
from backend.app.skills.skill_registry import SKILLS

SKILL_SPEC = SKILLS["nav_compare_skill"]


def run(product_codes: list[str], range_weeks: int = 13) -> dict:
    return five_product_compare(product_codes, range_weeks=range_weeks)
