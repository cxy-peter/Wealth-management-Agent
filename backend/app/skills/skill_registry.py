from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class SkillSpec:
    name: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    timeout_seconds: int = 15
    max_calls: int = 3
    risk_level: str = "low"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


SKILLS = {
    "data_upload_skill": SkillSpec(
        "data_upload_skill",
        {"file_type": "csv|xlsx|pptx", "dataset_scope": "own_company|full_market|reference_rates", "target_schema": "string"},
        {"upload_id": "string", "quality_report": "object", "evidence_ids": "array"},
        risk_level="medium",
    ),
    "weekly_summary_skill": SkillSpec(
        "weekly_summary_skill",
        {"report_date": "YYYY-MM-DD", "filters": "object"},
        {"summary": "object", "evidence_ids": "array"},
    ),
    "peer_benchmark_skill": SkillSpec(
        "peer_benchmark_skill",
        {"product_code": "string", "report_date": "YYYY-MM-DD"},
        {"peer_summary": "object", "evidence_ids": "array"},
    ),
    "channel_benchmark_skill": SkillSpec(
        "channel_benchmark_skill",
        {"channel": "string", "product_type": "string"},
        {"channel_summary": "object", "evidence_ids": "array"},
    ),
    "nav_compare_skill": SkillSpec(
        "nav_compare_skill",
        {"product_codes": "array", "range": "1m|3m|6m|all"},
        {"comparison": "object", "evidence_ids": "array"},
    ),
    "dpo_report_skill": SkillSpec(
        "dpo_report_skill",
        {"tool_outputs": "object", "task_type": "string"},
        {"draft": "string", "model_mode": "string"},
        risk_level="medium",
    ),
    "verifier_skill": SkillSpec(
        "verifier_skill",
        {"report": "object"},
        {"pass": "boolean", "failed_checks": "array"},
        risk_level="high",
    ),
}


def list_skills() -> list[dict[str, Any]]:
    return [skill.to_dict() for skill in SKILLS.values()]


def _contains_any(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def select_skills(user_task: str) -> list[str]:
    """Rule-based planner used as a fallback when the DPO plan is invalid."""

    task = str(user_task)
    if _contains_any(task, ["上传", "导入", "upload", "import", "涓婁紶"]):
        return ["data_upload_skill", "verifier_skill"]
    if _contains_any(task, ["利率", "基准利率", "reference", "rate", "鍒╃巼"]):
        return ["weekly_summary_skill", "verifier_skill"]
    if _contains_any(task, ["系列", "series", "绯诲垪"]):
        return ["weekly_summary_skill", "dpo_report_skill", "verifier_skill"]
    if _contains_any(task, ["渠道", "channel", "娓犻亾"]):
        return ["channel_benchmark_skill", "verifier_skill"]
    if _contains_any(task, ["竞品", "同业", "对标", "benchmark", "peer", "绔炲搧", "瀵规爣"]):
        return ["peer_benchmark_skill", "nav_compare_skill", "verifier_skill"]
    return ["weekly_summary_skill", "dpo_report_skill", "verifier_skill"]
