from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.app.utils.pandas_runtime import disable_optional_pandas_accelerators
from backend.app.weekly_report.parsers.weekly_snapshot_parser import frame_records

disable_optional_pandas_accelerators()

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
BENCHMARK_DIR = ROOT / "data" / "benchmark"


def _read_csv(name: str, **kwargs: Any) -> pd.DataFrame:
    path = BENCHMARK_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"benchmark sample file not found: {path}")
    return pd.read_csv(path, **kwargs)


def load_peer_universe() -> pd.DataFrame:
    return _read_csv("peer_product_universe.csv")


def load_peer_metrics(report_date: str | None = None) -> pd.DataFrame:
    df = _read_csv("peer_product_metrics.csv", parse_dates=["report_date"])
    if report_date:
        df = df[df["report_date"].dt.strftime("%Y-%m-%d") == str(report_date)]
    return df


def load_channel_peers(product_type: str | None = None, channel: str | None = None) -> pd.DataFrame:
    df = _read_csv("channel_peer_universe.csv")
    if product_type:
        df = df[df["product_type"].astype(str) == str(product_type)]
    if channel:
        df = df[df["channel"].astype(str) == str(channel)]
    return df


def load_top_peer_products(product_type: str | None = None, report_date: str | None = None) -> pd.DataFrame:
    df = _read_csv("top_peer_products.csv", parse_dates=["report_date"])
    if report_date:
        df = df[df["report_date"].dt.strftime("%Y-%m-%d") == str(report_date)]
    if product_type:
        df = df[df["product_type"].astype(str) == str(product_type)]
    return df.sort_values(["product_type", "rank"])


def _percentile(values: list[float], value: float, higher_is_better: bool = True) -> float:
    if not values:
        return 0.0
    if higher_is_better:
        return sum(1 for item in values if item <= value) / len(values)
    return sum(1 for item in values if item >= value) / len(values)


def product_percentile(snapshot_row: dict[str, Any], report_date: str | None = None) -> dict[str, Any]:
    product_type = str(snapshot_row["product_type"])
    peer_metrics = load_peer_metrics(report_date)
    peers = load_peer_universe()
    merged = peer_metrics.merge(peers[["peer_product_code", "product_type", "channel"]], on="peer_product_code", how="left")
    same_type = merged[merged["product_type"].astype(str) == product_type]
    if same_type.empty:
        return {
            "product_code": snapshot_row["product_code"],
            "return_percentile": 0.0,
            "drawdown_percentile": 0.0,
            "sharpe_percentile": 0.0,
            "peer_count": 0,
            "evidence_id": f"ev_percentile_missing_{snapshot_row['product_code']}",
            "source": "peer_product_metrics",
        }
    returns = same_type["return_3m"].astype(float).tolist()
    drawdowns = same_type["max_drawdown"].astype(float).tolist()
    sharpes = same_type["sharpe"].astype(float).tolist()
    return {
        "product_code": snapshot_row["product_code"],
        "product_type": product_type,
        "return_percentile": round(_percentile(returns, float(snapshot_row["return_3m"]), True), 4),
        "drawdown_percentile": round(_percentile(drawdowns, float(snapshot_row["max_drawdown"]), True), 4),
        "sharpe_percentile": round(_percentile(sharpes, float(snapshot_row["sharpe"]), True), 4),
        "peer_count": int(len(same_type)),
        "evidence_id": f"ev_percentile_{snapshot_row['product_code']}_{str(snapshot_row.get('report_date', report_date)).replace('-', '')[:8]}",
        "source": "peer_product_metrics",
    }


def attach_percentiles(snapshot: pd.DataFrame, report_date: str | None = None) -> pd.DataFrame:
    if snapshot.empty:
        return snapshot.copy()
    rows = [product_percentile(row.to_dict(), report_date) for _, row in snapshot.iterrows()]
    percentiles = pd.DataFrame(rows)
    return snapshot.merge(percentiles, on="product_code", how="left", suffixes=("", "_percentile_calc"))


def percentile_decliners(snapshot: pd.DataFrame, limit: int = 10) -> list[dict[str, Any]]:
    if snapshot.empty:
        return []
    enriched = attach_percentiles(snapshot, str(snapshot.iloc[0]["report_date"])[:10])
    focus = enriched[(enriched["return_percentile"] <= 0.35) | (enriched["drawdown_percentile"] <= 0.35)].copy()
    if focus.empty:
        focus = enriched.nsmallest(limit, "return_percentile").copy()
    focus["attention_score"] = (1 - focus["return_percentile"].astype(float)) + (1 - focus["drawdown_percentile"].astype(float))
    cols = [
        "report_date",
        "product_code",
        "product_name",
        "product_type",
        "channel",
        "risk_level",
        "return_3m",
        "max_drawdown",
        "return_percentile",
        "drawdown_percentile",
        "sharpe_percentile",
        "peer_count",
        "evidence_id",
    ]
    return frame_records(focus.sort_values("attention_score", ascending=False)[cols].head(limit))


def channel_percentile_summary(product_type: str | None = None, channel: str | None = None) -> dict[str, Any]:
    df = load_channel_peers(product_type=product_type, channel=channel)
    if df.empty:
        return {
            "product_type": product_type,
            "channel": channel,
            "peer_count": 0,
            "channels": [],
            "table": [],
            "evidence_ids": [],
        }
    grouped = (
        df.groupby(["channel", "product_type"], as_index=False)
        .agg(
            peer_count=("peer_product_code", "count"),
            avg_return_3m=("return_3m", "mean"),
            total_scale_bn=("scale_bn", "sum"),
        )
        .sort_values(["avg_return_3m", "total_scale_bn"], ascending=[False, False])
    )
    grouped["avg_return_3m"] = grouped["avg_return_3m"].round(6)
    grouped["total_scale_bn"] = grouped["total_scale_bn"].round(4)
    return {
        "product_type": product_type,
        "channel": channel,
        "peer_count": int(len(df)),
        "channels": sorted(df["channel"].astype(str).unique().tolist()),
        "table": frame_records(grouped.head(30)),
        "evidence_ids": df["evidence_id"].astype(str).head(12).tolist(),
    }
