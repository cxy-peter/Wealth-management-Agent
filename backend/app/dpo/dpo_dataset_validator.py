from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATASET = ROOT / "data" / "dpo" / "weekly_report_preference_pairs.jsonl"

FORBIDDEN_PATTERNS = [
    r"建议\s*(买入|卖出|持有)",
    r"推荐\s*配置",
    r"保证收益",
    r"确定性?\s*(上涨|增长|延续)",
    r"收益稳定可期",
    r"稳赚",
]


def _load_jsonl(path: str | Path = DEFAULT_DATASET) -> list[dict[str, Any]]:
    target = Path(path)
    if not target.exists():
        return []
    rows: list[dict[str, Any]] = []
    with target.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                rows.append({"_invalid_json": True, "line_no": line_no, "error": str(exc)})
    return rows


def _forbidden_hits(text: str) -> list[str]:
    return [pattern for pattern in FORBIDDEN_PATTERNS if re.search(pattern, text)]


def validate_dpo_dataset(path: str | Path = DEFAULT_DATASET) -> dict[str, Any]:
    rows = _load_jsonl(path)
    failures: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        row_id = row.get("id", f"row_{index}")
        if row.get("_invalid_json"):
            failures.append({"id": row_id, "check": "json_parse", "error": row.get("error")})
            continue
        for key in ["prompt", "chosen", "rejected", "reject_reason"]:
            if not row.get(key):
                failures.append({"id": row_id, "check": f"missing_{key}"})
        chosen = str(row.get("chosen", ""))
        rejected = str(row.get("rejected", ""))
        if "evidence_id=" not in chosen:
            failures.append({"id": row_id, "check": "chosen_missing_evidence_id"})
        if _forbidden_hits(chosen):
            failures.append({"id": row_id, "check": "chosen_forbidden_wording", "patterns": _forbidden_hits(chosen)})
        if len(chosen) < 80:
            failures.append({"id": row_id, "check": "chosen_too_short"})
        if chosen.strip() == rejected.strip():
            failures.append({"id": row_id, "check": "chosen_equals_rejected"})
        tool_output = row.get("prompt", {}).get("tool_output", {})
        evidence_id = str(tool_output.get("evidence_id", ""))
        if evidence_id and evidence_id not in chosen:
            failures.append({"id": row_id, "check": "chosen_not_grounded_to_tool_evidence"})
    return {
        "dataset_path": str(Path(path)),
        "pair_count": len(rows),
        "valid": len(failures) == 0 and len(rows) > 0,
        "failure_count": len(failures),
        "failures": failures[:50],
    }


if __name__ == "__main__":
    print(json.dumps(validate_dpo_dataset(), ensure_ascii=False, indent=2))
