from __future__ import annotations

from math import sqrt
from typing import Any

from backend.app.utils.pandas_runtime import disable_optional_pandas_accelerators

disable_optional_pandas_accelerators()

import pandas as pd


def nav_metrics_for_product(nav: pd.DataFrame, product_code: str, report_date: str | None = None) -> dict[str, Any]:
    rows = nav[nav["product_code"].astype(str) == str(product_code)].copy()
    if report_date and not rows.empty:
        rows = rows[rows["nav_date"] <= pd.Timestamp(report_date)]
    rows = rows.sort_values("nav_date").tail(53)
    if rows.empty:
        return {
            "product_code": product_code,
            "return_3m": 0.0,
            "max_drawdown": 0.0,
            "volatility": 0.0,
            "latest_nav": 1.0,
            "nav_evidence_ids": [],
        }
    values = rows["nav"].astype(float).tolist()
    if len(values) == 1:
        return {
            "product_code": product_code,
            "return_3m": 0.0,
            "max_drawdown": 0.0,
            "volatility": 0.0,
            "latest_nav": round(values[-1], 6),
            "nav_evidence_ids": rows["nav_evidence_id"].astype(str).tail(5).tolist(),
        }
    returns = [values[i] / values[i - 1] - 1 for i in range(1, len(values))]
    running_high = values[0]
    drawdowns: list[float] = []
    for value in values:
        running_high = max(running_high, value)
        drawdowns.append(value / running_high - 1)
    avg_return = sum(returns) / len(returns)
    variance = sum((item - avg_return) ** 2 for item in returns) / max(len(returns) - 1, 1)
    weeks = min(13, len(values) - 1)
    return_3m = values[-1] / values[-weeks - 1] - 1 if weeks else 0.0
    return {
        "product_code": product_code,
        "return_3m": round(float(return_3m), 6),
        "max_drawdown": round(float(min(drawdowns)), 6),
        "volatility": round(float(sqrt(variance) * sqrt(52)), 6),
        "latest_nav": round(float(values[-1]), 6),
        "nav_evidence_ids": rows["nav_evidence_id"].astype(str).tail(5).tolist(),
    }


def compare_snapshot_to_nav(snapshot_row: dict[str, Any], nav: pd.DataFrame, tolerance: float = 1e-4) -> list[dict[str, Any]]:
    metrics = nav_metrics_for_product(
        nav,
        str(snapshot_row["product_code"]),
        str(snapshot_row["report_date"])[:10],
    )
    mismatches: list[dict[str, Any]] = []
    for field in ["return_3m", "max_drawdown", "volatility"]:
        expected = float(metrics[field])
        actual = float(snapshot_row.get(field, 0.0))
        if abs(expected - actual) > tolerance:
            mismatches.append(
                {
                    "product_code": snapshot_row["product_code"],
                    "field": field,
                    "snapshot_value": round(actual, 6),
                    "nav_recomputed_value": round(expected, 6),
                    "evidence_ids": metrics["nav_evidence_ids"],
                }
            )
    return mismatches
