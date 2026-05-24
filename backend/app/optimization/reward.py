"""Reward function for eval-driven route optimization."""
from __future__ import annotations

from typing import Any


def latency_penalty(latency_ms: float, budget_ms: float = 800.0) -> float:
    return min(1.0, max(0.0, latency_ms / budget_ms))


def compute_reward(metrics: dict[str, Any]) -> float:
    score = (
        0.20 * float(metrics.get("tool_call_success", 0.0))
        + 0.20 * float(metrics.get("metric_consistency", 0.0))
        + 0.15 * float(metrics.get("risk_warning_coverage", 0.0))
        + 0.15 * float(metrics.get("evidence_coverage", 0.0))
        + 0.10 * float(metrics.get("report_format_pass", 0.0))
        + 0.10 * float(metrics.get("route_match_score", 0.0))
        - 0.10 * latency_penalty(float(metrics.get("latency_ms", 0.0)))
        - 0.15 * float(metrics.get("unnecessary_tool_penalty", 0.0))
        - 1.00 * float(metrics.get("forbidden_wording_hit", 0.0))
    )
    return round(score, 4)
