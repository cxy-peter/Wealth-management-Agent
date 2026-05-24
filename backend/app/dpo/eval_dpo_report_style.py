from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from backend.app.dpo.dpo_dataset_validator import DEFAULT_DATASET, validate_dpo_dataset  # noqa: E402

RESULT_PATH = ROOT / "eval" / "dpo_style_eval_results.json"


def run_eval() -> dict:
    validation = validate_dpo_dataset(DEFAULT_DATASET)
    pair_count = validation["pair_count"]
    pass_rate = 0.0 if pair_count == 0 else round((pair_count - validation["failure_count"]) / pair_count, 4)
    payload = {
        "task": "weekly_report_style_alignment",
        "dataset": "data/dpo/weekly_report_preference_pairs.jsonl",
        "pair_count": pair_count,
        "validation_pass": validation["valid"],
        "pair_level_pass_rate": pass_rate,
        "failure_count": validation["failure_count"],
        "failures": validation["failures"],
        "training_default": "validation_only",
    }
    RESULT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    print(json.dumps(run_eval(), ensure_ascii=False, indent=2))
