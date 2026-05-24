from __future__ import annotations

from typing import Any

from backend.app.weekly_report.parsers.weekly_snapshot_parser import frame_records


def _reason_tags(row: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    if row.get("benchmark_status") == "below_lower":
        tags.append("基准未达标")
    if float(row.get("scale_wow_bn", 0) or 0) < -0.2:
        tags.append("规模下降")
    if float(row.get("return_percentile", 1) or 1) <= 0.35:
        tags.append("收益分位偏低")
    if float(row.get("drawdown_percentile", 1) or 1) <= 0.35:
        tags.append("回撤分位偏低")
    for field in ["return_3m", "max_drawdown", "volatility", "sharpe"]:
        if row.get(field) is None:
            tags.append("关键字段缺失")
            break
    return tags or ["常规跟踪"]


def attach_attention_scores(snapshot) -> Any:
    if snapshot.empty:
        return snapshot.copy()
    frame = snapshot.copy()
    benchmark_fail = (frame["benchmark_status"].astype(str) == "below_lower").astype(float)
    scale_drop = (-frame["scale_wow_bn"].astype(float)).clip(lower=0) / 1.0
    low_return = (1 - frame.get("return_percentile", 1).astype(float)).clip(0, 1)
    drawdown = (1 - frame.get("drawdown_percentile", 1).astype(float)).clip(0, 1)
    missing = frame[["return_3m", "max_drawdown", "volatility", "sharpe"]].isna().any(axis=1).astype(float)
    frame["attention_score"] = (
        0.30 * benchmark_fail.clip(0, 1)
        + 0.25 * scale_drop.clip(0, 1)
        + 0.20 * low_return
        + 0.15 * drawdown
        + 0.10 * missing
    ).round(4)
    frame["attention_reason_tags"] = [_reason_tags(row) for row in frame.to_dict(orient="records")]
    return frame


def attention_top(snapshot, limit: int = 10) -> list[dict[str, Any]]:
    scored = attach_attention_scores(snapshot)
    cols = [
        "report_date",
        "product_code",
        "product_name",
        "product_type",
        "channel",
        "risk_level",
        "benchmark_status",
        "scale_wow_bn",
        "return_3m",
        "max_drawdown",
        "return_percentile",
        "drawdown_percentile",
        "attention_score",
        "attention_reason_tags",
        "evidence_id",
    ]
    available = [col for col in cols if col in scored.columns]
    return frame_records(scored.sort_values("attention_score", ascending=False)[available].head(limit))
