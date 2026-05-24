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


def _product_rows(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| 产品 | 资产类别 | 渠道 | 风险等级 | 年化收益 | 年化波动 | 最大回撤 | Sharpe | 收益排名 |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in rows:
        lines.append(
            f"| {item['product_name']} | {item['asset_class']} | {item['channel']} | {item['risk_level']} | "
            f"{format_pct(item['annualized_return'])} | {format_pct(item['annualized_volatility'])} | "
            f"{format_pct(item['max_drawdown'])} | {format_float(item['sharpe_ratio'])} | {item['return_rank']} |"
        )
    return "\n".join(lines)


def _news_rows(rows: list[dict[str, Any]]) -> str:
    lines = ["| 日期 | 标题 | 情绪分 | 风险分 | 模型模式 | 证据 |", "|---|---|---:|---:|---|---|"]
    for item in rows:
        lines.append(
            f"| {item['date']} | {item['title']} | {item['sentiment_score']} | "
            f"{item['risk_score']} | {item.get('model_mode', 'rule-based-fallback')} | {item['evidence']} |"
        )
    return "\n".join(lines)


def _tool_rows(rows: list[dict[str, Any]]) -> str:
    lines = ["| Agent | Tool | 状态 | 行数/条数 | 模式 |", "|---|---|---:|---:|---|"]
    for item in rows:
        status = "pass" if item.get("success") else "fail"
        lines.append(
            f"| {item.get('agent', '')} | {item.get('tool', '')} | {status} | "
            f"{item.get('rows', '')} | {item.get('mode', '')} |"
        )
    return "\n".join(lines)


def _bullet_rows(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- 暂无样例字段。"


def _sanitize(report: str) -> str:
    clean = report
    for phrase in FORBIDDEN_PHRASES:
        clean = clean.replace(phrase, "合规拦截表达")
    return clean


def render_report(result: dict[str, Any]) -> str:
    metrics = result["metrics"]
    peer = result["peer_summary"]
    news_summary = result["news_summary"]
    risk_flags = result["risk_flags"]
    fundamental = result.get("fundamental_analysis", {})
    valuation = result.get("valuation_analysis", {})
    technical = result.get("technical_analysis", {})
    tool_calls = result.get("tool_calls", [])
    qwen_meta = result.get("model_metadata", {}).get("qwen_risk_adapter", {})

    report = f"""# 资管投研辅助 Agent 报告：{result['company']}（{result['symbol']}）

## 0. 合规说明

{DISCLAIMER}

## 1. 数据与工具调用摘要

- 行情/净值样本：{metrics['observations']} 条观测，起始值 {metrics['start_value']:.3f}，结束值 {metrics['end_value']:.3f}。
- 新闻样本：{news_summary['signal_count']} 条，平均情绪分 {news_summary['avg_sentiment']}，平均风险分 {news_summary['avg_risk']}。
- 同业产品样本：{peer['product_count']} 款，覆盖风险等级：{', '.join(peer['risk_levels'])}。
- 数据模式：sample/mock；Qwen 风险适配器：{qwen_meta.get('mode', 'rule-based-fallback')}。

{_tool_rows(tool_calls)}

## 2. 核心量化指标

| 指标 | 数值 |
|---|---:|
| 区间收益 | {format_pct(metrics['total_return'])} |
| 年化收益 | {format_pct(metrics['annualized_return'])} |
| 年化波动率 | {format_pct(metrics['annualized_volatility'])} |
| 最大回撤 | {format_pct(metrics['max_drawdown'])} |
| Sharpe Ratio | {format_float(metrics['sharpe_ratio'])} |

## 3. 基本面与估值摘要

基本面标签：{fundamental.get('quality_label', 'NA')}

{_bullet_rows(fundamental.get('points', []))}

估值区间：{valuation.get('valuation_band', 'NA')}

{_bullet_rows(valuation.get('points', []))}

## 4. 技术面风险观察

- 趋势标签：{technical.get('trend_label', 'NA')}
- 波动状态：{technical.get('risk_regime', 'NA')}
- MA5 / MA20：{technical.get('ma5', 0):.3f} / {technical.get('ma20', 0):.3f}
- 5 日动量 / 20 日动量：{format_pct(technical.get('momentum_5d', 0))} / {format_pct(technical.get('momentum_20d', 0))}

{_bullet_rows(technical.get('points', []))}

## 5. 同业产品对比样例

{_product_rows(peer['table'])}

方法说明：{peer.get('methodology', '')}

## 6. 新闻情绪与风险信号

{_news_rows(result['news_signals'])}

重点风险标题：{'; '.join(news_summary['top_risks']) if news_summary['top_risks'] else '暂无'}。

## 7. 风险提示与可追溯结论

{chr(10).join(f'- {flag}' for flag in risk_flags)}

系统结论：当前输出适合作为投研初筛、风险摘要、产品对标和材料整理的辅助结果。正式决策前，应结合真实数据源、基金/理财产品说明书、投委会口径、合规审查与人工复核。
"""
    return _sanitize(report)


def write_report(report: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    return output_path
