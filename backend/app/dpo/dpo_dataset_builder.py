from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.dpo.hard_negative_generator import HARD_NEGATIVE_TYPES, make_hard_negative
from backend.app.weekly_report.parsers.weekly_snapshot_parser import list_report_dates, load_weekly_snapshot

ROOT = Path(__file__).resolve().parents[3]
DPO_DIR = ROOT / "data" / "dpo"
LEGACY_OUTPUT = DPO_DIR / "weekly_report_preference_pairs.jsonl"
PLANNER_OUTPUT = DPO_DIR / "planner_preference_pairs.jsonl"
REPORT_OUTPUT = DPO_DIR / "report_preference_pairs.jsonl"
EVAL_CASES_OUTPUT = DPO_DIR / "dpo_eval_cases.jsonl"
RULES_OUTPUT = DPO_DIR / "hard_negative_rules.yaml"


TASK_TYPES = [
    "weekly_product_summary",
    "peer_benchmark_report",
    "market_percentile_report",
    "channel_benchmark_report",
    "top_peer_tracking",
    "risk_summary",
]


def _latest_snapshot(limit: int = 40) -> list[dict[str, Any]]:
    dates = list_report_dates()
    if not dates:
        return []
    frame = load_weekly_snapshot(dates[-1]).sort_values(["product_scale_bn", "product_code"], ascending=[False, True])
    return frame.head(limit).to_dict(orient="records")


def _tool_output(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "report_date": str(row["report_date"])[:10],
        "product_code": row["product_code"],
        "product_name": row["product_name"],
        "product_type": row["product_type"],
        "channel": row["channel"],
        "risk_level": row["risk_level"],
        "scale_wow_bn": round(float(row["scale_wow_bn"]), 4),
        "scale_mom_bn": round(float(row["scale_mom_bn"]), 4),
        "return_3m": round(float(row["return_3m"]), 6),
        "max_drawdown": round(float(row["max_drawdown"]), 6),
        "volatility": round(float(row["volatility"]), 6),
        "sharpe": round(float(row["sharpe"]), 6),
        "benchmark_status": row["benchmark_status"],
        "return_percentile": 0.32 if row["benchmark_status"] == "below_lower" else 0.68,
        "source_type": row.get("source_type", "synthetic_weekly_snapshot"),
        "evidence_id": row["evidence_id"],
    }


def _chosen_report(row: dict[str, Any], task_type: str) -> str:
    tool = _tool_output(row)
    risk_line = "基准低于下限或同类分位偏低，后续周报需跟踪回撤、波动和规模变化。" if tool["benchmark_status"] == "below_lower" else "需持续跟踪回撤、波动和基准状态，避免把阶段性表现外推为未来收益。"
    scope = "模拟同业池分位" if tool["source_type"] == "synthetic_weekly_snapshot" else "同业池分位"
    return (
        f"{tool['product_name']}本周规模变化{tool['scale_wow_bn']:.2f}亿元，较上月变化{tool['scale_mom_bn']:.2f}亿元；"
        f"近3个月收益{tool['return_3m'] * 100:.2f}%，最大回撤{tool['max_drawdown'] * 100:.2f}%，波动率{tool['volatility'] * 100:.2f}%，"
        f"基准状态为{tool['benchmark_status']}，{scope}约{tool['return_percentile'] * 100:.0f}分位。"
        f"{risk_line}本段仅用于{task_type}的投研辅助和周报草稿，不构成投资建议。[evidence_id={tool['evidence_id']}]"
    )


def build_report_pairs(limit: int = 36) -> list[dict[str, Any]]:
    rows = _latest_snapshot(limit)
    pairs: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        task_type = TASK_TYPES[index % len(TASK_TYPES)]
        tool = _tool_output(row)
        chosen = _chosen_report(row, task_type)
        negative_type = HARD_NEGATIVE_TYPES[index % len(HARD_NEGATIVE_TYPES)]
        pairs.append(
            {
                "id": f"report_dpo_{index:03d}",
                "task_type": task_type,
                "prompt": {
                    "instruction": "基于 tool outputs 生成资管产品周报、竞品对标或渠道对标摘要。",
                    "tool_outputs": tool,
                },
                "chosen": chosen,
                "rejected": make_hard_negative(chosen, tool, negative_type),
                "rubric": {
                    "numeric_consistency": 1,
                    "evidence_coverage": 1,
                    "risk_warning": 1,
                    "forbidden_advice": 0,
                    "business_style": 1,
                    "source_boundary": 1,
                },
                "hard_negative_type": negative_type,
                "reject_reason": negative_type,
            }
        )
    return pairs


def build_planner_pairs(limit: int = 24) -> list[dict[str, Any]]:
    rows = _latest_snapshot(limit)
    tools = [
        "load_weekly_snapshot",
        "calculate_weekly_return_metrics",
        "calculate_percentile_metrics",
        "peer_benchmark",
        "channel_benchmark",
        "weekly_report_verifier",
        "guardrail_check",
    ]
    pairs: list[dict[str, Any]] = []
    for index, row in enumerate(rows, 1):
        task_type = TASK_TYPES[index % len(TASK_TYPES)]
        product_context = _tool_output(row)
        is_channel = task_type == "channel_benchmark_report"
        is_risk = task_type == "risk_summary" or product_context["benchmark_status"] == "below_lower"
        required_tools = ["load_weekly_snapshot", "calculate_weekly_return_metrics", "weekly_report_verifier", "guardrail_check"]
        if task_type in {"peer_benchmark_report", "top_peer_tracking"}:
            required_tools.append("peer_benchmark")
        if is_channel:
            required_tools.append("channel_benchmark")
        if task_type == "market_percentile_report":
            required_tools.append("calculate_percentile_metrics")
        if is_risk:
            required_tools.append("classify_risk_events")
        pairs.append(
            {
                "id": f"planner_dpo_{index:03d}",
                "task_type": task_type,
                "prompt": {
                    "user_task": f"请生成{task_type}，产品代码{product_context['product_code']}，并保留证据链。",
                    "product_context": product_context,
                    "available_tools": tools,
                    "data_source_status": {
                        "synthetic_weekly_snapshot": "available",
                        "official_disclosure_sample": "sample_only",
                        "public_market_report": "available",
                    },
                },
                "chosen": {
                    "plan_type": "channel_benchmark" if is_channel else task_type,
                    "steps": [
                        "读取周报快照和数据源元信息",
                        "调用必要指标和对标工具",
                        "写入 evidence_id/tool_call_id",
                        "进入 verifier 与 guardrail",
                    ],
                    "required_tools": sorted(set(required_tools)),
                    "required_evidence": ["evidence_id", "tool_call_id", "source_type"],
                    "verifier_required": True,
                    "guardrail_required": True,
                },
                "rejected": {
                    "plan_type": "generic_research",
                    "steps": ["泛化描述产品表现"],
                    "required_tools": ["load_weekly_snapshot"],
                    "required_evidence": [],
                    "verifier_required": False,
                    "guardrail_required": False,
                },
                "reject_reason": "missing task-specific tools, evidence, verifier, or guardrail",
            }
        )
    return pairs


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_rules() -> None:
    RULES_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    RULES_OUTPUT.write_text(
        "\n".join(
            [
                "hard_negative_rules:",
                "  numeric_hallucination: 篡改收益率、分位数、回撤或规模变化",
                "  percentile_misinterpretation: 把低分位写成表现领先或误读回撤分位",
                "  missing_evidence: 删除 evidence_id 或 tool_call_id",
                "  compliance_violation: 加入投资建议、收益承诺或确定性判断",
                "  missing_risk: 只写收益不写回撤、波动、基准或风险提示",
                "  task_mismatch: 对标维度与用户任务不一致",
                "  source_overclaim: 把 synthetic/mock 数据写成真实全市场数据",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def build_all_dpo_datasets(report_limit: int = 36, planner_limit: int = 24) -> dict[str, Any]:
    report_pairs = build_report_pairs(report_limit)
    planner_pairs = build_planner_pairs(planner_limit)
    legacy_pairs = [
        {
            "id": row["id"].replace("report_dpo", "dpo_weekly_generated"),
            "prompt": {"task": row["prompt"]["instruction"], "tool_output": row["prompt"]["tool_outputs"]},
            "chosen": row["chosen"],
            "rejected": row["rejected"],
            "reject_reason": row["reject_reason"],
        }
        for row in report_pairs
    ]
    eval_cases = [
        {
            "id": row["id"].replace("report_dpo", "dpo_eval"),
            "task_type": row["task_type"],
            "tool_outputs": row["prompt"]["tool_outputs"],
            "expected_checks": row["rubric"],
            "hard_negative_type": row["hard_negative_type"],
        }
        for row in report_pairs[:24]
    ]
    _write_jsonl(REPORT_OUTPUT, report_pairs)
    _write_jsonl(PLANNER_OUTPUT, planner_pairs)
    _write_jsonl(LEGACY_OUTPUT, legacy_pairs)
    _write_jsonl(EVAL_CASES_OUTPUT, eval_cases)
    _write_rules()
    return {
        "report_pairs": len(report_pairs),
        "planner_pairs": len(planner_pairs),
        "legacy_pairs": len(legacy_pairs),
        "eval_cases": len(eval_cases),
        "outputs": {
            "report": str(REPORT_OUTPUT),
            "planner": str(PLANNER_OUTPUT),
            "legacy": str(LEGACY_OUTPUT),
            "eval_cases": str(EVAL_CASES_OUTPUT),
            "rules": str(RULES_OUTPUT),
        },
    }


def write_weekly_dpo_pairs(path: str | Path = LEGACY_OUTPUT, limit: int = 32) -> dict[str, Any]:
    result = build_all_dpo_datasets(report_limit=limit, planner_limit=min(24, limit))
    return {"output_path": str(path), "pair_count": result["legacy_pairs"], "all_outputs": result["outputs"]}


if __name__ == "__main__":
    print(json.dumps(build_all_dpo_datasets(), ensure_ascii=False, indent=2))
