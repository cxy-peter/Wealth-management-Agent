from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DPOPlannerMetadata:
    model_mode: str
    adapter_path: str
    base_model: str
    fallback_required: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


REQUIRED_PLAN_KEYS = {
    "plan_type",
    "steps",
    "selected_skills",
    "required_evidence",
    "verifier_required",
    "guardrail_required",
}


def _contains_any(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


class DPOPlannerAdapter:
    """DPO-capable planner adapter with deterministic fallback.

    The fallback aligns planning preferences without loading model weights. It
    selects skills and review gates; metric calculation remains in deterministic
    tools.
    """

    def __init__(self, adapter_path: str | None = None, base_model: str | None = None) -> None:
        self.adapter_path = adapter_path or os.getenv("DPO_PLANNER_ADAPTER_PATH", "")
        self.base_model = base_model or os.getenv("DPO_PLANNER_BASE_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
        available = bool(self.adapter_path and Path(self.adapter_path).exists())
        self.metadata = DPOPlannerMetadata(
            model_mode="dpo_adapter" if available else "template_fallback",
            adapter_path=self.adapter_path,
            base_model=self.base_model,
            fallback_required=not available,
            reason="adapter path found" if available else "adapter path missing; deterministic planner template used",
        )

    @staticmethod
    def validate_plan(plan: dict[str, Any]) -> dict[str, Any]:
        missing = sorted(REQUIRED_PLAN_KEYS - set(plan))
        type_errors = []
        for key in ["steps", "selected_skills", "required_evidence"]:
            if key in plan and not isinstance(plan[key], list):
                type_errors.append(f"{key} must be list")
        if "selected_skills" in plan and not all(isinstance(skill, str) for skill in plan["selected_skills"]):
            type_errors.append("selected_skills must contain strings")
        return {"valid": not missing and not type_errors, "missing_keys": missing, "type_errors": type_errors}

    def generate_plan(self, prompt: dict[str, Any]) -> dict[str, Any]:
        task = str(prompt.get("user_task", ""))
        dataset_scope = str(prompt.get("dataset_scope") or "")
        available_skills = set(prompt.get("available_skills") or [])
        data_quality = prompt.get("data_quality_status") or {}

        plan_type = "weekly_report"
        selected = ["weekly_summary_skill", "dpo_report_skill", "verifier_skill"]

        if _contains_any(task, ["上传", "导入", "upload", "import", "涓婁紶"]) or dataset_scope:
            plan_type = "data_upload"
            selected = ["data_upload_skill", "verifier_skill"]

        if _contains_any(task, ["渠道", "channel", "娓犻亾"]):
            plan_type = "channel_benchmark"
            selected = ["channel_benchmark_skill", "verifier_skill"]
        elif _contains_any(task, ["竞品", "同业", "对标", "benchmark", "peer", "绔炲搧", "瀵规爣"]):
            plan_type = "peer_benchmark"
            selected = ["peer_benchmark_skill", "nav_compare_skill", "verifier_skill"]

        if _contains_any(task, ["净值对比", "五只", "5只", "nav compare", "five product"]):
            plan_type = "nav_compare"
            selected = ["nav_compare_skill", "dpo_report_skill", "verifier_skill"]

        if _contains_any(task, ["系列", "series", "绯诲垪"]):
            plan_type = "series_compare"
            selected = ["weekly_summary_skill", "dpo_report_skill", "verifier_skill"]

        if _contains_any(task, ["利率", "基准利率", "reference", "rate", "鍒╃巼"]) or dataset_scope == "reference_rates":
            plan_type = "reference_rate_benchmark"
            selected = ["data_upload_skill", "verifier_skill"] if dataset_scope == "reference_rates" else ["weekly_summary_skill", "verifier_skill"]

        if available_skills:
            selected = [skill for skill in selected if skill in available_skills]
            if "verifier_skill" in available_skills and "verifier_skill" not in selected:
                selected.append("verifier_skill")

        human_review_required = bool(data_quality.get("missing_required_fields") or data_quality.get("forbidden_wording_hit"))
        plan = {
            "plan_type": plan_type,
            "steps": [
                "读取 dataset_scope 与数据质量状态",
                "选择与任务匹配的 Skill-Harness skills",
                "要求所有关键结论带 evidence_id 或 tool_call_id",
                "进入 verifier 与 guardrail",
            ],
            "selected_skills": selected[:3],
            "required_tools": selected[:3],
            "required_evidence": ["evidence_id", "source_type", "dataset_scope"],
            "verifier_required": True,
            "guardrail_required": True,
            "human_review_required": human_review_required,
        }
        validation = self.validate_plan(plan)
        return {
            "model_mode": self.metadata.model_mode,
            "adapter_path": self.metadata.adapter_path,
            "base_model": self.metadata.base_model,
            "generated_plan": plan,
            "fallback_required": self.metadata.fallback_required,
            "schema_validation": validation,
        }

    def to_json(self, prompt: dict[str, Any]) -> str:
        return json.dumps(self.generate_plan(prompt), ensure_ascii=False)
