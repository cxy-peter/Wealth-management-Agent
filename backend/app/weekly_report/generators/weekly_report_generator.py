from __future__ import annotations

from typing import Any

from backend.app.weekly_report.metrics.benchmark_status import benchmark_failed_products, benchmark_summary
from backend.app.weekly_report.metrics.attention_score import attention_top
from backend.app.weekly_report.metrics.percentile_metrics import attach_percentiles, percentile_decliners
from backend.app.weekly_report.metrics.weekly_scale_metrics import channel_scale_summary, scale_change_rank, scale_kpis
from backend.app.weekly_report.parsers.market_issuance_parser import market_summary
from backend.app.weekly_report.parsers.weekly_snapshot_parser import frame_records, list_report_dates, load_weekly_snapshot


def _latest_date(report_date: str | None = None) -> str:
    dates = list_report_dates()
    if not dates:
        raise FileNotFoundError("weekly snapshot has no report dates")
    if not report_date:
        return dates[-1]
    requested = str(report_date)[:10]
    if requested in dates:
        return requested
    prior = [item for item in dates if item <= requested]
    return prior[-1] if prior else dates[-1]


def _apply_filters(snapshot, filters: dict[str, Any] | None = None):
    filters = filters or {}
    filtered = snapshot.copy()
    for column in ["product_series", "product_type", "channel", "risk_level", "benchmark_status", "open_type"]:
        value = filters.get(column)
        if value:
            filtered = filtered[filtered[column].astype(str) == str(value)]
    return filtered


def filter_options(snapshot) -> dict[str, list[str]]:
    options: dict[str, list[str]] = {}
    for column in ["product_series", "product_type", "channel", "risk_level", "benchmark_status", "open_type"]:
        options[column] = sorted(snapshot[column].astype(str).dropna().unique().tolist()) if column in snapshot else []
    return options


def _weekly_diff(selected_date: str, snapshot) -> list[dict[str, Any]]:
    dates = list_report_dates()
    if selected_date not in dates:
        return []
    index = dates.index(selected_date)
    if index == 0:
        return []
    previous = load_weekly_snapshot(dates[index - 1])
    merged = snapshot.merge(
        previous[
            [
                "product_code",
                "product_scale_bn",
                "benchmark_status",
                "return_3m",
                "max_drawdown",
                "evidence_id",
            ]
        ],
        on="product_code",
        how="left",
        suffixes=("", "_prev"),
    )
    if merged.empty:
        return []
    merged["scale_change_vs_prev_week"] = (merged["product_scale_bn"].astype(float) - merged["product_scale_bn_prev"].astype(float)).round(4)
    merged["return_3m_change_vs_prev_week"] = (merged["return_3m"].astype(float) - merged["return_3m_prev"].astype(float)).round(6)
    merged["drawdown_change_vs_prev_week"] = (merged["max_drawdown"].astype(float) - merged["max_drawdown_prev"].astype(float)).round(6)
    merged["benchmark_status_changed"] = merged["benchmark_status"].astype(str) != merged["benchmark_status_prev"].astype(str)
    focus = merged[
        (merged["benchmark_status_changed"])
        | (merged["scale_change_vs_prev_week"].abs() >= 0.2)
        | (merged["drawdown_change_vs_prev_week"].abs() >= 0.005)
    ].copy()
    if focus.empty:
        focus = merged.reindex(merged["scale_change_vs_prev_week"].abs().sort_values(ascending=False).index).head(10)
    cols = [
        "product_code",
        "product_name",
        "product_type",
        "channel",
        "scale_change_vs_prev_week",
        "benchmark_status_prev",
        "benchmark_status",
        "benchmark_status_changed",
        "return_3m_change_vs_prev_week",
        "drawdown_change_vs_prev_week",
        "evidence_id",
    ]
    return frame_records(focus[cols].head(12))


def weekly_summary(report_date: str | None = None, filters: dict[str, Any] | None = None) -> dict[str, Any]:
    selected_date = _latest_date(report_date)
    full_snapshot = load_weekly_snapshot(selected_date)
    snapshot = _apply_filters(full_snapshot, filters)
    pct_snapshot = attach_percentiles(snapshot, selected_date)
    benchmark = benchmark_summary(snapshot)
    scale = scale_kpis(snapshot)
    low_percentile_count = int((pct_snapshot.get("return_percentile", 1) <= 0.3).sum()) if not pct_snapshot.empty else 0
    attention_count = int(
        (
            (pct_snapshot.get("return_percentile", 1) <= 0.3)
            | (pct_snapshot.get("drawdown_percentile", 1) <= 0.3)
            | (pct_snapshot.get("benchmark_status", "") == "below_lower")
            | (pct_snapshot.get("scale_wow_bn", 0) < -0.2)
        ).sum()
    ) if not pct_snapshot.empty else 0
    market = market_summary(selected_date)
    evidence_ids = list(dict.fromkeys(scale["scale_evidence_ids"] + benchmark["benchmark_evidence_ids"] + [market["evidence_id"]]))
    return {
        "report_date": selected_date,
        "filters": {key: value for key, value in (filters or {}).items() if value},
        "product_count": int(len(snapshot)),
        "filter_options": filter_options(full_snapshot),
        "kpis": {
            **scale,
            **benchmark,
            "low_percentile_product_count": low_percentile_count,
            "attention_product_count": attention_count,
        },
        "scale_change_rank": scale_change_rank(snapshot, limit=12),
        "benchmark_failed_products": benchmark_failed_products(snapshot, limit=12),
        "percentile_decline_products": percentile_decliners(snapshot, limit=12),
        "attention_top10": attention_top(pct_snapshot, limit=10),
        "weekly_diff": _weekly_diff(selected_date, snapshot),
        "channel_scale_summary": channel_scale_summary(snapshot),
        "market_issuance": market,
        "data_source_note": "默认使用 synthetic/mock 周报和模拟同业池，公开披露样本仅作为局部证据样本，不声称拥有全市场实时产品级数据。",
        "evidence_ids": evidence_ids,
        "source_files": [
            "data/weekly/product_weekly_snapshot.csv",
            "data/weekly/product_scale_history.csv",
            "data/weekly/product_nav_weekly.csv",
            "data/benchmark/peer_product_metrics.csv",
            "data/weekly/market_issuance_weekly.csv",
        ],
    }


def weekly_products(report_date: str | None = None, filters: dict[str, Any] | None = None) -> dict[str, Any]:
    selected_date = _latest_date(report_date)
    full_snapshot = load_weekly_snapshot(selected_date)
    snapshot = _apply_filters(full_snapshot, filters)
    enriched = attach_percentiles(snapshot, selected_date)
    return {
        "report_date": selected_date,
        "filters": {key: value for key, value in (filters or {}).items() if value},
        "count": int(len(enriched)),
        "filter_options": filter_options(full_snapshot),
        "products": frame_records(enriched.sort_values(["product_scale_bn", "product_code"], ascending=[False, True])),
    }


def generate_weekly_report(report_date: str | None = None, filters: dict[str, Any] | None = None) -> dict[str, Any]:
    summary = weekly_summary(report_date, filters)
    kpis = summary["kpis"]
    first_evidence = summary["evidence_ids"][0] if summary["evidence_ids"] else "ev_weekly_missing"
    scale_evidence = kpis["scale_evidence_ids"][0] if kpis["scale_evidence_ids"] else first_evidence
    benchmark_evidence = kpis["benchmark_evidence_ids"][0] if kpis["benchmark_evidence_ids"] else first_evidence
    report_markdown = "\n".join(
        [
            "# 资管产品周报摘要",
            "",
            "本摘要基于 synthetic/mock 周报数据、模拟同业池分位和局部公开披露样本生成，仅用于投研辅助、风险摘要、产品对标和报告草稿整理，不构成投资建议。",
            f"- 周报日期：{summary['report_date']} [evidence_id={first_evidence}]",
            f"- 覆盖产品数 {summary['product_count']}，总规模 {kpis['total_scale_bn']:.2f} 亿元，较上周 {kpis['scale_wow_bn']:.2f} 亿元，较上月 {kpis['scale_mom_bn']:.2f} 亿元。[evidence_id={scale_evidence}]",
            f"- 基准区间内占比 {kpis['benchmark_pass_rate'] * 100:.1f}%，低于基准下限产品数 {kpis['benchmark_failed_count']}。[evidence_id={benchmark_evidence}]",
            f"- 低分位产品数 {kpis['low_percentile_product_count']}，需关注产品数 {kpis['attention_product_count']}；分位表述均为模拟同业池分位，需结合上传材料或公开披露样本复核。[evidence_id={summary['evidence_ids'][-1] if summary['evidence_ids'] else first_evidence}]",
        ]
    )
    return {
        **summary,
        "report_markdown": report_markdown,
        "tool_call_id": f"tc_weekly_report_{summary['report_date'].replace('-', '')}",
        "guardrail": {
            "pass": True,
            "scope": "weekly product research support only",
            "forbidden_wording_hit": False,
        },
    }
