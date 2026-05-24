"""Verifier node for metrics, evidence, guardrail and report structure."""
from __future__ import annotations

from typing import Any

from backend.app.agents.risk_guardrail_agent import contains_forbidden_wording
from backend.app.tools.metrics import format_float, format_pct

REQUIRED_SECTIONS = [
    "合规说明",
    "数据与工具调用摘要",
    "核心量化指标",
    "基本面与估值摘要",
    "技术面风险观察",
    "同业产品对标样例",
    "新闻情绪与风险信号",
    "风险提示与可追溯结论",
]


def verify_result(result: dict[str, Any]) -> dict[str, Any]:
    report = result.get("report_markdown", "")
    metrics = result.get("metrics", {})
    failed_checks: list[str] = []
    metric_mismatches: list[str] = []
    missing_evidence: list[str] = []

    for section in REQUIRED_SECTIONS:
        if section not in report:
            failed_checks.append(f"missing_section:{section}")

    metric_expectations = {
        "total_return": format_pct(metrics.get("total_return", 0.0)),
        "annualized_volatility": format_pct(metrics.get("annualized_volatility", 0.0)),
        "max_drawdown": format_pct(metrics.get("max_drawdown", 0.0)),
        "sharpe_ratio": format_float(metrics.get("sharpe_ratio", 0.0)),
    }
    for key, expected in metric_expectations.items():
        if metrics and expected not in report:
            metric_mismatches.append(f"{key}:{expected}")

    if "tool_call_id=" not in report and "evidence_id=" not in report:
        missing_evidence.append("report_has_no_inline_trace_reference")
    for signal in result.get("news_signals", []):
        if not signal.get("evidence_ids") and not signal.get("source_tool_call_id"):
            missing_evidence.append(f"news_signal:{signal.get('title', '')}")
    if result.get("peer_summary", {}).get("table") and not result.get("peer_summary", {}).get("source_tool_call_id"):
        missing_evidence.append("product_benchmark_summary")

    forbidden_wording = contains_forbidden_wording(report)
    if forbidden_wording:
        failed_checks.append("forbidden_wording")

    passed = not failed_checks and not metric_mismatches and not missing_evidence
    penalty = 0.12 * len(failed_checks) + 0.1 * len(metric_mismatches) + 0.08 * len(missing_evidence)
    confidence_score = max(0.0, min(1.0, 1.0 - penalty))
    return {
        "pass": passed,
        "failed_checks": failed_checks,
        "metric_mismatches": metric_mismatches,
        "missing_evidence": missing_evidence,
        "forbidden_wording": forbidden_wording,
        "confidence_score": round(confidence_score, 3),
    }


def verifier_agent(state: dict[str, Any]) -> dict[str, Any]:
    result = state.get("result", {})
    verification = verify_result(result)
    event = {
        "event_type": "verification_result",
        "agent_name": "verifier_agent",
        "payload": verification,
    }
    result["verification_result"] = verification
    return {
        **state,
        "result": result,
        "verification_result": verification,
        "agent_events": [*state.get("agent_events", []), event],
    }
