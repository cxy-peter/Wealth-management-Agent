from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.app.dpo.dpo_dataset_builder import REPORT_OUTPUT, build_all_dpo_datasets


def build_report_preferences(output_path: str | Path = REPORT_OUTPUT, limit: int = 36) -> dict[str, Any]:
    result = build_all_dpo_datasets(report_limit=limit)
    return {
        "output_path": str(output_path),
        "pair_count": result.get("report_pairs", 0),
        "status": "generated",
        "preference_focus": [
            "numeric consistency",
            "evidence coverage",
            "risk warning",
            "source boundary",
            "weekly report style",
        ],
    }


if __name__ == "__main__":
    print(build_report_preferences())
