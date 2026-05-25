from __future__ import annotations

import re
from typing import Any

RULE_VERSION = "product_series_rules.v1"

SERIES_KEYWORDS = [
    ("cash", "现金优选", ["现金", "日开", "现金管理"]),
    ("stable_income", "稳健添利", ["稳健", "添利", "纯固收"]),
    ("enhanced_income", "持有期增强", ["增强", "固收增强", "持有期"]),
    ("balanced", "多元配置", ["多元", "配置", "多资产", "混合"]),
    ("global", "全球配置", ["全球", "QDII", "海外"]),
    ("closed", "封闭精选", ["封闭", "封闭式"]),
    ("private", "悦享固收", ["悦享", "私银"])
]


def normalize_series_id(name: str) -> str:
    text = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", str(name).strip().lower())
    return text.strip("_") or "unclassified"


def classify_by_rules(row: dict[str, Any]) -> dict[str, Any]:
    product_name = str(row.get("product_name") or "")
    product_type = str(row.get("product_type") or "")
    open_type = str(row.get("open_type") or "")
    channel = str(row.get("channel") or "")
    risk_level = str(row.get("risk_level") or "")
    text = f"{product_name} {product_type} {open_type} {channel}"

    best = None
    best_hits: list[str] = []
    for series_id, series_name, keywords in SERIES_KEYWORDS:
        hits = [keyword for keyword in keywords if keyword and keyword in text]
        if len(hits) > len(best_hits):
            best = (series_id, series_name)
            best_hits = hits

    if best is None:
        if product_type:
            suggested_series_name = product_type
            suggested_series_id = normalize_series_id(product_type)
            confidence = 0.58
            reason = f"fallback_to_product_type:{product_type}"
        else:
            suggested_series_name = "未归类"
            suggested_series_id = "unclassified"
            confidence = 0.25
            reason = "missing_product_type_and_keyword"
    else:
        suggested_series_id, suggested_series_name = best
        confidence = min(0.96, 0.62 + 0.12 * len(best_hits))
        reason = "keyword_match:" + ",".join(best_hits)

    if risk_level in {"R4", "R5"} and suggested_series_id in {"cash", "stable_income"}:
        confidence = min(confidence, 0.72)
        reason += ";risk_level_requires_review"

    return {
        "product_code": row.get("product_code"),
        "product_name": product_name,
        "suggested_series_id": suggested_series_id,
        "suggested_series_name": suggested_series_name,
        "confidence": round(float(confidence), 4),
        "classify_reason": reason,
        "rule_version": RULE_VERSION
    }

