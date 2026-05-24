from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.optimization.context_features import extract_context  # noqa: E402
from backend.app.optimization.contextual_bandit import LinUCBPolicy  # noqa: E402
from backend.app.optimization.reward import compute_reward  # noqa: E402
from backend.app.optimization.router_policy import ACTIONS, EpsilonGreedyRouter  # noqa: E402

CASES_PATH = ROOT / "eval" / "contextual_bandit_cases.json"
RESULTS_PATH = ROOT / "eval" / "contextual_bandit_results.json"

ACTION_LATENCY_MS = {
    "fast_weekly_snapshot": 120.0,
    "standard_weekly_report": 430.0,
    "deep_product_review": 820.0,
    "benchmark_only": 240.0,
    "market_update_only": 180.0,
}

ACTION_TOOL_COUNT = {
    "fast_weekly_snapshot": 3,
    "standard_weekly_report": 7,
    "deep_product_review": 10,
    "benchmark_only": 4,
    "market_update_only": 3,
}

PARTIAL_ROUTE_MATCH = {
    ("standard_weekly_report", "deep_product_review"): 0.76,
    ("deep_product_review", "standard_weekly_report"): 0.72,
    ("fast_weekly_snapshot", "standard_weekly_report"): 0.62,
    ("standard_weekly_report", "fast_weekly_snapshot"): 0.70,
    ("benchmark_only", "standard_weekly_report"): 0.55,
    ("standard_weekly_report", "benchmark_only"): 0.62,
    ("market_update_only", "standard_weekly_report"): 0.48,
    ("standard_weekly_report", "market_update_only"): 0.64,
    ("benchmark_only", "deep_product_review"): 0.52,
    ("market_update_only", "deep_product_review"): 0.50,
}


def _oracle_for_case(case: dict[str, Any]) -> str:
    if case["is_product_benchmark"]:
        return "deep_product_review" if case["human_review_required"] or case["missing_nav_ratio"] >= 0.22 else "benchmark_only"
    if case["is_market_update"] and case["benchmark_failed_count"] < 8:
        return "market_update_only"
    if case["latency_budget_ms"] <= 450 and case["benchmark_failed_count"] <= 4 and case["scale_drop_count"] <= 4:
        return "fast_weekly_snapshot"
    if case["human_review_required"] or case["is_high_risk_product"] or case["missing_nav_ratio"] >= 0.22:
        return "deep_product_review"
    return "standard_weekly_report"


def _default_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    scenarios = [
        ("weekly_normal", "weekly_report"),
        ("benchmark_focus", "product_benchmark"),
        ("market_update", "market_update"),
        ("high_risk_review", "weekly_report"),
        ("low_latency", "weekly_report"),
        ("missing_nav", "weekly_report"),
        ("scale_pressure", "weekly_report"),
        ("benchmark_failed", "weekly_report"),
    ]
    risk_levels = ["R1", "R2", "R3", "R4", "R5"]
    for i in range(96):
        scenario, request_type = scenarios[i % len(scenarios)]
        risk_level = risk_levels[(i * 2 + 1) % len(risk_levels)]
        product_pool_size = 48 + (i * 17) % 105
        benchmark_failed = (i * 5) % 28
        scale_drop = (i * 7) % 36
        missing_nav = round(((i * 3) % 30) / 100, 3)
        latency_budget = [320, 450, 700, 950, 1400, 1800][i % 6]
        case = {
            "case_id": f"weekly_cb_{i + 1:03d}",
            "scenario": scenario,
            "request_type": request_type,
            "is_weekly_report": 1 if request_type == "weekly_report" else 0,
            "is_product_benchmark": 1 if request_type == "product_benchmark" else 0,
            "is_market_update": 1 if request_type == "market_update" else 0,
            "is_high_risk_product": risk_level in {"R4", "R5"} or scenario == "high_risk_review",
            "risk_level": risk_level,
            "benchmark_failed_count": benchmark_failed if scenario != "benchmark_focus" else 3 + (i % 9),
            "scale_drop_count": scale_drop if scenario != "market_update" else 2 + (i % 5),
            "product_pool_size": product_pool_size,
            "avg_return_percentile": round(max(0.05, min(0.95, 0.72 - ((i % 18) / 30))), 4),
            "avg_drawdown_percentile": round(max(0.05, min(0.95, 0.78 - ((i % 15) / 28))), 4),
            "missing_nav_ratio": missing_nav if scenario == "missing_nav" else round(missing_nav / 3, 3),
            "market_new_issue_count": 38 + (i * 11) % 70,
            "latency_budget_ms": latency_budget if scenario == "low_latency" else latency_budget + 250,
            "human_review_required": scenario == "high_risk_review" or (benchmark_failed >= 22 and risk_level in {"R4", "R5"}),
            "forbidden_wording_injection": i in {17, 58},
        }
        case["oracle_action"] = _oracle_for_case(case)
        cases.append(case)
    return cases


def _load_cases() -> list[dict[str, Any]]:
    cases = _default_cases()
    CASES_PATH.write_text(json.dumps(cases, ensure_ascii=False, indent=2), encoding="utf-8")
    return cases


def _route_match(action: str, oracle: str) -> float:
    if action == oracle:
        return 1.0
    return PARTIAL_ROUTE_MATCH.get((action, oracle), 0.25)


def _unnecessary_tool_penalty(action: str, oracle: str) -> float:
    extra = ACTION_TOOL_COUNT[action] - ACTION_TOOL_COUNT[oracle]
    if extra <= 0:
        return 0.0 if action == oracle else 0.12
    return min(1.0, extra / max(ACTION_TOOL_COUNT[oracle], 1))


def _latency(case: dict[str, Any], action: str) -> float:
    multiplier = 1.0
    if case.get("human_review_required"):
        multiplier += 0.25
    if case.get("missing_nav_ratio", 0) >= 0.18 and action in {"standard_weekly_report", "deep_product_review"}:
        multiplier += 0.12
    if case.get("product_pool_size", 0) >= 120 and action in {"benchmark_only", "deep_product_review"}:
        multiplier += 0.10
    return round(ACTION_LATENCY_MS[action] * multiplier, 2)


def evaluate_action(case: dict[str, Any], action: str) -> dict[str, Any]:
    oracle = case["oracle_action"]
    route_match = _route_match(action, oracle)
    latency_ms = _latency(case, action)
    high_risk = bool(case.get("is_high_risk_product")) or bool(case.get("human_review_required"))
    underpowered = ACTION_TOOL_COUNT[action] < ACTION_TOOL_COUNT[oracle] and action != oracle
    latency_budget = float(case.get("latency_budget_ms", 900))
    metrics = {
        "tool_call_success": 1.0 if not (case.get("missing_nav_ratio", 0) > 0.25 and action == "fast_weekly_snapshot") else 0.78,
        "metric_consistency": 0.68 if underpowered and oracle in {"standard_weekly_report", "deep_product_review"} else 1.0,
        "risk_warning_coverage": 1.0 if (not high_risk or action in {"deep_product_review", "standard_weekly_report"}) else 0.58,
        "evidence_coverage": 0.62 if underpowered else 0.86 if action == "fast_weekly_snapshot" else 1.0,
        "report_format_pass": 0.90 if underpowered else 1.0,
        "route_match_score": route_match,
        "latency_ms": latency_ms,
        "unnecessary_tool_penalty": _unnecessary_tool_penalty(action, oracle),
        "forbidden_wording_hit": 0.0,
    }
    # A route that ignores injected bad wording should be treated as non-pass
    # for verifier coverage, but the policy still receives the large compliance
    # penalty only if it chooses a shallow route.
    if case.get("forbidden_wording_injection") and action in {"fast_weekly_snapshot", "market_update_only"}:
        metrics["forbidden_wording_hit"] = 1.0
    verifier_pass = (
        metrics["metric_consistency"] >= 0.8
        and metrics["evidence_coverage"] >= 0.8
        and metrics["forbidden_wording_hit"] == 0
        and (not high_risk or metrics["risk_warning_coverage"] >= 0.8)
    )
    reward = compute_reward(metrics)
    if latency_ms > latency_budget * 1.25:
        reward = round(reward - 0.04, 4)
    return {
        "action": action,
        "reward": reward,
        "latency_ms": latency_ms,
        "verifier_pass": verifier_pass,
        "metrics": metrics,
    }


def _summarize(name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    rewards = [item["reward"] for item in rows]
    latencies = [item["latency_ms"] for item in rows]
    failures = [item["metrics"]["forbidden_wording_hit"] for item in rows]
    regret = [item["oracle_reward"] - item["reward"] for item in rows]
    verifier_passes = [item["verifier_pass"] for item in rows]
    return {
        "strategy": name,
        "average_reward": round(mean(rewards), 4),
        "average_latency_ms": round(mean(latencies), 2),
        "action_distribution": dict(Counter(item["action"] for item in rows)),
        "regret_vs_oracle": round(mean(regret), 4),
        "verifier_pass_rate": round(sum(1 for item in verifier_passes if item) / len(verifier_passes), 4),
        "forbidden_wording_fail_rate": round(sum(failures) / len(failures), 4),
        "per_case_results": rows,
    }


def _oracle_result(case: dict[str, Any]) -> dict[str, Any]:
    return max((evaluate_action(case, action) for action in ACTIONS), key=lambda item: item["reward"])


def _run_fixed(cases: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for case in cases:
        result = evaluate_action(case, "standard_weekly_report")
        oracle = _oracle_result(case)
        rows.append({**result, "case_id": case["case_id"], "oracle_action": oracle["action"], "oracle_reward": oracle["reward"]})
    return _summarize("fixed_standard_research", rows)


def _run_epsilon(cases: list[dict[str, Any]]) -> dict[str, Any]:
    router = EpsilonGreedyRouter(epsilon=0.15, seed=24)
    rows = []
    for case in cases:
        action = router.select_action()
        result = evaluate_action(case, action)
        router.update(action, result["reward"])
        oracle = _oracle_result(case)
        rows.append({**result, "case_id": case["case_id"], "oracle_action": oracle["action"], "oracle_reward": oracle["reward"]})
    summary = _summarize("epsilon_greedy", rows)
    summary["policy_state"] = router.snapshot()
    return summary


def _run_linucb(cases: list[dict[str, Any]]) -> dict[str, Any]:
    policy = LinUCBPolicy(alpha=0.35, ridge_lambda=1.0, seed=24)
    for case in cases[:48]:
        context = extract_context(case)
        oracle = _oracle_result(case)
        policy.update(oracle["action"], context, oracle["reward"])
    rows = []
    for case in cases:
        context = extract_context(case)
        action, scores = policy.select_action(context)
        result = evaluate_action(case, action)
        policy.update(action, context, result["reward"])
        oracle = _oracle_result(case)
        rows.append(
            {
                **result,
                "case_id": case["case_id"],
                "oracle_action": oracle["action"],
                "oracle_reward": oracle["reward"],
                "context": context,
                "action_scores": {key: round(value, 4) for key, value in scores.items()},
            }
        )
    policy.save()
    summary = _summarize("linucb_contextual_bandit", rows)
    summary["policy_state_path"] = "data/router_policy_state.json"
    summary["warm_start_cases"] = 48
    return summary


def main() -> None:
    cases = _load_cases()
    strategies = {
        "fixed_standard_research": _run_fixed(cases),
        "epsilon_greedy": _run_epsilon(cases),
        "linucb_contextual_bandit": _run_linucb(cases),
    }
    payload = {
        "case_count": len(cases),
        "actions": ACTIONS,
        "strategies": strategies,
        "best_policy": max(strategies, key=lambda name: strategies[name]["average_reward"]),
    }
    RESULTS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
