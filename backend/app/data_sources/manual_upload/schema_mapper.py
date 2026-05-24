from __future__ import annotations

from typing import Any


TARGET_SCHEMAS = {
    "product_weekly_snapshot": [
        "report_date",
        "product_code",
        "product_name",
        "product_type",
        "channel",
        "risk_level",
        "product_scale_bn",
        "scale_wow_bn",
        "scale_mom_bn",
        "latest_nav",
        "return_3m",
        "max_drawdown",
        "volatility",
        "sharpe",
        "benchmark_status",
    ],
    "peer_product_metrics": [
        "peer_product_code",
        "report_date",
        "return_3m",
        "max_drawdown",
        "volatility",
        "sharpe",
        "return_percentile",
        "drawdown_percentile",
    ],
    "market_issuance_weekly": [
        "report_date",
        "new_product_count",
        "by_investment_nature_json",
        "by_duration_json",
        "benchmark_lower_avg",
        "benchmark_upper_avg",
    ],
}

ALIASES = {
    "产品代码": "product_code",
    "产品名称": "product_name",
    "产品类型": "product_type",
    "渠道": "channel",
    "风险等级": "risk_level",
    "报告日期": "report_date",
    "规模": "product_scale_bn",
    "本周规模": "product_scale_bn",
    "较上周": "scale_wow_bn",
    "较上月": "scale_mom_bn",
    "最新净值": "latest_nav",
    "近3月收益": "return_3m",
    "最大回撤": "max_drawdown",
    "波动率": "volatility",
    "夏普": "sharpe",
    "基准状态": "benchmark_status",
    "同业产品代码": "peer_product_code",
    "新发数量": "new_product_count",
}


def suggest_mapping(columns: list[str], target_schema: str) -> dict[str, Any]:
    required = TARGET_SCHEMAS.get(target_schema, [])
    normalized: dict[str, str] = {}
    lower_lookup = {str(column).strip().lower(): str(column) for column in columns}
    for column in columns:
        text = str(column).strip()
        mapped = ALIASES.get(text) or text
        if mapped in required:
            normalized[mapped] = text
    for field in required:
        if field not in normalized and field.lower() in lower_lookup:
            normalized[field] = lower_lookup[field.lower()]
    missing = [field for field in required if field not in normalized]
    return {
        "target_schema": target_schema,
        "mapping": normalized,
        "required_fields": required,
        "missing_required_fields": missing,
        "mapping_status": "pass" if not missing else "needs_confirmation",
    }

