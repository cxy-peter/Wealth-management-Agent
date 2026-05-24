"""Relative valuation logic for the research-assistant workflow."""
from __future__ import annotations

from typing import Any


def _safe_float(row: Any, key: str, default: float = 0.0) -> float:
    value = row.get(key, default)
    try:
        return float(value)
    except Exception:
        return default


def evaluate_valuation(fundamentals_df: Any) -> dict[str, Any]:
    if fundamentals_df.empty:
        return {
            "available": False,
            "valuation_band": "缺少样例估值字段",
            "pe_ttm": 0.0,
            "pb": 0.0,
            "peer_pe_median": 0.0,
            "peer_pb_median": 0.0,
            "points": ["样例数据未覆盖估值字段，需要接入公开财报或估值表后再更新。"],
        }

    row = fundamentals_df.iloc[-1]
    pe = _safe_float(row, "pe_ttm")
    pb = _safe_float(row, "pb")
    peer_pe = _safe_float(row, "industry_pe_median")
    peer_pb = _safe_float(row, "industry_pb_median")
    pe_ratio = pe / peer_pe if peer_pe else 0.0
    pb_ratio = pb / peer_pb if peer_pb else 0.0

    if pe_ratio >= 1.15 or pb_ratio >= 1.15:
        band = "相对同业中位数偏高"
    elif pe_ratio <= 0.85 and pb_ratio <= 0.9:
        band = "相对同业中位数偏低"
    else:
        band = "接近同业中位数区间"

    return {
        "available": True,
        "valuation_band": band,
        "pe_ttm": pe,
        "pb": pb,
        "peer_pe_median": peer_pe,
        "peer_pb_median": peer_pb,
        "pe_to_peer": pe_ratio,
        "pb_to_peer": pb_ratio,
        "points": [
            f"PE(TTM) 为 {pe:.1f}，同业样例中位数为 {peer_pe:.1f}。",
            f"PB 为 {pb:.1f}，同业样例中位数为 {peer_pb:.1f}。",
            "估值结论只用于横向描述，不输出交易方向或收益承诺。",
        ],
    }
