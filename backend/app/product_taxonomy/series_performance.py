from __future__ import annotations

from typing import Any

from backend.app.product_taxonomy.series_classifier import classify_products


def _mean(values: list[float]) -> float:
    values = [float(value) for value in values if value is not None]
    return sum(values) / len(values) if values else 0.0


def _weighted_mean(rows: list[dict[str, Any]], metric: str) -> float:
    total = sum(float(row.get("product_scale_bn") or 0) for row in rows)
    if total <= 0:
        return _mean([float(row.get(metric) or 0) for row in rows])
    return sum(float(row.get(metric) or 0) * float(row.get("product_scale_bn") or 0) for row in rows) / total


def _median(values: list[float]) -> float:
    values = sorted(float(value) for value in values if value is not None)
    if not values:
      return 0.0
    mid = len(values) // 2
    return values[mid] if len(values) % 2 else (values[mid - 1] + values[mid]) / 2


def compute_series_performance(products: list[dict[str, Any]] | None = None, report_date: str | None = None) -> dict[str, Any]:
    classified = classify_products(products=products, report_date=report_date)["classified_products"]
    groups: dict[str, list[dict[str, Any]]] = {}
    names: dict[str, str] = {}
    for row in classified:
        series_id = str(row.get("suggested_series_id") or row.get("product_series") or "unclassified")
        groups.setdefault(series_id, []).append(row)
        names[series_id] = str(row.get("suggested_series_name") or row.get("product_series") or series_id)

    rows = []
    for series_id, members in groups.items():
        product_count = len(members)
        total_scale = sum(float(row.get("product_scale_bn") or 0) for row in members)
        benchmark_pass = sum(1 for row in members if row.get("benchmark_status") in {"in_range", "above_upper"})
        low_percentile = sum(1 for row in members if float(row.get("return_percentile") or 1) <= 0.3)
        attention = sum(
            1
            for row in members
            if row.get("benchmark_status") == "below_lower"
            or float(row.get("return_percentile") or 1) <= 0.3
            or float(row.get("scale_wow_bn") or 0) < -0.2
        )
        rows.append(
            {
                "series_id": series_id,
                "series_name": names[series_id],
                "product_count": product_count,
                "total_scale_bn": round(total_scale, 4),
                "scale_wow_bn": round(sum(float(row.get("scale_wow_bn") or 0) for row in members), 4),
                "scale_mom_bn": round(sum(float(row.get("scale_mom_bn") or 0) for row in members), 4),
                "equal_weight_return_1m": round(_mean([row.get("return_1m") for row in members]), 6),
                "equal_weight_return_3m": round(_mean([row.get("return_3m") for row in members]), 6),
                "equal_weight_return_6m": round(_mean([row.get("return_6m") for row in members]), 6),
                "aum_weighted_return_1m": round(_weighted_mean(members, "return_1m"), 6),
                "aum_weighted_return_3m": round(_weighted_mean(members, "return_3m"), 6),
                "aum_weighted_return_6m": round(_weighted_mean(members, "return_6m"), 6),
                "median_return_3m": round(_median([row.get("return_3m") for row in members]), 6),
                "max_drawdown_mean": round(_mean([row.get("max_drawdown") for row in members]), 6),
                "max_drawdown_max": round(min(float(row.get("max_drawdown") or 0) for row in members), 6),
                "volatility_mean": round(_mean([row.get("volatility") for row in members]), 6),
                "sharpe_mean": round(_mean([row.get("sharpe") for row in members]), 6),
                "benchmark_pass_rate": round(benchmark_pass / product_count if product_count else 0, 6),
                "low_percentile_product_count": low_percentile,
                "attention_product_count": attention,
                "evidence_ids": [row.get("evidence_id") for row in members if row.get("evidence_id")][:8]
            }
        )
    return {"report_date": report_date, "series_count": len(rows), "series": sorted(rows, key=lambda row: row["total_scale_bn"], reverse=True)}

