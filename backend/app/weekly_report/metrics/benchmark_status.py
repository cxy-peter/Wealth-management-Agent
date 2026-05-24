from __future__ import annotations

from typing import Any

from backend.app.utils.pandas_runtime import disable_optional_pandas_accelerators

disable_optional_pandas_accelerators()

import pandas as pd


def classify_benchmark_status(actual_return: float, lower: float, upper: float) -> str:
    if actual_return < lower:
        return "below_lower"
    if actual_return > upper:
        return "above_upper"
    return "in_range"


def benchmark_summary(snapshot: pd.DataFrame) -> dict[str, Any]:
    if snapshot.empty:
        return {
            "benchmark_pass_rate": 0.0,
            "benchmark_failed_count": 0,
            "benchmark_above_count": 0,
            "benchmark_in_range_count": 0,
            "benchmark_evidence_ids": [],
        }
    in_range = int((snapshot["benchmark_status"] == "in_range").sum())
    below = int((snapshot["benchmark_status"] == "below_lower").sum())
    above = int((snapshot["benchmark_status"] == "above_upper").sum())
    return {
        "benchmark_pass_rate": round(in_range / max(len(snapshot), 1), 4),
        "benchmark_failed_count": below,
        "benchmark_above_count": above,
        "benchmark_in_range_count": in_range,
        "benchmark_evidence_ids": snapshot["evidence_id"].astype(str).head(12).tolist(),
    }


def benchmark_failed_products(snapshot: pd.DataFrame, limit: int = 10) -> list[dict[str, Any]]:
    if snapshot.empty:
        return []
    cols = [
        "report_date",
        "product_code",
        "product_name",
        "product_type",
        "channel",
        "risk_level",
        "since_inception_annual_return",
        "benchmark_lower",
        "benchmark_upper",
        "benchmark_status",
        "evidence_id",
    ]
    failed = snapshot[snapshot["benchmark_status"] == "below_lower"].copy()
    if failed.empty:
        return []
    failed["gap_to_lower"] = failed["since_inception_annual_return"] - failed["benchmark_lower"]
    failed = failed.sort_values(["gap_to_lower", "product_scale_bn"], ascending=[True, False])
    records = failed[cols + ["gap_to_lower"]].head(limit).copy()
    records["gap_to_lower"] = records["gap_to_lower"].round(6)
    for column in records.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
        records[column] = records[column].dt.strftime("%Y-%m-%d")
    return records.to_dict(orient="records")
