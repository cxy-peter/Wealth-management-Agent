"""Product comparison helpers for synthetic wealth-management products."""
from __future__ import annotations

from typing import Any

from backend.app.utils.pandas_runtime import disable_optional_pandas_accelerators

disable_optional_pandas_accelerators()

import numpy as np
import pandas as pd

from backend.app.tools.data_loader import load_product_nav

RISK_LEVEL_VOL_PROXY = {
    "R1": 0.015,
    "R2": 0.035,
    "R3": 0.075,
    "R4": 0.16,
    "R5": 0.28,
}

FILTER_COLUMNS = [
    "duration_bucket",
    "liquidity_type",
    "strategy_type",
    "channel",
    "risk_level",
    "asset_class",
]


def _jsonable(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _annualized_return(values: pd.Series, periods_per_year: int = 52) -> float:
    clean = values.dropna().astype(float)
    if len(clean) <= 1 or clean.iloc[0] <= 0:
        return 0.0
    return float((clean.iloc[-1] / clean.iloc[0]) ** (periods_per_year / (len(clean) - 1)) - 1)


def _annualized_volatility(values: pd.Series, periods_per_year: int = 52) -> float:
    returns = values.astype(float).pct_change().dropna()
    if returns.empty:
        return 0.0
    return float(returns.std(ddof=1) * np.sqrt(periods_per_year))


def _max_drawdown(values: pd.Series) -> float:
    clean = values.dropna().astype(float)
    if clean.empty:
        return 0.0
    drawdown = clean / clean.cummax() - 1.0
    return float(drawdown.min())


def _drawdown_recovery_days(nav: pd.DataFrame) -> int:
    if nav.empty:
        return 0
    frame = nav.sort_values("date").copy()
    frame["running_max"] = frame["nav"].cummax()
    frame["drawdown"] = frame["nav"] / frame["running_max"] - 1.0
    trough_idx = frame["drawdown"].idxmin()
    trough = frame.loc[trough_idx]
    if float(trough["drawdown"]) >= 0:
        return 0
    target = float(trough["running_max"])
    recovered = frame[(frame["date"] > trough["date"]) & (frame["nav"] >= target)]
    if recovered.empty:
        return int((frame["date"].max() - trough["date"]).days)
    return int((recovered.iloc[0]["date"] - trough["date"]).days)


def _win_rate(nav: pd.DataFrame) -> float:
    frame = nav.sort_values("date").copy()
    returns = frame["nav"].astype(float).pct_change()
    benchmark_returns = frame["benchmark_nav"].astype(float).pct_change()
    valid = pd.DataFrame({"r": returns, "b": benchmark_returns}).dropna()
    if valid.empty:
        return 0.0
    return float((valid["r"] > valid["b"]).mean())


def _metric_row(product: pd.Series, nav: pd.DataFrame) -> dict[str, Any]:
    values = nav["nav"].astype(float)
    benchmark_values = nav["benchmark_nav"].astype(float)
    period_return = float(values.iloc[-1] / values.iloc[0] - 1) if len(values) > 1 else 0.0
    benchmark_return = (
        float(benchmark_values.iloc[-1] / benchmark_values.iloc[0] - 1) if len(benchmark_values) > 1 else 0.0
    )
    ann_return = _annualized_return(values)
    ann_vol = _annualized_volatility(values)
    max_dd = _max_drawdown(values)
    sharpe = float((ann_return - 0.02) / ann_vol) if ann_vol > 0 else 0.0
    calmar = float(ann_return / abs(max_dd)) if max_dd < 0 else 0.0
    product_id = str(product["product_id"])
    return {
        **product.to_dict(),
        "period_return": period_return,
        "annualized_return": ann_return,
        "annualized_volatility": ann_vol,
        "max_drawdown": max_dd,
        "sharpe_ratio": sharpe,
        "calmar_ratio": calmar,
        "benchmark_excess_return": period_return - benchmark_return,
        "win_rate": _win_rate(nav),
        "drawdown_recovery_days": _drawdown_recovery_days(nav),
        "nav_observations": int(len(nav)),
        "metric_evidence_id": f"ev_product_metric_{product_id}",
        "nav_evidence_id": f"ev_product_nav_{product_id}",
        "source_tool_call_id": "",
    }


def add_product_metrics(products: pd.DataFrame, nav: pd.DataFrame | None = None) -> pd.DataFrame:
    """Calculate product metrics from weekly NAV; use legacy fields as fallback."""

    if nav is not None and not nav.empty and "product_id" in products.columns:
        rows = []
        nav_groups = {str(pid): frame.sort_values("date") for pid, frame in nav.groupby("product_id")}
        for _, product in products.iterrows():
            product_nav = nav_groups.get(str(product["product_id"]))
            if product_nav is None or product_nav.empty:
                continue
            rows.append(_metric_row(product, product_nav))
        if rows:
            df = pd.DataFrame(rows)
            df["return_rank"] = df["annualized_return"].rank(ascending=False, method="min").astype(int)
            df["risk_adjusted_rank"] = df["sharpe_ratio"].rank(ascending=False, method="min").astype(int)
            df["calmar_rank"] = df["calmar_ratio"].rank(ascending=False, method="min").astype(int)
            return df.sort_values(["return_rank", "risk_adjusted_rank", "product_id"])

    df = products.copy()
    if "base_nav" not in df.columns or "latest_nav" not in df.columns:
        return pd.DataFrame(columns=[*products.columns, "annualized_return"])
    df["period_return"] = df["latest_nav"] / df["base_nav"] - 1
    df["annualized_return"] = (df["latest_nav"] / df["base_nav"]) ** (252 / df["duration_days"]) - 1
    if "annualized_volatility" not in df.columns:
        df["annualized_volatility"] = df["risk_level"].map(RISK_LEVEL_VOL_PROXY).fillna(0.08)
    if "max_drawdown" not in df.columns:
        df["max_drawdown"] = -(df["annualized_volatility"] * 0.45).clip(lower=0.005, upper=0.25)
    if "sharpe_ratio" not in df.columns:
        df["sharpe_ratio"] = (df["annualized_return"] - 0.02) / df["annualized_volatility"].replace(0, pd.NA)
        df["sharpe_ratio"] = df["sharpe_ratio"].fillna(0.0)
    df["calmar_ratio"] = df["annualized_return"] / df["max_drawdown"].abs().replace(0, pd.NA)
    df["calmar_ratio"] = df["calmar_ratio"].fillna(0.0)
    df["benchmark_excess_return"] = 0.0
    df["win_rate"] = 0.0
    df["drawdown_recovery_days"] = 0
    df["return_rank"] = df["annualized_return"].rank(ascending=False, method="min").astype(int)
    df["risk_adjusted_rank"] = df["sharpe_ratio"].rank(ascending=False, method="min").astype(int)
    df["calmar_rank"] = df["calmar_ratio"].rank(ascending=False, method="min").astype(int)
    df["metric_evidence_id"] = df["product_id"].map(lambda item: f"ev_product_metric_{item}")
    df["nav_evidence_id"] = df["product_id"].map(lambda item: f"ev_product_legacy_nav_{item}")
    df["source_tool_call_id"] = ""
    return df.sort_values(["return_rank", "risk_adjusted_rank", "product_id"])


def filter_products(products: pd.DataFrame, **filters: Any) -> pd.DataFrame:
    df = products.copy()
    for column in FILTER_COLUMNS:
        value = filters.get(column)
        if value and column in df.columns:
            df = df[df[column].astype(str) == str(value)]
    return df


def product_filter_options(products: pd.DataFrame) -> dict[str, list[str]]:
    options: dict[str, list[str]] = {}
    for column in FILTER_COLUMNS:
        if column in products.columns:
            options[column] = sorted(str(item) for item in products[column].dropna().unique().tolist())
        else:
            options[column] = []
    return options


def peer_summary(products: pd.DataFrame, filters: dict[str, Any] | None = None) -> dict[str, Any]:
    filters = {key: value for key, value in (filters or {}).items() if value}
    all_options = product_filter_options(products)
    filtered = filter_products(products, **filters)
    if filtered.empty:
        return {
            "product_count": 0,
            "product_universe_size": int(len(products)),
            "return_leader_product": "",
            "return_leader_annualized": 0.0,
            "median_annualized_return": 0.0,
            "risk_levels": [],
            "channels": [],
            "filter_options": all_options,
            "filters": filters,
            "table": [],
            "methodology": "样例产品池筛选结果为空，未生成对标排序。",
        }

    nav = load_product_nav()
    df = add_product_metrics(filtered, nav=nav)
    if df.empty:
        return {
            "product_count": 0,
            "product_universe_size": int(len(products)),
            "return_leader_product": "",
            "return_leader_annualized": 0.0,
            "median_annualized_return": 0.0,
            "risk_levels": [],
            "channels": [],
            "filter_options": all_options,
            "filters": filters,
            "table": [],
            "methodology": "样例产品池缺少可计算净值，已保留旧字段 fallback。",
        }

    table_columns = [
        "product_id",
        "product_name",
        "issuer_type",
        "asset_class",
        "strategy_type",
        "channel",
        "risk_level",
        "product_type",
        "liquidity_type",
        "duration_days",
        "duration_bucket",
        "benchmark",
        "period_return",
        "annualized_return",
        "annualized_volatility",
        "max_drawdown",
        "sharpe_ratio",
        "calmar_ratio",
        "benchmark_excess_return",
        "win_rate",
        "drawdown_recovery_days",
        "return_rank",
        "risk_adjusted_rank",
        "calmar_rank",
        "metric_evidence_id",
        "nav_evidence_id",
        "source_tool_call_id",
    ]
    available_columns = [column for column in table_columns if column in df.columns]
    return {
        "product_count": int(len(df)),
        "product_universe_size": int(len(products)),
        "return_leader_product": str(df.iloc[0]["product_name"]),
        "return_leader_annualized": float(df.iloc[0]["annualized_return"]),
        "median_annualized_return": float(df["annualized_return"].median()),
        "risk_levels": sorted(df["risk_level"].astype(str).unique().tolist()),
        "channels": sorted(df["channel"].astype(str).unique().tolist()),
        "filter_options": all_options,
        "filters": filters,
        "methodology": (
            "基于 synthetic sample 产品周度 NAV 与 benchmark_nav 计算收益、波动、回撤、"
            "Sharpe、Calmar、benchmark excess、胜率和回撤修复天数；排序仅用于投研材料整理。"
        ),
        "table": _jsonable(df[available_columns].to_dict(orient="records")),
    }


def product_detail(products: pd.DataFrame, product_id: str) -> dict[str, Any] | None:
    rows = products[products["product_id"].astype(str) == str(product_id)]
    if rows.empty:
        return None
    product = _jsonable(rows.iloc[0].to_dict())
    nav = load_product_nav(product_id)
    metrics = add_product_metrics(pd.DataFrame([product]), nav=nav)
    metric_payload = _jsonable(metrics.iloc[0].to_dict()) if not metrics.empty else {}
    return {
        "product": product,
        "metrics": metric_payload,
        "evidence_ids": [
            f"ev_product_catalog_{product_id}",
            metric_payload.get("metric_evidence_id", f"ev_product_metric_{product_id}"),
        ],
    }
