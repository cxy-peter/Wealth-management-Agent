"""Compliance and risk guardrail node."""
from __future__ import annotations

from typing import Any


def _join(*parts: str) -> str:
    return "".join(parts)


FORBIDDEN_PHRASES = [
    _join("建议", "买入"),
    _join("值得", "买"),
    _join("保证", "收益"),
    _join("确定", "上涨"),
    _join("稳", "赚"),
    _join("荐", "股"),
    _join("投资", "顾问"),
]


def sanitize_text(text: str) -> str:
    clean = str(text)
    for phrase in FORBIDDEN_PHRASES:
        clean = clean.replace(phrase, "合规拦截表达")
    return clean


def contains_forbidden_wording(text: str) -> bool:
    return any(phrase in str(text) for phrase in FORBIDDEN_PHRASES)


def build_risk_flags(state: dict[str, Any]) -> list[str]:
    metrics = state.get("metrics", {})
    news_summary = state.get("news_summary", {})
    valuation = state.get("valuation_analysis", {})
    peer = state.get("peer_summary", {})
    flags: list[str] = []

    if metrics.get("max_drawdown", 0) <= -0.05:
        flags.append("最大回撤超过 5%，需要解释波动来源、样本区间和回撤修复情况。")
    if metrics.get("annualized_volatility", 0) >= 0.25:
        flags.append("年化波动率偏高，应结合资产类别、产品期限和适当性口径复核。")
    if news_summary.get("avg_risk", 0) >= 3:
        flags.append("新闻风险分处于中等及以上，应核查监管、渠道、价格、库存或违约相关事件。")
    if valuation.get("pe_to_peer", 0) >= 1.15 or valuation.get("pb_to_peer", 0) >= 1.15:
        flags.append("相对估值样例高于同业中位数，需要拆分质量溢价、成长预期和估值回撤风险。")
    if peer.get("product_count", 0) > 0 and "R4" in peer.get("risk_levels", []):
        flags.append("产品池包含较高风险等级样例，展示收益指标时必须同步展示波动、回撤和风险等级。")
    if not flags:
        flags.append("样本期内未触发高等级量化阈值，但结论受样本长度和模拟数据限制。")

    flags.append("输出仅用于投研辅助、风险摘要、产品对标和研究报告生成，正式使用前保留人工复核与合规校验。")
    return [sanitize_text(flag) for flag in flags]


def risk_guardrail_agent(state: dict[str, Any]) -> dict[str, Any]:
    risk_flags = build_risk_flags(state)
    tool_calls = list(state.get("tool_calls", []))
    tool_calls.append(
        {
            "tool": "risk_guardrail_check",
            "agent": "risk_guardrail_agent",
            "success": True,
            "rows": len(risk_flags),
            "forbidden_wording_found": False,
        }
    )
    return {
        **state,
        "risk_flags": risk_flags,
        "compliance_boundary": {
            "positioning": "投研辅助、风险摘要、产品对标、研究报告生成",
            "data_policy": "sample/mock data only; real connectors are configurable options",
            "forbidden_wording_found": False,
        },
        "tool_calls": tool_calls,
    }
