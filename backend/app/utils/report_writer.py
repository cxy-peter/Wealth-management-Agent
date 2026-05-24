"""Markdown report renderer."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.app.agents.risk_guardrail_agent import FORBIDDEN_PHRASES
from backend.app.tools.metrics import format_float, format_pct

DISCLAIMER = (
    "本报告仅用于投研辅助、模型流程展示和教育研究，不构成投资建议、"
    "交易指令或收益承诺。所有样例数据均为脱敏/模拟数据。"
)


def _call_by_name(calls: list[dict[str, Any]], tool_name: str) -> dict[str, Any]:
    for item in reversed(calls):
        if item.get("tool_name") == tool_name:
            return item
    return {}


def _trace(record: dict[str, Any]) -> str:
    if not record:
        return "[tool_call_id=missing]"
    evidence = (record.get("evidence_ids") or ["missing"])[0]
    return f"[tool_call_id={record.get('tool_call_id', 'missing')}; evidence_id={evidence}]"


def _product_rows(rows: list[dict[str, Any]], source: str) -> str:
    lines = [
        "| 产品 | 资产类别 | 渠道 | 风险等级 | 年化收益 | 年化波动 | 最大回撤 | Sharpe | 收益排名 | 追溯 |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for item in rows:
        lines.append(
            f"| {item['product_name']} | {item['asset_class']} | {item.get('channel', '')} | {item['risk_level']} | "
            f"{format_pct(item['annualized_return'])} | {format_pct(item.get('annualized_volatility', 0))} | "
            f"{format_pct(item.get('max_drawdown', 0))} | {format_float(item.get('sharpe_ratio', 0))} | "
            f"{item['return_rank']} | {source} |"
        )
    return "\n".join(lines)


def _news_rows(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| 日期 | 标题 | 情绪分 | 风险分 | 模型模式 | 证据 | 追溯 |",
        "|---|---|---:|---:|---|---|---|",
    ]
    for item in rows:
        trace = f"[tool_call_id={item.get('source_tool_call_id', 'missing')}; evidence_id={(item.get('evidence_ids') or ['missing'])[0]}]"
        lines.append(
            f"| {item['date']} | {item['title']} | {item['sentiment_score']} | "
            f"{item['risk_score']} | {item.get('model_mode', 'rule-based-fallback')} | {item['evidence']} | {trace} |"
        )
    return "\n".join(lines)


def _tool_rows(rows: list[dict[str, Any]]) -> str:
    lines = ["| Tool call | Tool | 状态 | 耗时 | Evidence |", "|---|---|---:|---:|---|"]
    for item in rows:
        status = "pass" if item.get("success") else "fail"
        lines.append(
            f"| {item.get('tool_call_id', '')} | {item.get('tool_name', '')} | {status} | "
            f"{item.get('latency_ms', '')} ms | {', '.join(item.get('evidence_ids', []))} |"
        )
    return "\n".join(lines)


def _bullet_rows(items: list[str], fallback_trace: str) -> str:
    if not items:
        return f"- 暂无样例字段。{fallback_trace}"
    return "\n".join(f"- {item if 'tool_call_id=' in item or 'evidence_id=' in item else item + ' ' + fallback_trace}" for item in items)


def _sanitize(report: str) -> str:
    clean = report
    for phrase in FORBIDDEN_PHRASES:
        clean = clean.replace(phrase, "合规拦截表达")
    return clean


def _default_metrics(symbol: str) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "observations": 0,
        "start_value": 0.0,
        "end_value": 0.0,
        "total_return": 0.0,
        "annualized_return": 0.0,
        "annualized_volatility": 0.0,
        "max_drawdown": 0.0,
        "sharpe_ratio": 0.0,
    }


def render_report(result: dict[str, Any]) -> str:
    tool_calls = result.get("tool_calls", [])
    metrics_call = _call_by_name(tool_calls, "calculate_metrics")
    news_call = _call_by_name(tool_calls, "classify_news_risk")
    product_call = _call_by_name(tool_calls, "product_benchmark")
    guardrail_call = _call_by_name(tool_calls, "risk_guardrail_check")
    fundamental_call = _call_by_name(tool_calls, "load_fundamental_snapshot")
    valuation_call = _call_by_name(tool_calls, "load_valuation_snapshot")

    metrics = {**_default_metrics(result["symbol"]), **result.get("metrics", {})}
    peer = {"product_count": 0, "risk_levels": [], "table": [], **result.get("peer_summary", {})}
    news_summary = {
        "signal_count": 0,
        "avg_sentiment": 0,
        "avg_risk": 0,
        "top_risks": [],
        **result.get("news_summary", {}),
    }
    risk_flags = result.get("risk_flags", [])
    fundamental = result.get("fundamental_analysis", {})
    valuation = result.get("valuation_analysis", {})
    technical = result.get("technical_analysis", {})
    planner = result.get("planner_plan", {})
    qwen_meta = result.get("model_metadata", {}).get("qwen_risk_adapter", {})

    metric_trace = _trace(metrics_call)
    product_trace = _trace(product_call)
    news_trace = _trace(news_call)
    guardrail_trace = _trace(guardrail_call)

    report = f"""# 资管投研辅助 Agent 报告：{result['company']}（{result['symbol']}）

## 0. 合规说明

{DISCLAIMER} {guardrail_trace}

## 1. Planner、数据与工具调用摘要

- Planner task_type：{planner.get('task_type', 'standard_research')}；analysis_depth：{planner.get('analysis_depth', 'standard')}。[evidence_id=ev_planner_plan]
- 行情/净值样本：{metrics['observations']} 条观测，起始值 {metrics['start_value']:.3f}，结束值 {metrics['end_value']:.3f}。{metric_trace}
- 新闻样本：{news_summary['signal_count']} 条，平均情绪分 {news_summary['avg_sentiment']}，平均风险分 {news_summary['avg_risk']}。{news_trace}
- 同业产品样本：{peer.get('product_count', 0)} 款，覆盖风险等级：{', '.join(peer.get('risk_levels', []))}。{product_trace}
- 数据模式：sample/mock；Qwen 风险适配器：{qwen_meta.get('mode', 'rule-based-fallback')}。{news_trace}

{_tool_rows(tool_calls)}

## 2. 核心量化指标

| 指标 | 数值 | 追溯 |
|---|---:|---|
| 区间收益 | {format_pct(metrics['total_return'])} | {metric_trace} |
| 年化收益 | {format_pct(metrics['annualized_return'])} | {metric_trace} |
| 年化波动率 | {format_pct(metrics['annualized_volatility'])} | {metric_trace} |
| 最大回撤 | {format_pct(metrics['max_drawdown'])} | {metric_trace} |
| Sharpe Ratio | {format_float(metrics['sharpe_ratio'])} | {metric_trace} |

## 3. 基本面与估值摘要

基本面标签：{fundamental.get('quality_label', 'NA')} {_trace(fundamental_call)}

{_bullet_rows(fundamental.get('points', []), _trace(fundamental_call))}

估值区间：{valuation.get('valuation_band', 'NA')} {_trace(valuation_call)}

{_bullet_rows(valuation.get('points', []), _trace(valuation_call))}

## 4. 技术面风险观察

- 趋势标签：{technical.get('trend_label', 'NA')} {metric_trace}
- 波动状态：{technical.get('risk_regime', 'NA')} {metric_trace}
- MA5 / MA20：{technical.get('ma5', 0):.3f} / {technical.get('ma20', 0):.3f} {metric_trace}
- 5 日动量 / 20 日动量：{format_pct(technical.get('momentum_5d', 0))} / {format_pct(technical.get('momentum_20d', 0))} {metric_trace}

{_bullet_rows(technical.get('points', []), metric_trace)}

## 5. 同业产品对比样例

{_product_rows(peer.get('table', []), product_trace)}

方法说明：{peer.get('methodology', '')} {product_trace}

## 6. 新闻情绪与风险信号

{_news_rows(result.get('news_signals', []))}

重点风险标题：{'; '.join(news_summary.get('top_risks', [])) if news_summary.get('top_risks') else '暂无'}。{news_trace}

## 7. 风险提示与可追溯结论

{chr(10).join(f'- {flag} {guardrail_trace}' for flag in risk_flags)}

系统结论：当前输出适合作为投研初筛、风险摘要、产品对标和材料整理的辅助结果。正式决策前，应结合真实数据源、基金/理财产品说明书、投委会口径、合规审查与人工复核。{guardrail_trace}
"""
    return _sanitize(report)


def write_report(report: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    return output_path
