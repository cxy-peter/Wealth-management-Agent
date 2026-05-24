from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.dpo.eval_dpo_agent_alignment import RESULT_PATH as DPO_EVAL_PATH, run_eval as run_dpo_eval  # noqa: E402
from backend.app.weekly_report.generators.benchmark_report_generator import (  # noqa: E402
    channel_benchmark,
    peer_benchmark,
    top_peers,
    weekly_product_detail,
)
from backend.app.weekly_report.generators.weekly_report_generator import weekly_products, weekly_summary  # noqa: E402

PUBLIC_DIR = ROOT / "frontend" / "public" / "demo-data"
DEMO_DATES = ["2025-01-31", "2025-02-05", "2025-03-19", "2025-04-04"]
LATEST_DATE = "2025-04-04"
DEFAULT_PRODUCT = "WP0031"

ISSUERS = ["信银理财", "交银理财", "招银理财", "工银理财", "建信理财", "农银理财", "中银理财", "兴银理财"]
SERIES = ["稳健添利", "悦享固收", "多元配置", "现金优选", "全球配置", "封闭精选", "持有期增强", "均衡优选"]
CLASS_SUFFIX = ["A", "B", "C", "私银款", "机构款", "直销款"]


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def _date_key(date: str) -> str:
    return str(date)[:10]


def _filename_date(date: str) -> str:
    return _date_key(date)


def _product_index(code: str) -> int:
    digits = "".join(ch for ch in str(code) if ch.isdigit())
    return max(1, int(digits or "1"))


def _natural_name(row: dict[str, Any], code_key: str = "product_code") -> str:
    code = str(row.get(code_key) or row.get("peer_product_code") or DEFAULT_PRODUCT)
    idx = _product_index(code)
    series = SERIES[idx % len(SERIES)]
    product_type = str(row.get("product_type", "固收增强"))
    open_type = str(row.get("open_type") or row.get("duration_bucket") or row.get("holding_period_days") or "90天")
    if open_type.isdigit():
        open_type = f"{open_type}天"
    if product_type in {"现金管理", "日开型"}:
        term = "日开"
    elif "封闭" in product_type and "封闭" not in open_type:
        term = "1年封闭"
    else:
        term = open_type.replace("天", "天持有期")
    suffix = CLASS_SUFFIX[idx % len(CLASS_SUFFIX)]
    return f"{series}{term}{suffix}"


def _issuer(code: str) -> str:
    return ISSUERS[_product_index(code) % len(ISSUERS)]


def _annualized(period_return: Any, periods_per_year: int) -> float:
    value = float(period_return or 0)
    return round((1 + value) ** periods_per_year - 1, 6)


def _enrich_product(row: dict[str, Any], code_key: str = "product_code") -> dict[str, Any]:
    row = dict(row)
    code = str(row.get(code_key) or row.get("peer_product_code") or DEFAULT_PRODUCT)
    risk_num = int(str(row.get("risk_level", "R2")).replace("R", "") or 2)
    lower = float(row.get("benchmark_lower", 0.02) or 0.02)
    upper = float(row.get("benchmark_upper", 0.04) or 0.04)
    row["product_name"] = _natural_name(row, code_key)
    if code_key == "peer_product_code":
        row["peer_product_name"] = row["product_name"]
    row["issuer_name"] = _issuer(code)
    row["issuer_type"] = row.get("issuer_type") or "银行理财子公司"
    row["benchmark"] = row.get("benchmark") or f"{lower * 100:.2f}%-{upper * 100:.2f}%"
    row["fee_rate"] = round(float(row.get("fee_rate", 0.0015 + risk_num * 0.0004)), 4)
    row["total_fee_rate"] = row["fee_rate"]
    row["inception_date"] = str(row.get("inception_date") or "2023-01-06")[:10]
    row["latest_nav"] = round(float(row.get("latest_nav", 1 + float(row.get("return_3m", 0) or 0))), 6)
    row["since_inception_annual_return"] = round(
        float(row.get("since_inception_annual_return", float(row.get("return_3m", 0) or 0) * 4)),
        6,
    )
    row["return_3m_annualized"] = _annualized(row.get("return_3m", 0), 4)
    row["return_1m_annualized"] = _annualized(row.get("return_1m", float(row.get("return_3m", 0) or 0) / 3), 12)
    row["source_type"] = row.get("source_type") or "synthetic_weekly_snapshot"
    row["confidence_level"] = row.get("confidence_level") or "medium"
    return row


def _transform_product_rows(rows: list[dict[str, Any]], code_key: str = "product_code") -> list[dict[str, Any]]:
    return [_enrich_product(row, code_key=code_key) for row in rows]


def _apply_name_map(rows: list[dict[str, Any]], name_map: dict[str, str]) -> list[dict[str, Any]]:
    next_rows = []
    for row in rows:
        row = dict(row)
        code = row.get("product_code")
        if code in name_map:
            row["product_name"] = name_map[code]
        row["source_type"] = row.get("source_type") or "synthetic_weekly_snapshot"
        next_rows.append(row)
    return next_rows


def _transform_summary(summary: dict[str, Any], name_map: dict[str, str], requested_date: str) -> dict[str, Any]:
    payload = dict(summary)
    for table_key in ["scale_change_rank", "benchmark_failed_products", "percentile_decline_products", "attention_top10", "weekly_diff"]:
        payload[table_key] = _apply_name_map(payload.get(table_key, []), name_map)
    payload["report_date"] = _date_key(requested_date)
    payload["source_type"] = "synthetic_weekly_snapshot"
    payload["demo_disclaimer"] = "演示数据为 synthetic_weekly_snapshot，不代表真实全市场产品排名。"
    return payload


def _with_requested_date(payload: dict[str, Any], requested_date: str) -> dict[str, Any]:
    payload = dict(payload)
    payload["report_date"] = _date_key(requested_date)
    payload["source_type"] = "synthetic_weekly_snapshot"
    return payload


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    return values[len(values) // 2]


def _bucket_histogram(rows: list[dict[str, Any]], field: str = "return_3m") -> list[dict[str, Any]]:
    values = [float(row.get(field, 0) or 0) for row in rows]
    if not values:
        return []
    floor = min(values)
    ceiling = max(values)
    width = max((ceiling - floor) / 8, 0.0001)
    buckets = [{"from": round(floor + i * width, 6), "to": round(floor + (i + 1) * width, 6), "count": 0} for i in range(8)]
    for value in values:
        idx = min(7, max(0, int((value - floor) / width)))
        buckets[idx]["count"] += 1
    return buckets


def _peer_payload(product_code: str, report_date: str, name_map: dict[str, str]) -> dict[str, Any]:
    payload = peer_benchmark(product_code, report_date, limit=16)
    product = _enrich_product(payload.get("product", {}))
    product["product_name"] = name_map.get(product_code, product["product_name"])
    rows = _transform_product_rows(payload.get("table", []), code_key="peer_product_code")
    returns = sorted(float(row.get("return_3m", 0) or 0) for row in rows)
    drawdowns = sorted(float(row.get("max_drawdown", 0) or 0) for row in rows)
    sharpes = sorted(float(row.get("sharpe", 0) or 0) for row in rows)
    top_rows = sorted(rows, key=lambda row: float(row.get("return_3m", 0) or 0), reverse=True)[:10]
    bottom_rows = sorted(rows, key=lambda row: float(row.get("return_3m", 0) or 0))[:10]
    return {
        **payload,
        "report_date": _date_key(report_date),
        "product": product,
        "table": rows,
        "market_percentile_summary": {
            "pool_conditions": ["同产品类型", "同风险等级优先", "同期限/同渠道优先", "成立满3个月", "样本不足时使用模拟同业池扩展"],
            "sample_count": payload.get("peer_count", len(rows)),
            "source_type": "synthetic_weekly_snapshot",
            "indicators": [
                {
                    "metric": "近3个月收益",
                    "market_p50": round(_median(returns), 6),
                    "product_value": product.get("return_3m"),
                    "product_percentile": payload.get("percentile", {}).get("return_percentile"),
                },
                {
                    "metric": "最大回撤",
                    "market_p50": round(_median(drawdowns), 6),
                    "product_value": product.get("max_drawdown"),
                    "product_percentile": payload.get("percentile", {}).get("drawdown_percentile"),
                },
                {
                    "metric": "Sharpe",
                    "market_p50": round(_median(sharpes), 6),
                    "product_value": product.get("sharpe"),
                    "product_percentile": payload.get("percentile", {}).get("sharpe_percentile"),
                },
            ],
            "return_histogram": _bucket_histogram(rows, "return_3m"),
            "top_10": top_rows,
            "bottom_10": bottom_rows,
        },
    }


def _write(filename: str, payload: Any) -> None:
    (PUBLIC_DIR / filename).write_text(json.dumps(_jsonable(payload), ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    products_by_date: dict[str, dict[str, Any]] = {}
    summary_by_date: dict[str, dict[str, Any]] = {}

    for requested_date in DEMO_DATES:
        products_payload = weekly_products(requested_date)
        product_rows = _transform_product_rows(products_payload["products"])
        name_map = {row["product_code"]: row["product_name"] for row in product_rows}
        products_payload = _with_requested_date(products_payload, requested_date)
        products_payload["products"] = product_rows
        products_payload["source_type"] = "synthetic_weekly_snapshot"
        summary_payload = _transform_summary(weekly_summary(requested_date), name_map, requested_date)
        products_by_date[requested_date] = products_payload
        summary_by_date[requested_date] = summary_payload
        date_part = _filename_date(requested_date)
        _write(f"weekly_summary_{date_part}.json", summary_payload)
        _write(f"weekly_products_{date_part}.json", products_payload)

    latest_products = products_by_date[LATEST_DATE]
    latest_summary = summary_by_date[LATEST_DATE]
    latest_name_map = {row["product_code"]: row["product_name"] for row in latest_products["products"]}

    details: dict[str, Any] = {}
    peers: dict[str, Any] = {}
    for row in latest_products["products"]:
        code = row["product_code"]
        detail = weekly_product_detail(code, LATEST_DATE)
        if detail:
            detail = dict(detail)
            detail["snapshot"] = _enrich_product(detail.get("snapshot", {}))
            detail["snapshot"]["product_name"] = latest_name_map.get(code, detail["snapshot"]["product_name"])
            details[code] = detail
            _write(f"product_detail_{code}_{LATEST_DATE}.json", detail)
        peer_payload = _peer_payload(code, LATEST_DATE, latest_name_map)
        peers[code] = peer_payload
        _write(f"peer_summary_{code}_{LATEST_DATE}.json", peer_payload)

    channel_payload = channel_benchmark()
    channel_rows = []
    for index, row in enumerate(channel_payload.get("table", []), 1):
        row = dict(row)
        row["channel_rank"] = index
        row["product_channel_percentile"] = round(max(0.05, 1 - index / max(len(channel_payload.get("table", [])), 1)), 4)
        channel_rows.append(row)
    channel_payload["table"] = channel_rows
    channel_payload["source_type"] = "synthetic_weekly_snapshot"

    top_payload = top_peers(report_date=LATEST_DATE, limit=24)
    top_rows = []
    for row in top_payload.get("table", []):
        row = _enrich_product(row, code_key="peer_product_code")
        row["selection_reason"] = row.get("tracking_reason") or "同类收益分位和风险调整指标靠前，用于周报跟踪样例。"
        top_rows.append(row)
    top_payload["table"] = top_rows
    top_payload["source_type"] = "synthetic_weekly_snapshot"

    if not DPO_EVAL_PATH.exists():
        run_dpo_eval()
    dpo_payload = json.loads(DPO_EVAL_PATH.read_text(encoding="utf-8"))

    _write("weekly_dates.json", {"dates": DEMO_DATES, "latest": LATEST_DATE, "source_type": "synthetic_weekly_snapshot"})
    _write("weekly_summary.json", latest_summary)
    _write("weekly_products.json", latest_products)
    _write(
        "product_details.json",
        {"default_product_code": DEFAULT_PRODUCT, "by_product": {DEFAULT_PRODUCT: details.get(DEFAULT_PRODUCT)}, "source_type": "synthetic_weekly_snapshot"},
    )
    _write(
        "peer_benchmark.json",
        {"default_product_code": DEFAULT_PRODUCT, "by_product": {DEFAULT_PRODUCT: peers.get(DEFAULT_PRODUCT)}, "source_type": "synthetic_weekly_snapshot"},
    )
    _write("channel_benchmark.json", channel_payload)
    _write("top_peers.json", top_payload)
    _write("dpo_eval.json", dpo_payload)

    print(
        json.dumps(
            {
                "output_dir": str(PUBLIC_DIR),
                "dates": DEMO_DATES,
                "product_count": len(latest_products["products"]),
                "files": sorted(path.name for path in PUBLIC_DIR.glob("*.json")),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
