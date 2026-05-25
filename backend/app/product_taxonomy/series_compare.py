from __future__ import annotations

from typing import Any

from backend.app.product_taxonomy.series_performance import compute_series_performance


def compare_series(series_ids: list[str] | None = None, report_date: str | None = None) -> dict[str, Any]:
    payload = compute_series_performance(report_date=report_date)
    rows = payload["series"]
    if series_ids:
        wanted = set(series_ids)
        rows = [row for row in rows if row["series_id"] in wanted]
    scatter = [
        {
            "series_id": row["series_id"],
            "series_name": row["series_name"],
            "x_volatility": row["volatility_mean"],
            "y_return": row["aum_weighted_return_3m"],
            "size_scale_bn": row["total_scale_bn"],
            "attention_product_count": row["attention_product_count"]
        }
        for row in rows
    ]
    summary = [
        f"{row['series_name']}：规模 {row['total_scale_bn']:.2f} 亿，近3月规模加权收益 {row['aum_weighted_return_3m']:.2%}，基准达标率 {row['benchmark_pass_rate']:.0%}。"
        for row in rows[:4]
    ]
    return {
        "report_date": report_date,
        "series_count": len(rows),
        "table": rows,
        "scatter": scatter,
        "weekly_summary": summary,
        "dpo_calibration_note": "DPO 仅用于周报文风、证据覆盖和风险提示校准；系列收益、回撤、波动等数字来自 deterministic series_performance。"
    }

