"""Technical ReAct tool agent with local fallback."""
from __future__ import annotations

from typing import Any

from backend.app.agents.react_common import build_optional_react_agent, call_registry_tool, final_event

ALLOWED_TOOLS = ["load_price_series", "calculate_metrics"]


def technical_react_agent(state: dict[str, Any]) -> dict[str, Any]:
    build_optional_react_agent([])
    request = state["request"]
    price_call = call_registry_tool(state, "technical_react_agent", "load_price_series", symbol=request["symbol"])
    metric_call = call_registry_tool(
        {**state, "tool_calls": price_call["tool_calls"], "agent_events": price_call["agent_events"]},
        "technical_react_agent",
        "calculate_metrics",
        symbol=request["symbol"],
        price_records=price_call["record"].get("output", {}).get("records", []),
    )
    record = metric_call["record"]
    output = record.get("output", {})
    metrics = output.get("metrics", {})
    metrics["source_tool_call_id"] = record["tool_call_id"]
    metrics["evidence_ids"] = record.get("evidence_ids", [])
    technical = output.get("technical", {})
    technical["points"] = [
        f"最新样例收盘值 {technical.get('latest_close', 0):.3f}，MA5 为 {technical.get('ma5', 0):.3f}，MA20 为 {technical.get('ma20', 0):.3f}。[tool_call_id={record['tool_call_id']}]",
        f"5 日动量 {technical.get('momentum_5d', 0):.2%}，20 日动量 {technical.get('momentum_20d', 0):.2%}。[evidence_id={record['evidence_ids'][0]}]",
    ]
    technical["source_tool_call_id"] = record["tool_call_id"]
    technical["evidence_ids"] = record.get("evidence_ids", [])
    events = [*metric_call["agent_events"], final_event("technical_react_agent", technical)]
    return {
        **state,
        "price_series": price_call["record"].get("output", {}),
        "metrics": metrics,
        "technical_analysis": technical,
        "tool_calls": metric_call["tool_calls"],
        "agent_events": events,
    }
