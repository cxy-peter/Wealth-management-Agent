"""Human-review state node.

The default demo records a pending-review state instead of pausing execution.
LangGraph interrupt is imported when available so the project can switch to a
blocking approval flow without changing API contracts.
"""
from __future__ import annotations

from typing import Any

try:
    from langgraph.types import interrupt

    INTERRUPT_AVAILABLE = True
except Exception:  # pragma: no cover
    interrupt = None
    INTERRUPT_AVAILABLE = False


def should_trigger_review(state: dict[str, Any]) -> bool:
    verification = state.get("verification_result", {})
    news_risk = float(state.get("news_summary", {}).get("avg_risk", 0.0) or 0.0)
    guardrail = state.get("compliance_boundary", {})
    return any(
        [
            news_risk >= 4,
            not verification.get("pass", True),
            verification.get("forbidden_wording", False),
            bool(verification.get("missing_evidence")),
            bool(guardrail.get("forbidden_wording_found")),
            bool(state.get("planner_plan", {}).get("human_review_required")),
        ]
    )


def human_review_agent(state: dict[str, Any]) -> dict[str, Any]:
    pending = should_trigger_review(state)
    review = {
        "status": "pending_review" if pending else "auto_cleared",
        "reason": {
            "verification_pass": state.get("verification_result", {}).get("pass", True),
            "avg_news_risk": state.get("news_summary", {}).get("avg_risk", 0.0),
            "planner_requested": state.get("planner_plan", {}).get("human_review_required", False),
        },
        "interrupt_available": INTERRUPT_AVAILABLE,
    }
    result = state.get("result", {})
    result["human_review"] = review
    event = {
        "event_type": "human_review_status",
        "agent_name": "human_review_agent",
        "payload": review,
    }
    return {
        **state,
        "result": result,
        "human_review": review,
        "agent_events": [*state.get("agent_events", []), event],
    }
