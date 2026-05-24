from __future__ import annotations

import json
import re
from pathlib import Path
from statistics import mean
from typing import Any

from backend.app.dpo.dpo_dataset_builder import EVAL_CASES_OUTPUT, build_all_dpo_datasets
from backend.app.models.dpo_report_adapter import DPOReportAdapter

ROOT = Path(__file__).resolve().parents[3]
RESULT_PATH = ROOT / "eval" / "dpo_agent_eval_results.json"
FORBIDDEN = ["建议买入", "建议卖出", "建议持有", "推荐配置", "保证收益", "收益稳定可期", "确定上涨"]


def _load_cases() -> list[dict[str, Any]]:
    if not EVAL_CASES_OUTPUT.exists():
        build_all_dpo_datasets()
    rows: list[dict[str, Any]] = []
    with EVAL_CASES_OUTPUT.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _template_output(tool: dict[str, Any]) -> str:
    return f"{tool.get('product_name', '产品')}近3个月收益{float(tool.get('return_3m', 0)) * 100:.2f}%，基准状态{tool.get('benchmark_status')}。[evidence_id={tool.get('evidence_id')}]"


def _base_output(tool: dict[str, Any]) -> str:
    return f"{tool.get('product_name', '产品')}表现较好，可继续观察。"


def _score(text: str, tool: dict[str, Any]) -> dict[str, float]:
    evidence = str(tool.get("evidence_id", ""))
    expected_return = f"{float(tool.get('return_3m', 0)) * 100:.2f}%"
    expected_drawdown = f"{float(tool.get('max_drawdown', 0)) * 100:.2f}%"
    numeric = expected_return in text and expected_drawdown in text
    evidence_ok = bool(evidence and evidence in text)
    forbidden = any(term in text for term in FORBIDDEN)
    risk = bool(re.search(r"回撤|波动|风险|基准", text))
    percentile = "模拟同业池分位" in text if tool.get("source_type") == "synthetic_weekly_snapshot" else "分位" in text
    source = "真实全市场" not in text and "官网实时" not in text
    verifier = numeric and evidence_ok and not forbidden and risk and source
    score = mean([numeric, evidence_ok, not forbidden, risk, percentile, source, verifier])
    return {
        "numeric_consistency": float(numeric),
        "evidence_coverage": float(evidence_ok),
        "forbidden_wording": float(forbidden),
        "risk_warning": float(risk),
        "percentile_accuracy": float(percentile),
        "source_boundary": float(source),
        "verifier_pass": float(verifier),
        "report_score": round(score, 4),
    }


def _evaluate_variant(name: str, cases: list[dict[str, Any]], adapter: DPOReportAdapter | None = None) -> dict[str, Any]:
    rows = []
    for case in cases:
        tool = case["tool_outputs"]
        if name == "template_baseline":
            text = _template_output(tool)
        elif name == "sft_adapter_or_base":
            text = _base_output(tool)
        else:
            text = adapter.generate_report(tool, case["task_type"])["generated_text"] if adapter else _template_output(tool)
        score = _score(text, tool)
        rows.append({"case_id": case["id"], "output": text, **score})
    return {
        "numeric_consistency_rate": round(mean(row["numeric_consistency"] for row in rows), 4),
        "evidence_coverage_rate": round(mean(row["evidence_coverage"] for row in rows), 4),
        "forbidden_wording_rate": round(mean(row["forbidden_wording"] for row in rows), 4),
        "risk_warning_coverage": round(mean(row["risk_warning"] for row in rows), 4),
        "percentile_interpretation_accuracy": round(mean(row["percentile_accuracy"] for row in rows), 4),
        "source_boundary_accuracy": round(mean(row["source_boundary"] for row in rows), 4),
        "verifier_pass_rate": round(mean(row["verifier_pass"] for row in rows), 4),
        "average_report_score": round(mean(row["report_score"] for row in rows), 4),
        "per_case_results": rows[:12],
    }


def run_eval() -> dict[str, Any]:
    cases = _load_cases()
    adapter = DPOReportAdapter()
    variants = {
        "template_baseline": _evaluate_variant("template_baseline", cases),
        "sft_adapter_or_base": _evaluate_variant("sft_adapter_or_base", cases),
        "dpo_adapter": _evaluate_variant("dpo_adapter", cases, adapter),
    }
    baseline = variants["template_baseline"]["average_report_score"]
    dpo_score = variants["dpo_adapter"]["average_report_score"]
    variants["dpo_adapter"]["preference_win_rate_vs_baseline"] = 1.0 if dpo_score >= baseline else 0.0
    payload = {
        "training_status": "not_trained" if adapter.metadata.fallback_required else "adapter_available",
        "adapter_available": not adapter.metadata.fallback_required,
        "case_count": len(cases),
        "variants": variants,
    }
    RESULT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    print(json.dumps(run_eval(), ensure_ascii=False, indent=2))
