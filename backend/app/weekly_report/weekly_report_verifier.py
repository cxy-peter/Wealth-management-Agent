from __future__ import annotations

import re
from typing import Any

from backend.app.utils.pandas_runtime import disable_optional_pandas_accelerators
from backend.app.weekly_report.metrics.benchmark_status import classify_benchmark_status
from backend.app.weekly_report.metrics.percentile_metrics import product_percentile
from backend.app.weekly_report.metrics.weekly_return_metrics import compare_snapshot_to_nav
from backend.app.weekly_report.parsers.weekly_snapshot_parser import load_nav_weekly, load_scale_history, load_weekly_snapshot

disable_optional_pandas_accelerators()

import pandas as pd

FORBIDDEN_PATTERNS = [
    r"建议\s*(买入|卖出|持有)",
    r"推荐\s*配置",
    r"保证收益",
    r"确定性?\s*(上涨|增长|延续)",
    r"收益稳定可期",
    r"稳赚",
]
REALTIME_OVERCLAIM_PATTERNS = [
    r"真实全市场",
    r"全市场实时",
    r"官网实时数据",
    r"已接入官网实时数据",
]


def _text_from_payload(payload: dict[str, Any]) -> str:
    parts = [str(payload.get("report_markdown", ""))]
    for key in ["summary", "conclusion", "risk_summary"]:
        if key in payload:
            parts.append(str(payload[key]))
    return "\n".join(parts)


def _forbidden_hits(text: str) -> list[str]:
    hits: list[str] = []
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, text):
            hits.append(pattern)
    return hits


def _verify_scale(snapshot: pd.DataFrame, scale_history: pd.DataFrame) -> list[dict[str, Any]]:
    mismatches: list[dict[str, Any]] = []
    if snapshot.empty or scale_history.empty:
        return mismatches
    scale_history = scale_history.copy()
    scale_history["report_date_text"] = scale_history["report_date"].dt.strftime("%Y-%m-%d")
    for _, row in snapshot.iterrows():
        code = str(row["product_code"])
        report_date = pd.Timestamp(row["report_date"])
        current = float(row["product_scale_bn"])
        product_scale = scale_history[scale_history["product_code"].astype(str) == code]
        prev_week = product_scale[product_scale["report_date_text"] == (report_date - pd.Timedelta(days=7)).strftime("%Y-%m-%d")]
        prev_month = product_scale[product_scale["report_date_text"] == (report_date - pd.Timedelta(days=28)).strftime("%Y-%m-%d")]
        prev_week_value = current if prev_week.empty else float(prev_week.iloc[-1]["product_scale_bn"])
        prev_month_value = current if prev_month.empty else float(prev_month.iloc[-1]["product_scale_bn"])
        expected_wow = round(current - prev_week_value, 4)
        expected_mom = round(current - prev_month_value, 4)
        if abs(expected_wow - float(row["scale_wow_bn"])) > 1e-4:
            mismatches.append(
                {
                    "product_code": code,
                    "field": "scale_wow_bn",
                    "snapshot_value": float(row["scale_wow_bn"]),
                    "recomputed_value": expected_wow,
                    "evidence_id": row.get("evidence_id"),
                }
            )
        if abs(expected_mom - float(row["scale_mom_bn"])) > 1e-4:
            mismatches.append(
                {
                    "product_code": code,
                    "field": "scale_mom_bn",
                    "snapshot_value": float(row["scale_mom_bn"]),
                    "recomputed_value": expected_mom,
                    "evidence_id": row.get("evidence_id"),
                }
            )
    return mismatches


def verify_weekly_report(payload: dict[str, Any], sample_size: int = 20) -> dict[str, Any]:
    report_date = payload.get("report_date")
    snapshot = load_weekly_snapshot(report_date).head(sample_size)
    scale_history = load_scale_history()
    nav = load_nav_weekly()

    failed_checks: list[str] = []
    metric_mismatches: list[dict[str, Any]] = []
    missing_evidence: list[str] = []

    scale_mismatches = _verify_scale(snapshot, scale_history)
    if scale_mismatches:
        failed_checks.append("scale_delta_consistency")
        metric_mismatches.extend(scale_mismatches[:10])

    for _, row in snapshot.iterrows():
        row_dict = row.to_dict()
        nav_mismatches = compare_snapshot_to_nav(row_dict, nav)
        if nav_mismatches:
            failed_checks.append("nav_metric_consistency")
            metric_mismatches.extend(nav_mismatches[:10])

        expected_status = classify_benchmark_status(
            float(row["since_inception_annual_return"]),
            float(row["benchmark_lower"]),
            float(row["benchmark_upper"]),
        )
        if expected_status != str(row["benchmark_status"]):
            failed_checks.append("benchmark_status_rule")
            metric_mismatches.append(
                {
                    "product_code": row["product_code"],
                    "field": "benchmark_status",
                    "snapshot_value": row["benchmark_status"],
                    "recomputed_value": expected_status,
                    "evidence_id": row.get("evidence_id"),
                }
            )

        percentile = product_percentile(row_dict, str(row["report_date"])[:10])
        if not percentile.get("evidence_id"):
            failed_checks.append("percentile_evidence")
            missing_evidence.append(str(row["product_code"]))

    text = _text_from_payload(payload)
    forbidden = _forbidden_hits(text)
    if forbidden:
        failed_checks.append("forbidden_wording")
    source_overclaim = [pattern for pattern in REALTIME_OVERCLAIM_PATTERNS if re.search(pattern, text)]
    if source_overclaim:
        failed_checks.append("source_overclaim")
    source_types = payload.get("source_types") or ["synthetic_weekly_snapshot"]
    if "synthetic_weekly_snapshot" in source_types and "分位" in text and "模拟同业池分位" not in text:
        failed_checks.append("synthetic_percentile_not_labeled")
    if payload.get("official_disclosure_adapter_status") == "failed" and re.search(r"官网|官方披露", text) and not re.search(r"样本|局部|失败|未接入", text):
        failed_checks.append("official_disclosure_overclaim")
    for record in payload.get("official_disclosure_records", []):
        if record.get("source_type") == "official_disclosure_sample" and not (record.get("source_url_or_file") or record.get("source_name")):
            failed_checks.append("official_record_missing_source")
            missing_evidence.append(str(record.get("evidence_id", "official_record")))
    if "evidence_id=" not in text and payload.get("report_markdown"):
        failed_checks.append("report_missing_evidence_id")
        missing_evidence.append("report_markdown")

    evidence_ids = payload.get("evidence_ids", [])
    if not evidence_ids:
        failed_checks.append("payload_missing_evidence")
        missing_evidence.append("evidence_ids")

    failed_checks = sorted(set(failed_checks))
    pass_flag = not failed_checks and not metric_mismatches and not forbidden and not missing_evidence
    penalty = 0.12 * len(failed_checks) + 0.04 * len(metric_mismatches) + 0.08 * len(missing_evidence)
    confidence = max(0.0, min(1.0, 1.0 - penalty))
    return {
        "pass": pass_flag,
        "failed_checks": failed_checks,
        "metric_mismatches": metric_mismatches[:25],
        "missing_evidence": missing_evidence,
        "forbidden_wording": bool(forbidden),
        "forbidden_patterns": forbidden,
        "source_overclaim": bool(source_overclaim),
        "source_overclaim_patterns": source_overclaim,
        "confidence_score": round(confidence, 4),
    }
