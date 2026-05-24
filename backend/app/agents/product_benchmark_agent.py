"""Product benchmark node for wealth-management product comparison."""
from __future__ import annotations

from typing import Any

from backend.app.agents.react_common import call_registry_tool, final_event


def product_benchmark_agent(state: dict[str, Any]) -> dict[str, Any]:
    request = state["request"]
    filters = request.get("product_filters") or {}
    call = call_registry_tool(
        state,
        "product_benchmark_agent",
        "product_benchmark",
        asset_class=filters.get("asset_class"),
        risk_level=filters.get("risk_level"),
        channel=filters.get("channel"),
        duration_bucket=filters.get("duration_bucket"),
        liquidity_type=filters.get("liquidity_type"),
        strategy_type=filters.get("strategy_type"),
    )
    record = call["record"]
    peer = record.get("output", {})
    peer["source_tool_call_id"] = record["tool_call_id"]
    peer["evidence_ids"] = record.get("evidence_ids", [])

    return {
        **state,
        "peer_summary": peer,
        "tool_calls": call["tool_calls"],
        "agent_events": [*call["agent_events"], final_event("product_benchmark_agent", peer)],
    }
