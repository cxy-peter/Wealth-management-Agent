from __future__ import annotations

import json
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
        raise FileNotFoundError(f"weekly market sample file not found: {path}")
    return pd.read_csv(path, **kwargs)


def load_market_issuance(report_date: str | None = None) -> pd.DataFrame:
    df = _read_csv("market_issuance_weekly.csv", parse_dates=["report_date"])
    if report_date:
        df = df[df["report_date"].dt.strftime("%Y-%m-%d") == str(report_date)]
    return df.sort_values("report_date")


def load_market_new_products(report_date: str | None = None) -> pd.DataFrame:
    df = _read_csv("market_new_product_detail.csv", parse_dates=["report_date"])
    if report_date:
        df = df[df["report_date"].dt.strftime("%Y-%m-%d") == str(report_date)]
    return df.sort_values(["report_date", "new_product_code"])


def market_summary(report_date: str) -> dict[str, Any]:
    rows = load_market_issuance(report_date)
    if rows.empty:
        return {
            "report_date": report_date,
            "new_product_count": 0,
            "by_investment_nature": {},
            "by_duration": {},
            "benchmark_lower_avg": 0.0,
            "benchmark_upper_avg": 0.0,
            "evidence_id": "ev_market_missing",
        }
    row = rows.iloc[-1]
    return {
        "report_date": report_date,
        "new_product_count": int(row["new_product_count"]),
        "by_investment_nature": json.loads(row["by_investment_nature_json"]),
        "by_duration": json.loads(row["by_duration_json"]),
        "benchmark_lower_avg": float(row["benchmark_lower_avg"]),
        "benchmark_upper_avg": float(row["benchmark_upper_avg"]),
        "evidence_id": str(row["evidence_id"]),
    }
