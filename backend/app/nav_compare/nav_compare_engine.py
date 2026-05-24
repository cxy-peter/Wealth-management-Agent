from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def nav_metrics(nav: pd.DataFrame, value_col: str = "nav", benchmark_col: str = "benchmark_nav") -> dict[str, float]:
    if nav.empty or value_col not in nav:
        return {
            "period_return": 0.0,
            "annualized_return": 0.0,
            "annualized_volatility": 0.0,
            "max_drawdown": 0.0,
            "sharpe": 0.0,
            "calmar": 0.0,
            "benchmark_excess": 0.0,
        }
    values = nav[value_col].astype(float).to_numpy()
    returns = pd.Series(values).pct_change().dropna().to_numpy()
    period_return = values[-1] / values[0] - 1 if values[0] else 0.0
    annualized_return = (1 + period_return) ** (52 / max(len(values), 1)) - 1
    annualized_volatility = float(np.std(returns) * np.sqrt(52)) if len(returns) else 0.0
    peaks = np.maximum.accumulate(values)
    drawdowns = values / peaks - 1
    max_drawdown = float(np.min(drawdowns)) if len(drawdowns) else 0.0
    sharpe = annualized_return / annualized_volatility if annualized_volatility else 0.0
    calmar = annualized_return / abs(max_drawdown) if max_drawdown else 0.0
    benchmark_excess = period_return
    if benchmark_col in nav and not nav[benchmark_col].dropna().empty:
        benchmark = nav[benchmark_col].astype(float).to_numpy()
        benchmark_return = benchmark[-1] / benchmark[0] - 1 if benchmark[0] else 0.0
        benchmark_excess = period_return - benchmark_return
    return {
        "period_return": round(float(period_return), 6),
        "annualized_return": round(float(annualized_return), 6),
        "annualized_volatility": round(float(annualized_volatility), 6),
        "max_drawdown": round(float(max_drawdown), 6),
        "sharpe": round(float(sharpe), 6),
        "calmar": round(float(calmar), 6),
        "benchmark_excess": round(float(benchmark_excess), 6),
    }


def normalize_nav(nav: pd.DataFrame, value_col: str = "nav") -> pd.DataFrame:
    frame = nav.copy()
    if frame.empty or value_col not in frame:
        frame["normalized_nav"] = []
        return frame
    start = float(frame[value_col].iloc[0]) or 1.0
    frame["normalized_nav"] = (frame[value_col].astype(float) / start).round(6)
    return frame


def compare_nav_series(series_by_product: dict[str, pd.DataFrame]) -> dict[str, Any]:
    return {
        "products": [
            {
                "product_code": product_code,
                "metrics": nav_metrics(frame),
                "records": normalize_nav(frame).to_dict(orient="records"),
            }
            for product_code, frame in series_by_product.items()
        ]
    }
