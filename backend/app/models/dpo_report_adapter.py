from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DPOReportMetadata:
    model_mode: str
    adapter_path: str
    base_model: str
    fallback_required: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DPOReportAdapter:
    def __init__(self, adapter_path: str | None = None, base_model: str | None = None) -> None:
        self.adapter_path = adapter_path or os.getenv("DPO_REPORT_ADAPTER_PATH", "")
        self.base_model = base_model or os.getenv("DPO_REPORT_BASE_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")
        available = bool(self.adapter_path and Path(self.adapter_path).exists())
        self.metadata = DPOReportMetadata(
            model_mode="dpo_adapter" if available else "template_fallback",
            adapter_path=self.adapter_path,
            base_model=self.base_model,
            fallback_required=not available,
            reason="adapter path found" if available else "adapter path missing; deterministic report template used",
        )

    def generate_report(self, tool_outputs: dict[str, Any], task_type: str = "weekly_product_summary") -> dict[str, Any]:
        evidence_id = tool_outputs.get("evidence_id") or "ev_missing"
        source_type = tool_outputs.get("source_type", "synthetic_weekly_snapshot")
        percentile_label = "模拟同业池分位" if source_type == "synthetic_weekly_snapshot" else "同业池分位"
        product_name = tool_outputs.get("product_name", tool_outputs.get("product_code", "样例产品"))
        text = (
            f"{product_name}用于{task_type}周报草稿：本周规模变化{float(tool_outputs.get('scale_wow_bn', 0)):.2f}亿元，"
            f"近3个月收益{float(tool_outputs.get('return_3m', 0)) * 100:.2f}%，最大回撤{float(tool_outputs.get('max_drawdown', 0)) * 100:.2f}%，"
            f"波动率{float(tool_outputs.get('volatility', 0)) * 100:.2f}%，基准状态为{tool_outputs.get('benchmark_status', 'unknown')}。"
            f"{percentile_label}与风险事件需在正式报告中同步展示；本段不输出投资建议或收益承诺。[evidence_id={evidence_id}]"
        )
        return {
            "model_mode": self.metadata.model_mode,
            "adapter_path": self.metadata.adapter_path,
            "base_model": self.metadata.base_model,
            "generated_text": text,
            "fallback_required": self.metadata.fallback_required,
        }
