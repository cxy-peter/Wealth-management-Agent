"""Valuation ReAct tool agent with local fallback."""
from __future__ import annotations

from typing import Any

from backend.app.agents.react_common import build_optional_react_agent, call_registry_tool, final_event

ALLOWED_TOOLS = ["load_valuation_snapshot"]


def valuation_react_agent(state: dict[str, Any]) -> dict[str, Any]:
    build_optional_react_agent([])
    request = state["request"]
    call = call_registry_tool(state, "valuation_react_agent", "load_valuation_snapshot", symbol=request["symbol"])
    record = call["record"]
    valuation = record.get("output", {}).get("valuation", {})
    valuation["source_tool_call_id"] = record["tool_call_id"]
    valuation["evidence_ids"] = record.get("evidence_ids", [])
    valuation["points"] = [
        f"{point} [tool_call_id={record['tool_call_id']}]" for point in valuation.get("points", [])
    ]
    events = [*call["agent_events"], final_event("valuation_react_agent", valuation)]
    return {
        **state,
        "valuation_analysis": valuation,
        "tool_calls": call["tool_calls"],
        "agent_events": events,
    }
