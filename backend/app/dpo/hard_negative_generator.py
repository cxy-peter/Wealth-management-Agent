from __future__ import annotations

import re
from typing import Any


HARD_NEGATIVE_TYPES = [
    "numeric_hallucination",
    "percentile_misinterpretation",
    "missing_evidence",
    "compliance_violation",
    "missing_risk",
    "task_mismatch",
    "source_overclaim",
]


def numeric_hallucination(chosen: str, tool_output: dict[str, Any]) -> str:
    text = chosen
    for field in ["return_3m", "max_drawdown", "scale_wow_bn"]:
        if field in tool_output:
            value = float(tool_output[field])
            replacement = value * (1.8 if value >= 0 else -1.6)
            text = text.replace(f"{value * 100:.2f}%", f"{replacement * 100:.2f}%")
            text = text.replace(f"{value:.2f}", f"{replacement:.2f}")
    return text + "（数字未经复核）"


def percentile_misinterpretation(chosen: str, _: dict[str, Any]) -> str:
    return re.sub(r"低分位|分位偏低|需关注", "同类领先", chosen) + "，并据此外推未来表现。"


def missing_evidence(chosen: str, _: dict[str, Any]) -> str:
    return re.sub(r"\s*\[evidence_id=[^\]]+\]", "", chosen)


def compliance_violation(chosen: str, _: dict[str, Any]) -> str:
    return chosen + " 建议买入并推荐配置，收益稳定可期。"


def missing_risk(chosen: str, _: dict[str, Any]) -> str:
    first_sentence = chosen.split("。", 1)[0]
    return first_sentence + "，整体表现较好。"


def task_mismatch(chosen: str, _: dict[str, Any]) -> str:
    return "本段改写为泛市场点评，未按照渠道对标或产品周报任务展开。" + missing_evidence(chosen, {})


def source_overclaim(chosen: str, _: dict[str, Any]) -> str:
    return chosen + " 以上结论来自真实全市场实时产品数据和官网实时接入。"


GENERATORS = {
    "numeric_hallucination": numeric_hallucination,
    "percentile_misinterpretation": percentile_misinterpretation,
    "missing_evidence": missing_evidence,
    "compliance_violation": compliance_violation,
    "missing_risk": missing_risk,
    "task_mismatch": task_mismatch,
    "source_overclaim": source_overclaim,
}


def make_hard_negative(chosen: str, tool_output: dict[str, Any], negative_type: str) -> str:
    generator = GENERATORS.get(negative_type)
    if generator is None:
        raise ValueError(f"unknown hard negative type: {negative_type}")
    return generator(chosen, tool_output)

