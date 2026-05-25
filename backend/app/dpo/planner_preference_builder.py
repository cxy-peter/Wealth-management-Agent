from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.app.dpo.dpo_dataset_builder import PLANNER_OUTPUT, build_all_dpo_datasets


def build_planner_preferences(output_path: str | Path = PLANNER_OUTPUT, limit: int = 24) -> dict[str, Any]:
    result = build_all_dpo_datasets(planner_limit=limit)
    return {
        "output_path": str(output_path),
        "pair_count": result.get("planner_pairs", 0),
        "status": "generated",
        "preference_focus": ["skill selection", "dataset_scope", "verifier_required", "guardrail_required"],
    }


if __name__ == "__main__":
    print(build_planner_preferences())

