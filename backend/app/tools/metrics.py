"""Financial metric utilities used by the research-agent MVP.

The functions are intentionally deterministic and auditable so that the final
LLM/report layer cannot silently invent numbers.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable

from backend.app.utils.pandas_runtime import disable_optional_pandas_accelerators

disable_optional_pandas_accelerators()

import numpy as np
import pandas as pd

TRADING_DAYS = 252


@dataclass(frozen=True)
class RiskMetrics:
    symbol: str
    observations: int
    start_value: float
    end_value: float
    total_return: float
    annualized_return: float
    annualized_volatility: float
    max_drawdown: float
    sharpe_ratio: float

    def to_dict(self) -> dict:
        return asdict(self)


def _as_price_series(values: Iterable[float]) -> pd.Series:
    series = pd.Series(list(values), dtype="float64").dropna()
    if series.empty:
        raise ValueError("price/nav series is empty")
    if (series <= 0).any():
        raise ValueError("price/nav series must contain positive values only")
    return series.reset_index(drop=True)


def pct_returns(values: Iterable[float]) -> pd.Series:
    series = _as_price_series(values)
    returns = series.pct_change().dropna()
    return returns


def max_drawdown(values: Iterable[float]) -> float:
    series = _as_price_series(values)
    running_max = series.cummax()
    drawdown = series / running_max - 1.0
    return float(drawdown.min())


def annualized_return(values: Iterable[float], trading_days: int = TRADING_DAYS) -> float:
    series = _as_price_series(values)
    periods = len(series) - 1
    if periods <= 0:
        return 0.0
    return float((series.iloc[-1] / series.iloc[0]) ** (trading_days / periods) - 1)


def annualized_volatility(values: Iterable[float], trading_days: int = TRADING_DAYS) -> float:
    returns = pct_returns(values)
    if returns.empty:
        return 0.0
    return float(returns.std(ddof=1) * np.sqrt(trading_days))


def sharpe_ratio(values: Iterable[float], risk_free_rate: float = 0.02) -> float:
    ann_ret = annualized_return(values)
    ann_vol = annualized_volatility(values)
    if ann_vol == 0:
        return 0.0
    return float((ann_ret - risk_free_rate) / ann_vol)


def compute_metrics(df: pd.DataFrame, symbol: str, value_col: str = "close") -> RiskMetrics:
    if value_col not in df.columns:
        raise ValueError(f"missing value column: {value_col}")
    values = _as_price_series(df[value_col])
    return RiskMetrics(
        symbol=symbol,
        observations=int(len(values)),
        start_value=float(values.iloc[0]),
        end_value=float(values.iloc[-1]),
        total_return=float(values.iloc[-1] / values.iloc[0] - 1),
        annualized_return=annualized_return(values),
        annualized_volatility=annualized_volatility(values),
        max_drawdown=max_drawdown(values),
        sharpe_ratio=sharpe_ratio(values),
    )


def moving_average(values: Iterable[float], window: int) -> float:
    series = _as_price_series(values)
    if len(series) < window:
        return float(series.mean())
    return float(series.tail(window).mean())


def momentum(values: Iterable[float], periods: int) -> float:
    series = _as_price_series(values)
    if len(series) <= periods:
        return float(series.iloc[-1] / series.iloc[0] - 1)
    return float(series.iloc[-1] / series.iloc[-periods - 1] - 1)


def technical_snapshot(df: pd.DataFrame, symbol: str, value_col: str = "close") -> dict:
    if value_col not in df.columns:
        raise ValueError(f"missing value column: {value_col}")
    values = _as_price_series(df[value_col])
    latest = float(values.iloc[-1])
    ma5 = moving_average(values, 5)
    ma20 = moving_average(values, 20)
    mom5 = momentum(values, 5)
    mom20 = momentum(values, 20)
    ann_vol = annualized_volatility(values)
    drawdown = max_drawdown(values)

    if latest >= ma5 >= ma20 and mom5 >= 0:
        trend_label = "样本内短期趋势偏强"
    elif latest <= ma5 <= ma20 and mom5 < 0:
        trend_label = "样本内短期趋势承压"
    else:
        trend_label = "样本内趋势分歧"

    if ann_vol >= 0.3 or drawdown <= -0.08:
        risk_regime = "高波动观察"
    elif ann_vol >= 0.18 or drawdown <= -0.04:
        risk_regime = "中等波动观察"
    else:
        risk_regime = "低波动观察"

    return {
        "symbol": symbol,
        "latest_close": latest,
        "ma5": ma5,
        "ma20": ma20,
        "momentum_5d": mom5,
        "momentum_20d": mom20,
        "annualized_volatility": ann_vol,
        "max_drawdown": drawdown,
        "trend_label": trend_label,
        "risk_regime": risk_regime,
    }


def format_pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def format_float(x: float) -> str:
    return f"{x:.3f}"
