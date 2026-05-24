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
    "required_tools",
    "required_evidence",
    "verifier_required",
    "guardrail_required",
}


class DPOPlannerAdapter:
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
        if "steps" in plan and not isinstance(plan["steps"], list):
            type_errors.append("steps must be list")
        if "required_tools" in plan and not isinstance(plan["required_tools"], list):
            type_errors.append("required_tools must be list")
        return {"valid": not missing and not type_errors, "missing_keys": missing, "type_errors": type_errors}

    def generate_plan(self, prompt: dict[str, Any]) -> dict[str, Any]:
        task = str(prompt.get("user_task", "")).lower()
        tools = set(prompt.get("available_tools", []))
        plan_type = "weekly_report"
        required = {"load_weekly_snapshot", "weekly_report_verifier", "guardrail_check"}
        if "渠道" in task or "channel" in task:
            plan_type = "channel_benchmark"
            required.add("channel_benchmark")
        if "竞品" in task or "peer" in task:
            plan_type = "peer_benchmark"
            required.add("peer_benchmark")
        if "分位" in task or "percentile" in task:
            required.add("calculate_percentile_metrics")
        if "风险" in task or prompt.get("product_context", {}).get("benchmark_status") == "below_lower":
            required.add("classify_risk_events")
        plan = {
            "plan_type": plan_type,
            "steps": [
                "读取周报快照、同业池和数据源状态",
                "调用与任务匹配的指标/对标工具",
                "生成带 evidence_id/tool_call_id 的摘要",
                "进入 verifier 和 guardrail",
            ],
            "required_tools": sorted(tool for tool in required if not tools or tool in tools or tool in {"weekly_report_verifier", "guardrail_check"}),
            "required_evidence": ["evidence_id", "tool_call_id", "source_type"],
            "verifier_required": True,
            "guardrail_required": True,
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

