"""Evaluation helpers shared by the CLI script and FastAPI endpoint."""
from __future__ import annotations

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.agents.risk_guardrail_agent import FORBIDDEN_PHRASES, contains_forbidden_wording
from backend.app.agents.workflow import ResearchRequest, run_workflow
from backend.app.storage import add_eval_result

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASES_PATH = ROOT / "eval" / "eval_cases.json"
DEFAULT_RESULTS_PATH = ROOT / "eval" / "results.json"

REQUIRED_REPORT_SECTIONS = [
    "合规说明",
    "数据与工具调用摘要",
    "核心量化指标",
    "基本面与估值摘要",
    "技术面风险观察",
    "同业产品对标样例",
    "新闻情绪与风险信号",
    "风险提示与可追溯结论",
]


def _load_cases(path: Path = DEFAULT_CASES_PATH) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def _metric_consistency(metrics: dict[str, Any], result: dict[str, Any] | None = None, case: dict[str, Any] | None = None) -> bool:
    keys = ["total_return", "annualized_return", "annualized_volatility", "max_drawdown", "sharpe_ratio"]
    if all(key in metrics and math.isfinite(float(metrics[key])) for key in keys):
        return True
    result = result or {}
    peer_rows = result.get("peer_summary", {}).get("table", [])
    if result.get("peer_summary", {}).get("product_count") == 0 and (case or {}).get("analysis_type") == "product":
        return True
    if peer_rows:
        product_keys = [
            "annualized_return",
            "annualized_volatility",
            "max_drawdown",
            "sharpe_ratio",
            "calmar_ratio",
            "benchmark_excess_return",
        ]
        return all(key in peer_rows[0] and math.isfinite(float(peer_rows[0][key])) for key in product_keys)
    return False


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    start = time.perf_counter()
    result = run_workflow(
        ResearchRequest(
            symbol=case["symbol"],
            company=case["company"],
            analysis_type=case.get("analysis_type", "full"),
            risk_preference=case.get("risk_preference", "balanced"),
            product_filters=case.get("product_filters", {}),
            output_path=str(Path("reports") / f"eval_{case['symbol']}.md"),
        )
    )
    latency_ms = round((time.perf_counter() - start) * 1000, 2)
    report = result["report_markdown"]

    report_format_pass = all(section in report for section in case.get("must_contain", REQUIRED_REPORT_SECTIONS))
    metric_consistency = _metric_consistency(result["metrics"], result, case)
    risk_warning_coverage = len(result.get("risk_flags", [])) >= case.get("min_risk_flags", 1)
    tool_call_success = all(item.get("success") for item in result.get("tool_calls", []))
    forbidden_wording_fail = contains_forbidden_wording(report)
    evidence_coverage = not result.get("verification_result", {}).get("missing_evidence")

    return {
        "symbol": case["symbol"],
        "company": case["company"],
        "latency_ms": latency_ms,
        "tool_call_success": tool_call_success,
        "report_format_pass": report_format_pass,
        "metric_consistency": metric_consistency,
        "risk_warning_coverage": risk_warning_coverage,
        "evidence_coverage": evidence_coverage,
        "forbidden_wording_fail": forbidden_wording_fail,
        "verification_pass": result.get("verification_result", {}).get("pass", False),
        "run_id": result.get("run_id"),
        "workflow_engine": result.get("workflow_engine"),
        "report_path": result.get("report_path"),
        "passed": all(
            [
                tool_call_success,
                report_format_pass,
                metric_consistency,
                risk_warning_coverage,
                evidence_coverage,
                not forbidden_wording_fail,
            ]
        ),
    }


def _rate(cases: list[dict[str, Any]], key: str) -> float:
    if not cases:
        return 0.0
    return round(sum(1 for item in cases if item[key]) / len(cases), 4)


def run_evaluation(
    cases_path: str | Path | None = None,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    cases = _load_cases(Path(cases_path) if cases_path else DEFAULT_CASES_PATH)
    case_results = [evaluate_case(case) for case in cases]
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "case_count": len(case_results),
        "metrics": {
            "tool_call_success": _rate(case_results, "tool_call_success"),
            "report_format_pass": _rate(case_results, "report_format_pass"),
            "metric_consistency": _rate(case_results, "metric_consistency"),
            "risk_warning_coverage": _rate(case_results, "risk_warning_coverage"),
            "evidence_coverage": _rate(case_results, "evidence_coverage"),
            "forbidden_wording_fail_rate": _rate(case_results, "forbidden_wording_fail"),
            "avg_latency_ms": round(
                sum(item["latency_ms"] for item in case_results) / len(case_results), 2
            )
            if case_results
            else 0.0,
        },
        "guardrail_terms_count": len(FORBIDDEN_PHRASES),
        "cases": case_results,
    }

    path = Path(output_path) if output_path else DEFAULT_RESULTS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    add_eval_result("report_eval", payload)
    try:
        payload["results_path"] = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        payload["results_path"] = str(path)
    return payload
