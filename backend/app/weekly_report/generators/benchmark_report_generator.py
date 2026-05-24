from __future__ import annotations

from typing import Any

from backend.app.weekly_report.metrics.percentile_metrics import (
    channel_percentile_summary,
    load_peer_metrics,
    load_peer_universe,
    load_top_peer_products,
    product_percentile,
)
from backend.app.weekly_report.parsers.weekly_snapshot_parser import frame_records, list_report_dates, load_nav_weekly, load_weekly_snapshot


def _latest_date(report_date: str | None = None) -> str:
    dates = list_report_dates()
    if not dates:
        raise FileNotFoundError("weekly snapshot has no report dates")
    return report_date or dates[-1]


def weekly_product_detail(product_code: str, report_date: str | None = None) -> dict[str, Any] | None:
    selected_date = _latest_date(report_date)
    snapshot = load_weekly_snapshot(selected_date)
    rows = snapshot[snapshot["product_code"].astype(str) == str(product_code)]
    if rows.empty:
        all_rows = load_weekly_snapshot()
        rows = all_rows[all_rows["product_code"].astype(str) == str(product_code)]
        if rows.empty:
            return None
        rows = rows.sort_values("report_date").tail(1)
        selected_date = str(rows.iloc[0]["report_date"])[:10]
    row = rows.iloc[0].to_dict()
    nav = load_nav_weekly(product_code)
    nav_to_date = nav[nav["nav_date"] <= rows.iloc[0]["report_date"]].tail(58)
    percentile = product_percentile(row, selected_date)
    return {
        "report_date": selected_date,
        "snapshot": frame_records(rows)[0],
        "nav": frame_records(nav_to_date),
        "percentile": percentile,
        "risk_events": [
            {
                "event_date": selected_date,
                "event_type": "benchmark_status",
                "event_summary": f"benchmark_status={row['benchmark_status']}; return_percentile={percentile['return_percentile']}",
                "evidence_id": percentile["evidence_id"],
            }
        ],
        "evidence_ids": [row.get("evidence_id"), percentile["evidence_id"]],
    }


def peer_benchmark(product_code: str, report_date: str | None = None, limit: int = 12) -> dict[str, Any]:
    detail = weekly_product_detail(product_code, report_date)
    if detail is None:
        return {"product_code": product_code, "peer_count": 0, "table": [], "evidence_ids": []}
    snapshot = detail["snapshot"]
    product_type = snapshot["product_type"]
    peers = load_peer_universe()
    metrics = load_peer_metrics(detail["report_date"])
    merged = metrics.merge(peers, on="peer_product_code", how="left")
    same_type = merged[merged["product_type"].astype(str) == str(product_type)].copy()
    if same_type.empty:
        return {"product_code": product_code, "peer_count": 0, "table": [], "evidence_ids": detail["evidence_ids"]}
    same_type["return_gap_vs_product"] = same_type["return_3m"].astype(float) - float(snapshot["return_3m"])
    same_type["drawdown_gap_vs_product"] = same_type["max_drawdown"].astype(float) - float(snapshot["max_drawdown"])
    table = same_type.sort_values(["return_percentile", "sharpe"], ascending=[False, False]).head(limit)
    return {
        "product_code": product_code,
        "report_date": detail["report_date"],
        "product": snapshot,
        "percentile": detail["percentile"],
        "peer_count": int(len(same_type)),
        "table": frame_records(table),
        "evidence_ids": list(dict.fromkeys(detail["evidence_ids"] + table["evidence_id_x"].astype(str).head(8).tolist())),
        "source_files": ["data/benchmark/peer_product_universe.csv", "data/benchmark/peer_product_metrics.csv"],
    }


def channel_benchmark(product_type: str | None = None, channel: str | None = None) -> dict[str, Any]:
    return channel_percentile_summary(product_type=product_type, channel=channel)


def top_peers(product_type: str | None = None, report_date: str | None = None, limit: int = 20) -> dict[str, Any]:
    selected_date = _latest_date(report_date)
    rows = load_top_peer_products(product_type=product_type, report_date=selected_date).head(limit)
    return {
        "report_date": selected_date,
        "product_type": product_type,
        "count": int(len(rows)),
        "table": frame_records(rows),
        "evidence_ids": rows["evidence_id"].astype(str).head(12).tolist() if not rows.empty else [],
    }
