"""Context feature extraction for weekly-report route optimization."""
from __future__ import annotations

from typing import Any

FEATURE_NAMES = [
    "bias",
    "is_weekly_report",
    "is_product_benchmark",
    "is_market_update",
    "is_high_risk_product",
    "benchmark_failed_count",
    "scale_drop_count",
    "product_pool_size",
    "avg_return_percentile",
    "avg_drawdown_percentile",
    "missing_nav_ratio",
    "market_new_issue_count",
    "latency_budget_ms",
    "human_review_required",
]


def _bounded(value: Any, denominator: float, default: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = default
    return min(max(numeric / denominator, 0.0), 1.0)


def extract_context(case: dict[str, Any], result: dict[str, Any] | None = None) -> dict[str, float]:
    result = result or {}
    scenario = str(case.get("scenario", "")).lower()
    request_type = str(case.get("request_type", case.get("analysis_type", "weekly_report"))).lower()
    risk_level = str(case.get("risk_level", case.get("product_risk_level", ""))).upper()

    benchmark_failed_count = case.get(
        "benchmark_failed_count",
        result.get("kpis", {}).get("benchmark_failed_count", 0),
    )
    scale_drop_count = case.get("scale_drop_count", result.get("kpis", {}).get("scale_drop_count", 0))
    product_pool_size = case.get("product_pool_size", result.get("product_count", 0))
    avg_return_percentile = case.get("avg_return_percentile", result.get("avg_return_percentile", 0.5))
    avg_drawdown_percentile = case.get("avg_drawdown_percentile", result.get("avg_drawdown_percentile", 0.5))
    missing_nav_ratio = case.get("missing_nav_ratio", result.get("missing_nav_ratio", 0))
    market_new_issue_count = case.get(
        "market_new_issue_count",
        result.get("market_issuance", {}).get("new_product_count", 0),
    )

    return {
        "bias": 1.0,
        "is_weekly_report": 1.0 if request_type in {"weekly_report", "standard_weekly_report", "full"} else 0.0,
        "is_product_benchmark": 1.0
        if request_type in {"product_benchmark", "benchmark", "benchmark_only", "product"}
        or "benchmark" in scenario
        else 0.0,
        "is_market_update": 1.0 if request_type in {"market_update", "market_update_only"} or "market" in scenario else 0.0,
        "is_high_risk_product": 1.0 if risk_level in {"R4", "R5"} or bool(case.get("is_high_risk_product", False)) else 0.0,
        "benchmark_failed_count": _bounded(benchmark_failed_count, 30.0),
        "scale_drop_count": _bounded(scale_drop_count, 40.0),
        "product_pool_size": _bounded(product_pool_size, 160.0),
        "avg_return_percentile": min(max(float(avg_return_percentile), 0.0), 1.0),
        "avg_drawdown_percentile": min(max(float(avg_drawdown_percentile), 0.0), 1.0),
        "missing_nav_ratio": min(max(float(missing_nav_ratio), 0.0), 1.0),
        "market_new_issue_count": _bounded(market_new_issue_count, 120.0),
        "latency_budget_ms": _bounded(case.get("latency_budget_ms", 900), 2500.0),
        "human_review_required": 1.0 if bool(case.get("human_review_required", False)) else 0.0,
    }


def vectorize_context(context: dict[str, float]) -> list[float]:
    return [float(context.get(name, 0.0)) for name in FEATURE_NAMES]
