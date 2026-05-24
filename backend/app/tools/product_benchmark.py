"""Peer product comparison helpers for sanitized sample products."""
from __future__ import annotations

from typing import Any

from backend.app.utils.pandas_runtime import disable_optional_pandas_accelerators

disable_optional_pandas_accelerators()

import pandas as pd

RISK_LEVEL_VOL_PROXY = {
    "R1": 0.015,
    "R2": 0.035,
    "R3": 0.075,
    "R4": 0.16,
    "R5": 0.28,
}


def add_product_metrics(products: pd.DataFrame) -> pd.DataFrame:
    df = products.copy()
    df["period_return"] = df["latest_nav"] / df["base_nav"] - 1
    df["annualized_return"] = (df["latest_nav"] / df["base_nav"]) ** (252 / df["duration_days"]) - 1
    if "annualized_volatility" not in df.columns:
        df["annualized_volatility"] = df["risk_level"].map(RISK_LEVEL_VOL_PROXY).fillna(0.08)
    if "max_drawdown" not in df.columns:
        df["max_drawdown"] = -(df["annualized_volatility"] * 0.45).clip(lower=0.005, upper=0.25)
    if "sharpe_ratio" not in df.columns:
        df["sharpe_ratio"] = (df["annualized_return"] - 0.02) / df["annualized_volatility"].replace(0, pd.NA)
        df["sharpe_ratio"] = df["sharpe_ratio"].fillna(0.0)
    df["return_rank"] = df["annualized_return"].rank(ascending=False, method="min").astype(int)
    df["risk_adjusted_rank"] = df["sharpe_ratio"].rank(ascending=False, method="min").astype(int)
    return df.sort_values(["return_rank", "risk_adjusted_rank", "product_id"])


def filter_products(
    products: pd.DataFrame,
    asset_class: str | None = None,
    risk_level: str | None = None,
    channel: str | None = None,
) -> pd.DataFrame:
    df = products.copy()
    if asset_class:
        df = df[df["asset_class"].astype(str) == str(asset_class)]
    if risk_level:
        df = df[df["risk_level"].astype(str) == str(risk_level)]
    if channel:
        df = df[df["channel"].astype(str) == str(channel)]
    return df


def peer_summary(products: pd.DataFrame, filters: dict[str, Any] | None = None) -> dict:
    filters = filters or {}
    products = filter_products(
        products,
        asset_class=filters.get("asset_class"),
        risk_level=filters.get("risk_level"),
        channel=filters.get("channel"),
    )
    if products.empty:
        return {
            "product_count": 0,
            "return_leader_product": "",
            "return_leader_annualized": 0.0,
            "median_annualized_return": 0.0,
            "risk_levels": [],
            "channels": [],
            "table": [],
            "methodology": "样例产品表为空，未生成对标排序。",
        }

    df = add_product_metrics(products)
    return {
        "product_count": int(len(df)),
        "return_leader_product": str(df.iloc[0]["product_name"]),
        "return_leader_annualized": float(df.iloc[0]["annualized_return"]),
        "median_annualized_return": float(df["annualized_return"].median()),
        "risk_levels": sorted(df["risk_level"].unique().tolist()),
        "channels": sorted(df["channel"].unique().tolist()),
        "methodology": "基于样例净值、期限、风险等级和渠道字段做横向对标；排序仅用于投研材料整理。",
        "table": df[[
            "product_id",
            "product_name",
            "asset_class",
            "channel",
            "risk_level",
            "period_return",
            "annualized_return",
            "annualized_volatility",
            "max_drawdown",
            "sharpe_ratio",
            "return_rank",
            "risk_adjusted_rank",
        ]].to_dict(orient="records"),
    }
