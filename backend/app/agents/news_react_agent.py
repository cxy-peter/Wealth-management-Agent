"""News ReAct tool agent with local fallback."""
from __future__ import annotations

from typing import Any

from backend.app.agents.react_common import build_optional_react_agent, call_registry_tool, final_event

ALLOWED_TOOLS = ["load_news", "classify_news_risk"]


def news_react_agent(state: dict[str, Any]) -> dict[str, Any]:
    build_optional_react_agent([])
    request = state["request"]
    news_call = call_registry_tool(state, "news_react_agent", "load_news", symbol=request["symbol"])
    risk_call = call_registry_tool(
        {**state, "tool_calls": news_call["tool_calls"], "agent_events": news_call["agent_events"]},
        "news_react_agent",
        "classify_news_risk",
        symbol=request["symbol"],
        news_records=news_call["record"].get("output", {}).get("records", []),
    )
    record = risk_call["record"]
    output = record.get("output", {})
    signals = output.get("signals", [])
    for signal in signals:
        signal["source_tool_call_id"] = record["tool_call_id"]
        signal["evidence_ids"] = record.get("evidence_ids", [])
    summary = output.get("summary", {})
    summary["source_tool_call_id"] = record["tool_call_id"]
    summary["evidence_ids"] = record.get("evidence_ids", [])
    events = [*risk_call["agent_events"], final_event("news_react_agent", summary)]
    return {
        **state,
        "news_records": news_call["record"].get("output", {}),
        "news_signals": signals,
        "news_summary": summary,
        "model_metadata": output.get("model_metadata", {}),
        "tool_calls": risk_call["tool_calls"],
        "agent_events": events,
    }
