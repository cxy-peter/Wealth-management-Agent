from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.app.utils.pandas_runtime import disable_optional_pandas_accelerators

disable_optional_pandas_accelerators()

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
WEEKLY_DIR = ROOT / "data" / "weekly"


def _read_csv(name: str, **kwargs: Any) -> pd.DataFrame:
    path = WEEKLY_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"weekly sample file not found: {path}")
    return pd.read_csv(path, **kwargs)


def load_weekly_snapshot(report_date: str | None = None) -> pd.DataFrame:
    df = _read_csv("product_weekly_snapshot.csv", parse_dates=["report_date", "inception_date"])
    if report_date:
        df = df[df["report_date"].dt.strftime("%Y-%m-%d") == str(report_date)]
    return df.sort_values(["report_date", "product_code"])


def load_scale_history(product_code: str | None = None) -> pd.DataFrame:
    df = _read_csv("product_scale_history.csv", parse_dates=["report_date"])
    if product_code:
        df = df[df["product_code"].astype(str) == str(product_code)]
    return df.sort_values(["product_code", "report_date"])


def load_nav_weekly(product_code: str | None = None) -> pd.DataFrame:
    df = _read_csv("product_nav_weekly.csv", parse_dates=["nav_date"])
    if product_code:
        df = df[df["product_code"].astype(str) == str(product_code)]
    return df.sort_values(["product_code", "nav_date"])


def load_benchmark_status(report_date: str | None = None, product_code: str | None = None) -> pd.DataFrame:
    df = _read_csv("product_benchmark_status.csv", parse_dates=["report_date"])
    if report_date:
        df = df[df["report_date"].dt.strftime("%Y-%m-%d") == str(report_date)]
    if product_code:
        df = df[df["product_code"].astype(str) == str(product_code)]
    return df.sort_values(["report_date", "product_code"])


def list_report_dates() -> list[str]:
    df = load_weekly_snapshot()
    return sorted(df["report_date"].dt.strftime("%Y-%m-%d").unique().tolist())


def frame_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    frame = df.copy()
    for column in frame.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
        frame[column] = frame[column].dt.strftime("%Y-%m-%d")
    return frame.to_dict(orient="records")
