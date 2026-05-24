"""Fundamental ReAct tool agent with local fallback."""
from __future__ import annotations

from typing import Any

from backend.app.agents.react_common import build_optional_react_agent, call_registry_tool, final_event

ALLOWED_TOOLS = ["load_fundamental_snapshot"]


def fundamental_react_agent(state: dict[str, Any]) -> dict[str, Any]:
    build_optional_react_agent([])
    request = state["request"]
    call = call_registry_tool(state, "fundamental_react_agent", "load_fundamental_snapshot", symbol=request["symbol"])
    record = call["record"]
    snapshot = record.get("output", {}).get("snapshot", {})
    if snapshot:
        roe = float(snapshot.get("roe", 0.0))
        net_margin = float(snapshot.get("net_margin", 0.0))
        debt_to_asset = float(snapshot.get("debt_to_asset", 0.0))
        quality_label = (
            "盈利质量样例较强"
            if roe >= 0.18 and net_margin >= 0.25 and debt_to_asset <= 0.35
            else "基本面质量中性观察"
        )
        points = [
            f"营收增速样例值为 {float(snapshot.get('revenue_growth', 0.0)):.1%}。[tool_call_id={record['tool_call_id']}]",
            f"ROE 样例值为 {roe:.1%}，净利率样例值为 {net_margin:.1%}。[tool_call_id={record['tool_call_id']}]",
            f"资产负债率样例值为 {debt_to_asset:.1%}。[evidence_id={record['evidence_ids'][0]}]",
        ]
    else:
        quality_label = "缺少样例基本面字段"
        points = [f"样例数据未覆盖财务字段。[tool_call_id={record['tool_call_id']}]"]

    analysis = {
        "available": bool(snapshot),
        "quality_label": quality_label,
        "points": points,
        "source_tool_call_id": record["tool_call_id"],
        "evidence_ids": record.get("evidence_ids", []),
    }
    events = [*call["agent_events"], final_event("fundamental_react_agent", analysis)]
    return {
        **state,
        "fundamental_analysis": analysis,
        "tool_calls": call["tool_calls"],
        "agent_events": events,
    }
