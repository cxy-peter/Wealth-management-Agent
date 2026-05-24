from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.weekly_report.parsers.weekly_snapshot_parser import list_report_dates, load_weekly_snapshot

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = ROOT / "data" / "dpo" / "weekly_report_preference_pairs.jsonl"


def build_weekly_dpo_pairs(limit: int = 32) -> list[dict[str, Any]]:
    report_date = list_report_dates()[-1]
    snapshot = load_weekly_snapshot(report_date).sort_values(["product_scale_bn", "product_code"], ascending=[False, True])
    pairs: list[dict[str, Any]] = []
    for index, row in enumerate(snapshot.head(limit).to_dict(orient="records"), 1):
        evidence_id = str(row["evidence_id"])
        pairs.append(
            {
                "id": f"dpo_weekly_generated_{index:03d}",
                "prompt": {
                    "task": "根据 tool outputs 生成资管产品周报摘要。",
                    "tool_output": {
                        "report_date": report_date,
                        "product_code": row["product_code"],
                        "product_name": row["product_name"],
                        "scale_wow_bn": row["scale_wow_bn"],
                        "return_3m": row["return_3m"],
                        "benchmark_status": row["benchmark_status"],
                        "max_drawdown": row["max_drawdown"],
                        "evidence_id": evidence_id,
                    },
                },
                "chosen": (
                    f"{row['product_name']} 本周规模变化 {float(row['scale_wow_bn']):.2f} 亿元，"
                    f"近 3 个月收益 {float(row['return_3m']) * 100:.2f}%，"
                    f"基准状态为 {row['benchmark_status']}，最大回撤 {float(row['max_drawdown']) * 100:.2f}%。"
                    f"周报口径下需同步观察规模变化、同类分位和风险事件，不作配置建议。 "
                    f"[evidence_id={evidence_id}]"
                ),
                "rejected": (
                    f"{row['product_name']} 本周表现较好，描述缺少数字来源和风险提示，"
                    "并把阶段性表现外推为未来表现。"
                ),
                "reject_reason": "缺少 evidence_id、风险提示不足，且存在未来表现外推。",
            }
        )
    return pairs


def write_weekly_dpo_pairs(path: str | Path = DEFAULT_OUTPUT, limit: int = 32) -> dict[str, Any]:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    pairs = build_weekly_dpo_pairs(limit=limit)
    with target.open("w", encoding="utf-8") as handle:
        for pair in pairs:
            handle.write(json.dumps(pair, ensure_ascii=False) + "\n")
    return {"output_path": str(target), "pair_count": len(pairs)}


if __name__ == "__main__":
    print(json.dumps(write_weekly_dpo_pairs(), ensure_ascii=False, indent=2))
