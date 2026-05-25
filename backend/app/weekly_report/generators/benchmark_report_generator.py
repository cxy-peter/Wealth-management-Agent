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
    if not report_date:
        return dates[-1]
    requested = str(report_date)[:10]
    if requested in dates:
        return requested
    prior = [item for item in dates if item <= requested]
    return prior[-1] if prior else dates[-1]


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
    source_fields = [
        "product_scale_bn",
        "scale_wow_bn",
        "scale_mom_bn",
        "latest_nav",
        "return_3m",
        "max_drawdown",
        "volatility",
        "sharpe",
        "benchmark_status",
        "return_percentile",
        "drawdown_percentile",
    ]
    source_matrix = [
        {
            "field": field,
            "source": "product_weekly_snapshot" if field not in {"return_percentile", "drawdown_percentile"} else "peer_product_metrics",
            "source_type": row.get("source_type", "synthetic_weekly_snapshot") if field not in {"return_percentile", "drawdown_percentile"} else "synthetic_weekly_snapshot",
            "as_of_date": row.get("as_of_date", selected_date),
            "confidence": row.get("confidence_level", "medium"),
            "evidence_id": row.get("evidence_id") if field not in {"return_percentile", "drawdown_percentile"} else percentile["evidence_id"],
        }
        for field in source_fields
    ]
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
        "field_source_matrix": source_matrix,
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
    included = [
        {
            "peer_product_code": row["peer_product_code"],
            "include_reason": [
                "同产品类型",
                "同风险等级" if str(row.get("risk_level")) == str(snapshot.get("risk_level")) else "同类扩展风险等级",
                "同期限" if str(row.get("open_type")) == str(snapshot.get("open_type")) else "相邻期限或全市场补充",
                "成立满3个月",
            ],
            "evidence_id": row.get("evidence_id_x") or row.get("evidence_id"),
        }
        for row in table.to_dict(orient="records")
    ]
    rejected = []
    for _, row in merged.head(40).iterrows():
        if str(row.get("product_type")) != str(product_type):
            rejected.append(
                {
                    "peer_product_code": row.get("peer_product_code"),
                    "exclude_reason": "产品类型不一致",
                    "evidence_id": row.get("evidence_id_x") or row.get("evidence_id"),
                }
            )
        if len(rejected) >= 8:
            break
    return {
        "product_code": product_code,
        "report_date": detail["report_date"],
        "product": snapshot,
        "percentile": detail["percentile"],
        "peer_count": int(len(same_type)),
        "table": frame_records(table),
        "peer_universe_explainer": {
            "pool_rule": "同产品类型、同风险等级优先、同期限/同渠道优先，成立满3个月；样例数据不足时使用全市场同类扩展。",
            "included": included,
            "excluded": rejected,
        },
        "evidence_ids": list(dict.fromkeys(detail["evidence_ids"] + table["evidence_id_x"].astype(str).head(8).tolist())),
        "source_files": ["data/benchmark/peer_product_universe.csv", "data/benchmark/peer_product_metrics.csv"],
    }


def channel_benchmark(product_type: str | None = None, channel: str | None = None) -> dict[str, Any]:
    return channel_percentile_summary(product_type=product_type, channel=channel)


def top_peers(product_type: str | None = None, report_date: str | None = None, limit: int = 20) -> dict[str, Any]:
    selected_date = _latest_date(report_date)
    rows = load_top_peer_products(product_type=product_type, report_date=selected_date).copy()
    if not rows.empty:
        if "product_scale_bn" not in rows.columns:
            rows["product_scale_bn"] = 0.0
        rows = rows.sort_values(
            ["return_3m", "sharpe", "max_drawdown", "product_scale_bn", "peer_product_code"],
            ascending=[False, False, True, False, True],
        ).reset_index(drop=True)
        rows["global_rank"] = range(1, len(rows) + 1)
        rows = rows.head(limit)
    return {
        "report_date": selected_date,
        "product_type": product_type,
        "count": int(len(rows)),
        "table": frame_records(rows),
        "evidence_ids": rows["evidence_id"].astype(str).head(12).tolist() if not rows.empty else [],
    }
