from __future__ import annotations

import importlib
import time
from typing import Any

from backend.app.models.dpo_planner_adapter import DPOPlannerAdapter
from backend.app.skills.harness_validator import HarnessValidator
from backend.app.skills.skill_registry import SKILLS, select_skills
from backend.app.skills.skill_trace import make_skill_call

MODULE_BY_SKILL = {
    "data_upload_skill": "backend.app.skills.data_upload_skill",
    "weekly_summary_skill": "backend.app.skills.weekly_summary_skill",
    "peer_benchmark_skill": "backend.app.skills.peer_benchmark_skill",
    "channel_benchmark_skill": "backend.app.skills.channel_benchmark_skill",
    "nav_compare_skill": "backend.app.skills.nav_compare_skill",
    "dpo_report_skill": "backend.app.skills.dpo_report_skill",
    "verifier_skill": "backend.app.skills.verifier_skill",
}


def _input_for_skill(skill_name: str, task_payload: dict[str, Any], tool_outputs: dict[str, Any]) -> dict[str, Any]:
    if skill_name == "data_upload_skill":
        return {
            "dataset_scope": task_payload.get("dataset_scope", "own_company"),
            "target_schema": task_payload.get("target_schema", "product_weekly_snapshot"),
            "row_count": task_payload.get("row_count", 0),
            "upload_id": task_payload.get("upload_id"),
        }
    if skill_name == "weekly_summary_skill":
        return {"report_date": task_payload.get("report_date"), "filters": task_payload.get("filters", {})}
    if skill_name == "peer_benchmark_skill":
        return {"product_code": task_payload.get("product_code", "WP0001"), "report_date": task_payload.get("report_date")}
    if skill_name == "channel_benchmark_skill":
        return {"product_type": task_payload.get("product_type"), "channel": task_payload.get("channel")}
    if skill_name == "nav_compare_skill":
        return {"product_codes": task_payload.get("product_codes", ["WP0001", "WP0002"]), "range_weeks": task_payload.get("range_weeks", 13)}
    if skill_name == "dpo_report_skill":
        return {"tool_outputs": tool_outputs, "task_type": task_payload.get("task_type", "weekly_product_summary")}
    if skill_name == "verifier_skill":
        return {"report": tool_outputs.get("weekly_summary_skill") or tool_outputs.get("dpo_report_skill") or tool_outputs}
    return dict(task_payload)


def execute_skill_harness(user_task: str, task_payload: dict[str, Any] | None = None, max_total_calls: int = 3) -> dict[str, Any]:
    task_payload = task_payload or {}
    selected = select_skills(user_task)[:max_total_calls]
    planner_prompt = {
        "user_task": user_task,
        "dataset_scope": task_payload.get("dataset_scope"),
        "available_skills": list(SKILLS),
        "data_quality_status": task_payload.get("data_quality_status", {}),
    }
    planner = DPOPlannerAdapter().generate_plan(planner_prompt)
    validator = HarnessValidator()
    tool_outputs: dict[str, Any] = {}
    skill_calls = []

    for skill_name in selected:
        spec = SKILLS[skill_name]
        input_payload = _input_for_skill(skill_name, task_payload, tool_outputs)
        started_at = time.perf_counter()
        try:
            module = importlib.import_module(MODULE_BY_SKILL[skill_name])
            output = module.run(**input_payload)
            harness_result = validator.validate(output, report_type=task_payload.get("task_type", "weekly_report"))
            success = bool(harness_result["pass"])
            error_type = None
            tool_outputs[skill_name] = output
        except Exception as exc:  # pragma: no cover - defensive trace path
            output = {"error": str(exc)}
            harness_result = {"pass": False, "failed_rules": ["skill_exception"], "error": str(exc)}
            success = False
            error_type = exc.__class__.__name__
        skill_calls.append(
            make_skill_call(
                skill_name=skill_name,
                input_payload=input_payload,
                output=output,
                timeout_seconds=spec.timeout_seconds,
                max_calls=spec.max_calls,
                risk_level=spec.risk_level,
                started_at=started_at,
                success=success,
                error_type=error_type,
                harness_result=harness_result,
            )
        )

    failed_rules = sorted({rule for call in skill_calls for rule in call["harness_result"].get("failed_rules", [])})
    return {
        "user_task": user_task,
        "selected_skills": selected,
        "dpo_planner": planner,
        "skill_calls": skill_calls,
        "harness_result": {
            "pass": not failed_rules,
            "failed_rules": failed_rules,
            "source_boundary_check": "fail" if "source_boundary_rules" in failed_rules else "pass",
        },
        "trace": {
            "selected_skills": selected,
            "skill_call_count": len(skill_calls),
            "evidence_ids": list(dict.fromkeys(eid for call in skill_calls for eid in call.get("evidence_ids", []))),
        },
    }

