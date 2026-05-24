"""Sample-data loading helpers.

The demo defaults to synthetic CSV files in ``data/``. Real market-data
connectors can be enabled later through environment variables, but no local
absolute path or credential is required for the default workflow.
"""
from __future__ import annotations

import os
from pathlib import Path

from backend.app.utils.pandas_runtime import disable_optional_pandas_accelerators

disable_optional_pandas_accelerators()

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_DIR = ROOT / "data"


def get_data_dir(data_dir: Path | str | None = None) -> Path:
    if data_dir is not None:
        return Path(data_dir)
    configured = os.getenv("WEALTH_AGENT_DATA_DIR")
    return Path(configured) if configured else DEFAULT_DATA_DIR


def _read_csv(name: str, data_dir: Path | str | None = None, **kwargs) -> pd.DataFrame:
    path = get_data_dir(data_dir) / name
    if not path.exists():
        raise FileNotFoundError(f"sample data file not found: {path}")
    return pd.read_csv(path, **kwargs)


def load_nav(symbol: str, data_dir: Path | str | None = None) -> pd.DataFrame:
    df = _read_csv("sample_nav.csv", data_dir, parse_dates=["date"])
    df = df[df["symbol"].astype(str) == str(symbol)].sort_values("date")
    if df.empty:
        raise ValueError(f"no nav/price data found for symbol={symbol}")
    return df


def load_news(symbol: str, data_dir: Path | str | None = None) -> pd.DataFrame:
    df = _read_csv("sample_news.csv", data_dir, parse_dates=["date"])
    return df[df["symbol"].astype(str) == str(symbol)].sort_values("date")


def load_products(data_dir: Path | str | None = None) -> pd.DataFrame:
    return _read_csv("sample_products.csv", data_dir)


def load_fundamentals(symbol: str, data_dir: Path | str | None = None) -> pd.DataFrame:
    df = _read_csv("sample_fundamentals.csv", data_dir, parse_dates=["as_of"])
    return df[df["symbol"].astype(str) == str(symbol)].sort_values("as_of")
