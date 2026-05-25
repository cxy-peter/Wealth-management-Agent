from __future__ import annotations

from typing import Any


REAL_MARKET_CLAIMS = ["真实全市场", "全市场实时", "覆盖全市场", "官方实时", "已完成官网验证"]


def check_source_boundary(report_text: str, source_context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = source_context or {}
    text = report_text or ""
    failed_rules: list[str] = []
    warnings: list[str] = []
    manual_review_required = False

    source_types = set(context.get("source_types") or [])
    if context.get("synthetic_peer_universe") or "synthetic_weekly_snapshot" in source_types:
        if "真实全市场排名" in text or "真实全市场" in text:
            failed_rules.append("synthetic_data_real_market_claim")
            warnings.append("source_type=synthetic_weekly_snapshot 时禁止写真实全市场排名。")
        if context.get("percentile_from_synthetic") and "模拟同业池分位" not in text:
            failed_rules.append("missing_synthetic_percentile_disclaimer")
            warnings.append("分位数来自 synthetic peer universe，报告必须写模拟同业池分位。")

    if "manual_upload" in source_types and "基于用户上传数据" not in text:
        failed_rules.append("missing_manual_upload_disclaimer")
        warnings.append("数据来自 manual_upload，报告必须写基于用户上传数据。")

    if context.get("official_adapter_status") == "failed" and ("已完成官网验证" in text or "官方实时" in text):
        failed_rules.append("official_adapter_failed_overclaim")
        warnings.append("official adapter 失败时不得写已完成官网验证。")

    if context.get("nav_conflict"):
        manual_review_required = True
        if "人工复核" not in text and "降级" not in text:
            failed_rules.append("missing_manual_review_for_nav_conflict")
            warnings.append("外部净值字段和上传净值冲突时，报告必须降级措辞并提示人工复核。")

    for phrase in REAL_MARKET_CLAIMS:
        if phrase in text and not context.get("has_official_full_coverage", False):
            failed_rules.append("unsupported_real_data_claim")
            warnings.append(f"缺少官方覆盖证据，不应使用“{phrase}”。")
            break

    return {
        "pass": not failed_rules,
        "failed_rules": failed_rules,
        "warnings": warnings,
        "manual_review_required": manual_review_required,
    }
