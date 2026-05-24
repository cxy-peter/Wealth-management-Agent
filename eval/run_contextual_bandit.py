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
    "fast_snapshot": 120.0,
    "standard_research": 420.0,
    "deep_review": 760.0,
    "product_compare": 220.0,
    "risk_only": 180.0,
}

ACTION_TOOL_COUNT = {
    "fast_snapshot": 4,
    "standard_research": 7,
    "deep_review": 8,
    "product_compare": 1,
    "risk_only": 4,
}

PARTIAL_ROUTE_MATCH = {
    ("standard_research", "deep_review"): 0.70,
    ("deep_review", "standard_research"): 0.75,
    ("fast_snapshot", "standard_research"): 0.60,
    ("standard_research", "fast_snapshot"): 0.65,
    ("risk_only", "deep_review"): 0.55,
    ("deep_review", "risk_only"): 0.65,
    ("product_compare", "standard_research"): 0.45,
    ("standard_research", "product_compare"): 0.55,
}


def _load_cases() -> list[dict[str, Any]]:
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


def _route_match(action: str, oracle: str) -> float:
    if action == oracle:
        return 1.0
    return PARTIAL_ROUTE_MATCH.get((action, oracle), 0.25)


def _unnecessary_tool_penalty(action: str, oracle: str) -> float:
    extra = ACTION_TOOL_COUNT[action] - ACTION_TOOL_COUNT[oracle]
    if extra <= 0:
        return 0.0 if action == oracle else 0.15
    return min(1.0, extra / max(ACTION_TOOL_COUNT[oracle], 1))


def _latency(case: dict[str, Any], action: str) -> float:
    multiplier = 1.0
    if case.get("human_review_required"):
        multiplier += 0.20
    if case.get("avg_news_risk", 0) >= 4:
        multiplier += 0.10
    if case.get("missing_fundamental_data") and action in {"standard_research", "deep_review"}:
        multiplier += 0.08
    return round(ACTION_LATENCY_MS[action] * multiplier, 2)


def evaluate_action(case: dict[str, Any], action: str) -> dict[str, Any]:
    oracle = case["oracle_action"]
    route_match = _route_match(action, oracle)
    latency_ms = _latency(case, action)
    product_pool_empty = bool(case.get("product_pool_empty", False))
    missing_data = bool(case.get("missing_fundamental_data", False))
    high_risk = float(case.get("avg_news_risk", 0)) >= 4 or bool(case.get("human_review_required", False))

    underpowered_route = ACTION_TOOL_COUNT[action] < ACTION_TOOL_COUNT[oracle] and action != oracle
    metrics = {
        "tool_call_success": 1.0 if not (product_pool_empty and action == "product_compare") else 0.85,
        "metric_consistency": 0.70
        if underpowered_route and oracle in {"standard_research", "deep_review"}
        else 0.85
        if missing_data and action in {"standard_research", "deep_review"}
        else 1.0,
        "risk_warning_coverage": 1.0 if (not high_risk or action in {"risk_only", "deep_review", "standard_research"}) else 0.65,
        "evidence_coverage": 0.62
        if underpowered_route
        else 1.0
        if action != "fast_snapshot" or route_match >= 0.8
        else 0.82,
        "report_format_pass": 0.90 if underpowered_route else 1.0,
        "route_match_score": route_match,
        "latency_ms": latency_ms,
        "unnecessary_tool_penalty": _unnecessary_tool_penalty(action, oracle),
        "forbidden_wording_hit": 0.0,
    }
    return {
        "action": action,
        "reward": compute_reward(metrics),
        "latency_ms": latency_ms,
        "metrics": metrics,
    }


def _summarize(name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    rewards = [item["reward"] for item in rows]
    latencies = [item["latency_ms"] for item in rows]
    failures = [item["metrics"]["forbidden_wording_hit"] for item in rows]
    regret = [item["oracle_reward"] - item["reward"] for item in rows]
    return {
        "strategy": name,
        "average_reward": round(mean(rewards), 4),
        "average_latency_ms": round(mean(latencies), 2),
        "forbidden_wording_fail_rate": round(sum(failures) / len(failures), 4),
        "action_distribution": dict(Counter(item["action"] for item in rows)),
        "regret_vs_oracle": round(mean(regret), 4),
        "per_case_results": rows,
    }


def _run_fixed(cases: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for case in cases:
        result = evaluate_action(case, "standard_research")
        oracle = max((evaluate_action(case, action) for action in ACTIONS), key=lambda item: item["reward"])
        rows.append({**result, "case_id": case["case_id"], "oracle_action": oracle["action"], "oracle_reward": oracle["reward"]})
    return _summarize("fixed_standard_research", rows)


def _run_epsilon(cases: list[dict[str, Any]]) -> dict[str, Any]:
    router = EpsilonGreedyRouter(epsilon=0.15, seed=24)
    rows = []
    for case in cases:
        action = router.select_action()
        result = evaluate_action(case, action)
        router.update(action, result["reward"])
        oracle = max((evaluate_action(case, item) for item in ACTIONS), key=lambda item: item["reward"])
        rows.append({**result, "case_id": case["case_id"], "oracle_action": oracle["action"], "oracle_reward": oracle["reward"]})
    summary = _summarize("epsilon_greedy", rows)
    summary["policy_state"] = router.snapshot()
    return summary


def _run_linucb(cases: list[dict[str, Any]]) -> dict[str, Any]:
    policy = LinUCBPolicy(alpha=0.65, ridge_lambda=1.0, seed=24)
    rows = []
    for case in cases:
        context = extract_context(case)
        action, scores = policy.select_action(context)
        result = evaluate_action(case, action)
        policy.update(action, context, result["reward"])
        oracle = max((evaluate_action(case, item) for item in ACTIONS), key=lambda item: item["reward"])
        rows.append(
            {
                **result,
                "case_id": case["case_id"],
                "oracle_action": oracle["action"],
                "oracle_reward": oracle["reward"],
                "action_scores": {key: round(value, 4) for key, value in scores.items()},
            }
        )
    policy.save()
    summary = _summarize("linucb_contextual_bandit", rows)
    summary["policy_state_path"] = "data/router_policy_state.json"
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
        "strategies": strategies,
        "best_policy": max(strategies, key=lambda name: strategies[name]["average_reward"]),
    }
    RESULTS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
