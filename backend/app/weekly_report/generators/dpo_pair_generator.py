from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DPO_PATH = ROOT / "data" / "dpo" / "weekly_report_preference_pairs.jsonl"


def load_dpo_pairs(path: str | Path = DEFAULT_DPO_PATH) -> list[dict[str, Any]]:
    target = Path(path)
    if not target.exists():
        return []
    rows: list[dict[str, Any]] = []
    with target.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def dpo_trace_sample(limit: int = 3) -> dict[str, Any]:
    pairs = load_dpo_pairs()
    return {
        "pair_count": len(pairs),
        "samples": pairs[:limit],
        "source_file": "data/dpo/weekly_report_preference_pairs.jsonl",
        "training_default": "disabled; validation only unless ENABLE_DPO_TRAINING=true",
    }
