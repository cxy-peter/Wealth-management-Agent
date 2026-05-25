"""Planner node for dynamic routing."""
from __future__ import annotations

from typing import Any


ACTION_TO_TOOLS = {
    "fast_snapshot": ["load_price_series", "calculate_metrics", "load_news", "classify_news_risk"],
    "standard_research": [
        "load_price_series",
        "calculate_metrics",
        "load_fundamental_snapshot",
        "load_valuation_snapshot",
        "load_news",
        "classify_news_risk",
        "product_benchmark",
    ],
    "deep_review": [
        "load_price_series",
        "calculate_metrics",
        "load_fundamental_snapshot",
        "load_valuation_snapshot",
        "load_news",
        "classify_news_risk",
        "product_benchmark",
    ],
    "product_compare": ["product_benchmark"],
    "risk_only": ["load_price_series", "calculate_metrics", "load_news", "classify_news_risk"],
}


def infer_task_type(analysis_type: str, risk_preference: str) -> str:
    analysis_type = (analysis_type or "full").lower()
    risk_preference = (risk_preference or "balanced").lower()
    if analysis_type in {"risk", "risk_only"}:
        return "risk_only"
    if analysis_type in {"weekly_product", "product", "product_compare", "benchmark"}:
        return "product_compare"
    if analysis_type in {"fast", "snapshot"}:
        return "fast_snapshot"
    if analysis_type in {"deep", "deep_review"} or risk_preference in {"conservative", "strict"}:
        return "deep_review"
    return "standard_research"


def planner_agent(state: dict[str, Any]) -> dict[str, Any]:
    request = state["request"]
    task_type = infer_task_type(request.get("analysis_type", "full"), request.get("risk_preference", "balanced"))
    required_tools = ACTION_TO_TOOLS[task_type]
    all_tools = sorted({tool for tools in ACTION_TO_TOOLS.values() for tool in tools})
    risk_level = "high" if task_type in {"deep_review", "risk_only"} else "medium"
    plan = {
        "task_type": task_type,
        "analysis_depth": "deep" if task_type == "deep_review" else "standard" if task_type == "standard_research" else "focused",
        "required_tools": required_tools,
        "skipped_tools": [tool for tool in all_tools if tool not in required_tools],
        "risk_level": risk_level,
        "human_review_required": task_type == "deep_review",
    }
    event = {
        "event_type": "planner_output",
        "agent_name": "planner_agent",
        "payload": plan,
    }
    return {
        **state,
        "planner_plan": plan,
        "agent_events": [*state.get("agent_events", []), event],
        "run_trace": {
            **state.get("run_trace", {}),
            "planner": plan,
        },
    }
