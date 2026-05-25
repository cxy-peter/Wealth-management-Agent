from __future__ import annotations

import time
import uuid
from typing import Any


def new_skill_call_id(skill_name: str) -> str:
    return f"sc_{skill_name}_{uuid.uuid4().hex[:10]}"


def make_skill_call(
    *,
    skill_name: str,
    input_payload: dict[str, Any],
    output: dict[str, Any] | None,
    timeout_seconds: int,
    max_calls: int,
    risk_level: str,
    started_at: float,
    success: bool,
    error_type: str | None = None,
    harness_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    evidence_ids = []
    if isinstance(output, dict):
        if isinstance(output.get("evidence_ids"), list):
            evidence_ids.extend(output["evidence_ids"])
        if output.get("evidence_id"):
            evidence_ids.append(output["evidence_id"])
    return {
        "skill_call_id": new_skill_call_id(skill_name),
        "skill_name": skill_name,
        "input": input_payload,
        "output": output or {},
        "timeout_seconds": timeout_seconds,
        "max_calls": max_calls,
        "risk_level": risk_level,
        "latency_ms": round((time.perf_counter() - started_at) * 1000, 3),
        "success": success,
        "error_type": error_type,
        "evidence_ids": list(dict.fromkeys(str(item) for item in evidence_ids if item)),
        "harness_result": harness_result or {"pass": success, "failed_rules": []},
    }

