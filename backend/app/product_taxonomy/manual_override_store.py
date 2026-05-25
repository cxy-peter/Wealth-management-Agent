from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
OVERRIDE_PATH = ROOT / "data" / "uploads" / "product_series_manual_override.json"


def _read() -> list[dict[str, Any]]:
    if not OVERRIDE_PATH.exists():
        return []
    try:
        payload = json.loads(OVERRIDE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return list(payload.get("overrides", []))


def _write(rows: list[dict[str, Any]]) -> None:
    OVERRIDE_PATH.parent.mkdir(parents=True, exist_ok=True)
    OVERRIDE_PATH.write_text(json.dumps({"overrides": rows}, ensure_ascii=False, indent=2), encoding="utf-8")


def list_overrides() -> list[dict[str, Any]]:
    return _read()


def create_override(
    *,
    product_code: str,
    product_name: str = "",
    old_series_id: str = "",
    new_series_id: str = "",
    action_type: str = "move",
    reason: str = "manual correction",
) -> dict[str, Any]:
    rows = _read()
    override = {
        "override_id": f"override_{uuid.uuid4().hex[:12]}",
        "product_code": product_code,
        "product_name": product_name,
        "old_series_id": old_series_id,
        "new_series_id": new_series_id,
        "action_type": action_type,
        "reason": reason,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evidence_id": f"ev_series_override_{product_code}_{uuid.uuid4().hex[:8]}"
    }
    rows.insert(0, override)
    _write(rows[:500])
    return override


def apply_overrides(classified_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest_by_code: dict[str, dict[str, Any]] = {}
    for row in reversed(_read()):
        latest_by_code[row["product_code"]] = row

    output = []
    for row in classified_rows:
        next_row = dict(row)
        override = latest_by_code.get(str(row.get("product_code")))
        if override and override.get("action_type") != "remove":
            next_row["suggested_series_id"] = override.get("new_series_id") or next_row.get("suggested_series_id")
            next_row["suggested_series_name"] = override.get("new_series_name") or override.get("new_series_id") or next_row.get("suggested_series_name")
            next_row["confidence"] = 1.0
            next_row["classify_reason"] = f"manual_override:{override.get('reason', '')}"
            next_row["manual_override_id"] = override.get("override_id")
            next_row["evidence_id"] = override.get("evidence_id")
        elif override and override.get("action_type") == "remove":
            next_row["suggested_series_id"] = "unclassified"
            next_row["suggested_series_name"] = "未归类"
            next_row["confidence"] = 1.0
            next_row["classify_reason"] = f"manual_remove:{override.get('reason', '')}"
            next_row["manual_override_id"] = override.get("override_id")
            next_row["evidence_id"] = override.get("evidence_id")
        output.append(next_row)
    return output

