"""Technical-analysis node for price/NAV sample data."""
from __future__ import annotations

from typing import Any

from backend.app.tools.metrics import compute_metrics, technical_snapshot


def technical_agent(state: dict[str, Any]) -> dict[str, Any]:
    request = state["request"]
    nav_df = state["nav_df"]
    symbol = request["symbol"]

    metrics = compute_metrics(nav_df, symbol, value_col="close").to_dict()
    snapshot = technical_snapshot(nav_df, symbol, value_col="close")
    snapshot["points"] = [
        f"最新样例收盘值 {snapshot['latest_close']:.3f}，MA5 为 {snapshot['ma5']:.3f}，MA20 为 {snapshot['ma20']:.3f}。",
        f"5 日动量 {snapshot['momentum_5d']:.2%}，20 日动量 {snapshot['momentum_20d']:.2%}。",
        f"样本内波动状态：{snapshot['risk_regime']}。",
    ]

    tool_calls = list(state.get("tool_calls", []))
    tool_calls.append(
        {
            "tool": "compute_metrics",
            "agent": "technical_agent",
            "success": True,
            "rows": int(len(nav_df)),
        }
    )

    return {
        **state,
        "metrics": metrics,
        "technical_analysis": snapshot,
        "tool_calls": tool_calls,
    }
