"""Fundamental-analysis node adapted for a research-assistant workflow."""
from __future__ import annotations

from typing import Any

from backend.app.agents.valuation_agent import evaluate_valuation


def _latest_row(df: Any) -> Any | None:
    if df.empty:
        return None
    return df.iloc[-1]


def _quality_label(roe: float, net_margin: float, debt_to_asset: float) -> str:
    if roe >= 0.18 and net_margin >= 0.25 and debt_to_asset <= 0.35:
        return "盈利质量样例较强"
    if roe <= 0.06 or debt_to_asset >= 0.7:
        return "基本面质量需重点复核"
    return "基本面质量中性观察"


def fundamental_agent(state: dict[str, Any]) -> dict[str, Any]:
    df = state["fundamentals_df"]
    row = _latest_row(df)

    if row is None:
        analysis = {
            "available": False,
            "quality_label": "缺少样例基本面字段",
            "points": ["当前样例数据未覆盖财务字段，需要补充公开财报或模拟财务表。"],
        }
    else:
        revenue_growth = float(row.get("revenue_growth", 0.0))
        net_margin = float(row.get("net_margin", 0.0))
        roe = float(row.get("roe", 0.0))
        debt_to_asset = float(row.get("debt_to_asset", 0.0))
        operating_cashflow_ratio = float(row.get("operating_cashflow_ratio", 0.0))
        analysis = {
            "available": True,
            "as_of": str(row.get("as_of", ""))[:10],
            "source": str(row.get("source", "demo_mock")),
            "revenue_growth": revenue_growth,
            "net_margin": net_margin,
            "roe": roe,
            "debt_to_asset": debt_to_asset,
            "operating_cashflow_ratio": operating_cashflow_ratio,
            "quality_label": _quality_label(roe, net_margin, debt_to_asset),
            "points": [
                f"营收增速样例值为 {revenue_growth:.1%}，用于观察增长节奏。",
                f"ROE 样例值为 {roe:.1%}，净利率样例值为 {net_margin:.1%}。",
                f"资产负债率样例值为 {debt_to_asset:.1%}，需结合行业口径复核。",
            ],
        }

    tool_calls = list(state.get("tool_calls", []))
    tool_calls.append(
        {
            "tool": "fundamental_metric_parser",
            "agent": "fundamental_agent",
            "success": True,
            "rows": int(len(df)),
        }
    )

    return {
        **state,
        "fundamental_analysis": analysis,
        "valuation_analysis": evaluate_valuation(df),
        "tool_calls": tool_calls,
    }
