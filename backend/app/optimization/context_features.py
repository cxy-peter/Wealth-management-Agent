"""Context feature extraction for route optimization."""
from __future__ import annotations

from typing import Any

FEATURE_NAMES = [
    "bias",
    "is_equity",
    "is_product",
    "is_risk_only",
    "is_product_compare",
    "risk_preference_conservative",
    "risk_preference_strict",
    "missing_fundamental_data",
    "news_count",
    "avg_news_risk",
    "max_drawdown_abs",
    "volatility",
    "product_pool_size",
    "product_risk_level_num",
    "latency_budget_ms",
    "human_review_required",
]

EQUITY_ASSET_CLASSES = {"权益增强", "多资产", "QDII/全球配置"}


def risk_level_num(value: str | int | float | None) -> float:
    if value is None:
        return 0.0
    text = str(value).upper().replace("R", "")
    try:
        return float(text)
    except ValueError:
        return 0.0


def extract_context(case: dict[str, Any], result: dict[str, Any] | None = None) -> dict[str, float]:
    result = result or {}
    analysis_type = str(case.get("analysis_type", "full")).lower()
    risk_preference = str(case.get("risk_preference", "balanced")).lower()
    asset_class = str(case.get("asset_class") or case.get("product_filters", {}).get("asset_class") or "")
    product_pool_size = case.get("product_pool_size", result.get("peer_summary", {}).get("product_count", 0))
    avg_news_risk = case.get("avg_news_risk", result.get("news_summary", {}).get("avg_risk", 0))
    max_drawdown_abs = case.get("max_drawdown_abs", abs(result.get("metrics", {}).get("max_drawdown", 0)))
    volatility = case.get("volatility", result.get("metrics", {}).get("annualized_volatility", 0))
    product_risk_level = case.get("product_risk_level", case.get("product_filters", {}).get("risk_level"))
    human_review = bool(case.get("human_review_required", False))

    return {
        "bias": 1.0,
        "is_equity": 1.0 if asset_class in EQUITY_ASSET_CLASSES or analysis_type in {"equity", "stock"} else 0.0,
        "is_product": 1.0 if case.get("symbol", "").startswith("SP") or analysis_type == "product" else 0.0,
        "is_risk_only": 1.0 if analysis_type in {"risk", "risk_only"} else 0.0,
        "is_product_compare": 1.0 if analysis_type in {"product", "product_compare", "benchmark"} else 0.0,
        "risk_preference_conservative": 1.0 if risk_preference == "conservative" else 0.0,
        "risk_preference_strict": 1.0 if risk_preference == "strict" else 0.0,
        "missing_fundamental_data": 1.0 if case.get("missing_fundamental_data", False) else 0.0,
        "news_count": min(float(case.get("news_count", result.get("news_summary", {}).get("signal_count", 0))) / 10.0, 1.0),
        "avg_news_risk": min(float(avg_news_risk) / 5.0, 1.0),
        "max_drawdown_abs": min(float(max_drawdown_abs) / 0.30, 1.0),
        "volatility": min(float(volatility) / 0.50, 1.0),
        "product_pool_size": min(float(product_pool_size) / 120.0, 1.0),
        "product_risk_level_num": min(risk_level_num(product_risk_level) / 5.0, 1.0),
        "latency_budget_ms": min(float(case.get("latency_budget_ms", 800)) / 2000.0, 1.0),
        "human_review_required": 1.0 if human_review else 0.0,
    }


def vectorize_context(context: dict[str, float]) -> list[float]:
    return [float(context.get(name, 0.0)) for name in FEATURE_NAMES]
