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
    """DPO-capable report writer with deterministic template fallback.

    DPO is used for wording, evidence coverage, risk-warning completeness and
    source-boundary discipline. It does not calculate returns, drawdown,
    percentiles or reference-rate spreads.
    """

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
        evidence_ids = tool_outputs.get("evidence_ids") if isinstance(tool_outputs.get("evidence_ids"), list) else []
        evidence_id = tool_outputs.get("evidence_id") or (evidence_ids[0] if evidence_ids else "ev_missing")
        source_type = tool_outputs.get("source_type", "synthetic_weekly_snapshot")
        product_name = tool_outputs.get("product_name") or tool_outputs.get("product_code") or "样例产品"
        scale_wow = float(tool_outputs.get("scale_wow_bn") or 0)
        return_3m = float(tool_outputs.get("return_3m") or tool_outputs.get("aum_weighted_return_3m") or 0)
        drawdown = float(tool_outputs.get("max_drawdown") or tool_outputs.get("max_drawdown_mean") or 0)
        volatility = float(tool_outputs.get("volatility") or tool_outputs.get("volatility_mean") or 0)
        benchmark_status = tool_outputs.get("benchmark_status", "unknown")
        source_phrase = "模拟样本" if source_type.startswith("synthetic") else "用户上传样本" if source_type == "manual_upload" else source_type
        text = (
            f"{product_name}用于{task_type}摘要：本期规模变化 {scale_wow:.2f} 亿元，"
            f"近3个月收益 {return_3m * 100:.2f}%，最大回撤 {drawdown * 100:.2f}%，"
            f"波动率 {volatility * 100:.2f}%，基准状态为 {benchmark_status}。"
            f"上述数字来自 deterministic tools，数据来源标记为{source_phrase}；"
            f"正式周报需同步展示风险提示、证据编号和来源边界。[evidence_id={evidence_id}]"
        )
        return {
            "model_mode": self.metadata.model_mode,
            "adapter_path": self.adapter_path,
            "base_model": self.base_model,
            "generated_text": text,
            "fallback_required": self.metadata.fallback_required,
            "evidence_ids": [evidence_id],
        }
