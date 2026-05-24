from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.agents.risk_guardrail_agent import contains_forbidden_wording  # noqa: E402
from backend.app.agents.verifier_agent import REQUIRED_SECTIONS  # noqa: E402
from backend.app.agents.workflow import ResearchRequest, run_workflow  # noqa: E402
from backend.app.optimization.reward import compute_reward  # noqa: E402
from backend.app.optimization.router_policy import ACTION_TO_REQUEST, EpsilonGreedyRouter  # noqa: E402
from backend.app.storage import add_eval_result  # noqa: E402


def evaluate_route(case: dict, action: str) -> dict:
    params = ACTION_TO_REQUEST[action]
    started = time.perf_counter()
    result = run_workflow(
        ResearchRequest(
            symbol=case["symbol"],
            company=case["company"],
            analysis_type=params["analysis_type"],
            risk_preference=params["risk_preference"],
            product_filters=case.get("product_filters", {}),
            output_path=str(Path("reports") / f"route_{action}_{case['symbol']}.md"),
        )
    )
    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    report = result.get("report_markdown", "")
    metrics = {
        "tool_call_success": 1.0 if all(item.get("success") for item in result.get("tool_calls", [])) else 0.0,
        "metric_consistency": 1.0 if result.get("verification_result", {}).get("metric_mismatches") == [] else 0.0,
        "risk_warning_coverage": 1.0 if result.get("risk_flags") else 0.0,
        "evidence_coverage": 1.0 if not result.get("verification_result", {}).get("missing_evidence") else 0.0,
        "report_format_pass": 1.0 if all(section in report for section in REQUIRED_SECTIONS) else 0.0,
        "route_match_score": 1.0 if action == case.get("preferred_action", action) else 0.5,
        "latency_ms": latency_ms,
        "unnecessary_tool_penalty": 0.0 if action == case.get("preferred_action", action) else 0.25,
        "forbidden_wording_hit": 1.0 if contains_forbidden_wording(report) else 0.0,
    }
    reward = compute_reward(metrics)
    return {
        "symbol": case["symbol"],
        "action": action,
        "planner_task_type": result.get("planner_plan", {}).get("task_type"),
        "reward": reward,
        "metrics": metrics,
        "run_id": result.get("run_id"),
    }


def main() -> None:
    cases = json.loads((ROOT / "eval" / "route_eval_cases.json").read_text(encoding="utf-8"))
    router = EpsilonGreedyRouter(epsilon=0.15, seed=7)
    evaluations = []
    for case in cases:
        action = case.get("preferred_action") or router.select_action()
        item = evaluate_route(case, action)
        router.update(action, item["reward"])
        evaluations.append(item)

    payload = {
        "case_count": len(evaluations),
        "average_reward": round(sum(item["reward"] for item in evaluations) / len(evaluations), 4),
        "policy": router.snapshot(),
        "evaluations": evaluations,
    }
    out = ROOT / "eval" / "route_optimization_results.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    add_eval_result("route_optimization", payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if any(item["metrics"]["forbidden_wording_hit"] for item in evaluations):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
