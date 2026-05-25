from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.app.utils.pandas_runtime import disable_optional_pandas_accelerators

disable_optional_pandas_accelerators()

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
REFERENCE_PATH = ROOT / "data" / "reference" / "reference_rates.csv"


def load_reference_rates(as_of_date: str | None = None) -> pd.DataFrame:
    if not REFERENCE_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(REFERENCE_PATH)
    if as_of_date and "as_of_date" in df.columns:
        df = df[df["as_of_date"].astype(str) <= str(as_of_date)]
        if not df.empty:
            latest = sorted(df["as_of_date"].astype(str).unique())[-1]
            df = df[df["as_of_date"].astype(str) == latest]
    return df


def _closest_rate(rates: pd.DataFrame, tenor_days: int | float | None, rate_type: str | None = None) -> dict[str, Any] | None:
    if rates.empty:
        return None
    frame = rates.copy()
    if rate_type:
        typed = frame[frame["rate_type"].astype(str) == str(rate_type)]
        if not typed.empty:
            frame = typed
    target = float(tenor_days or 90)
    frame["_distance"] = (frame["tenor_days"].astype(float) - target).abs()
    row = frame.sort_values(["_distance", "rate_id"]).iloc[0].drop(labels=["_distance"]).to_dict()
    return row


def compare_product_to_reference(product: dict[str, Any], as_of_date: str | None = None) -> dict[str, Any]:
    rates = load_reference_rates(as_of_date or product.get("report_date") or product.get("as_of_date"))
    product_return = float(product.get("return_3m") or product.get("since_inception_annual_return") or 0)
    annualized_product_return = product_return * 4 if abs(product_return) < 0.4 else product_return
    tenor = product.get("holding_period_days") or product.get("duration_days") or 90
    rows = []
    for rate_type in ["deposit", "us_treasury", "gov_bond", "ncd"]:
        rate = _closest_rate(rates, tenor, rate_type)
        if not rate:
            continue
        rows.append(
            {
                "rate_id": rate["rate_id"],
                "rate_type": rate["rate_type"],
                "tenor_label": rate["tenor_label"],
                "annual_yield": float(rate["annual_yield"]),
                "product_annualized_return": round(annualized_product_return, 6),
                "product_minus_reference": round(annualized_product_return - float(rate["annual_yield"]), 6),
                "benchmark_lower_minus_reference": round(float(product.get("benchmark_lower") or 0) - float(rate["annual_yield"]), 6),
                "benchmark_upper_minus_reference": round(float(product.get("benchmark_upper") or 0) - float(rate["annual_yield"]), 6),
                "benchmark_excess": round(annualized_product_return - float(product.get("benchmark_lower") or 0), 6),
                "source_type": rate.get("source_type", "synthetic_reference_rates"),
                "evidence_id": rate.get("evidence_id")
            }
        )
    return {
        "product_code": product.get("product_code"),
        "as_of_date": as_of_date or product.get("report_date") or product.get("as_of_date"),
        "source_boundary": "reference rates are synthetic_reference_rates or manual_upload unless an explicit adapter supplies source metadata",
        "comparisons": rows,
        "evidence_ids": [row["evidence_id"] for row in rows if row.get("evidence_id")]
    }


def compare_series_to_reference(series_row: dict[str, Any], as_of_date: str | None = None) -> dict[str, Any]:
    rates = load_reference_rates(as_of_date)
    rate = _closest_rate(rates, 90, "deposit")
    reference = float(rate["annual_yield"]) if rate else 0.0
    series_return = float(series_row.get("aum_weighted_return_3m") or 0) * 4
    return {
        "series_id": series_row.get("series_id"),
        "series_name": series_row.get("series_name"),
        "series_annualized_return": round(series_return, 6),
        "reference_rate_id": rate.get("rate_id") if rate else None,
        "reference_annual_yield": reference,
        "series_minus_reference": round(series_return - reference, 6),
        "source_type": rate.get("source_type", "synthetic_reference_rates") if rate else "missing_reference_rate",
        "evidence_id": rate.get("evidence_id") if rate else None
    }

