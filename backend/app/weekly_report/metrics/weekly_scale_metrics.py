from __future__ import annotations

from typing import Any

from backend.app.utils.pandas_runtime import disable_optional_pandas_accelerators
from backend.app.weekly_report.parsers.weekly_snapshot_parser import frame_records

disable_optional_pandas_accelerators()

import pandas as pd


def scale_kpis(snapshot: pd.DataFrame) -> dict[str, Any]:
    if snapshot.empty:
        return {
            "total_scale_bn": 0.0,
            "scale_wow_bn": 0.0,
            "scale_mom_bn": 0.0,
            "scale_drop_count": 0,
            "scale_evidence_ids": [],
        }
    return {
        "total_scale_bn": round(float(snapshot["product_scale_bn"].sum()), 4),
        "scale_wow_bn": round(float(snapshot["scale_wow_bn"].sum()), 4),
        "scale_mom_bn": round(float(snapshot["scale_mom_bn"].sum()), 4),
        "scale_drop_count": int((snapshot["scale_wow_bn"] < 0).sum()),
        "scale_evidence_ids": snapshot["evidence_id"].astype(str).head(12).tolist(),
    }


def scale_change_rank(snapshot: pd.DataFrame, limit: int = 10) -> list[dict[str, Any]]:
    if snapshot.empty:
        return []
    cols = [
        "report_date",
        "product_code",
        "product_name",
        "product_series",
        "product_type",
        "channel",
        "risk_level",
        "product_scale_bn",
        "scale_wow_bn",
        "scale_mom_bn",
        "evidence_id",
    ]
    ranked = snapshot.assign(abs_scale_wow=snapshot["scale_wow_bn"].abs()).sort_values(
        ["abs_scale_wow", "product_scale_bn"], ascending=[False, False]
    )
    return frame_records(ranked[cols].head(limit))


def channel_scale_summary(snapshot: pd.DataFrame) -> list[dict[str, Any]]:
    if snapshot.empty:
        return []
    grouped = (
        snapshot.groupby("channel", as_index=False)
        .agg(
            product_count=("product_code", "count"),
            total_scale_bn=("product_scale_bn", "sum"),
            scale_wow_bn=("scale_wow_bn", "sum"),
            scale_mom_bn=("scale_mom_bn", "sum"),
        )
        .sort_values("total_scale_bn", ascending=False)
    )
    for column in ["total_scale_bn", "scale_wow_bn", "scale_mom_bn"]:
        grouped[column] = grouped[column].round(4)
    return frame_records(grouped)
