from __future__ import annotations

import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
HARNESS_RULES_PATH = ROOT / "config" / "harness_rules.yaml"

DEFAULT_FORBIDDEN = [
    "建议买入",
    "值得买",
    "推荐配置",
    "保证收益",
    "确定上涨",
    "收益稳定可期",
    "买入",
    "卖出",
    "持有建议",
    # Backward-compatible mojibake tokens from older fixtures.
    "寤鸿涔板叆",
    "鎺ㄨ崘閰嶇疆",
    "淇濊瘉鏀剁泭",
    "纭畾涓婃定",
    "涔板叆",
    "鍗栧嚭",
]

DEFAULT_REQUIRED_FIELDS = {
    "weekly_report": ["product_count", "total_scale_bn", "benchmark_pass_rate", "attention_count"],
    "weekly_product_summary": ["product_count", "total_scale_bn", "benchmark_pass_rate", "attention_count"],
    "peer_benchmark": ["product_code", "peer_count", "market_percentile"],
}

FIELD_ALIASES = {
    "total_scale": ["total_scale", "total_scale_bn", "kpis.total_scale_bn"],
    "total_scale_bn": ["total_scale_bn", "kpis.total_scale_bn"],
    "benchmark_pass_rate": ["benchmark_pass_rate", "kpis.benchmark_pass_rate"],
    "attention_count": ["attention_count", "attention_product_count", "kpis.attention_product_count"],
    "market_percentile": ["market_percentile", "percentile.market_percentile", "percentile.percentile"],
}

NUMERIC_CLAIM_PATTERN = re.compile(r"\d+(?:\.\d+)?\s*(?:%|bp|bps|亿元|亿|天|days?)")
NUMERIC_KEYWORDS = [
    "return",
    "drawdown",
    "percentile",
    "收益",
    "回撤",
    "分位",
    "波动",
    "规模",
    "鐢熸垚",
    "鏀剁泭",
    "鍥炴挙",
]


class HarnessValidator:
    def __init__(self, rules_path: str | Path = HARNESS_RULES_PATH) -> None:
        self.rules_path = Path(rules_path)
        self.rules = self._load_rules()

    def _load_rules(self) -> dict[str, Any]:
        if not self.rules_path.exists():
            return {"forbidden_wording": DEFAULT_FORBIDDEN, "required_fields_by_report_type": DEFAULT_REQUIRED_FIELDS}
        text = self.rules_path.read_text(encoding="utf-8")
        forbidden = self._parse_list(text, "forbidden_wording") or DEFAULT_FORBIDDEN
        required = self._parse_required_fields(text) or DEFAULT_REQUIRED_FIELDS
        return {"forbidden_wording": forbidden, "required_fields_by_report_type": required, "raw": text}

    @staticmethod
    def _parse_list(text: str, section: str) -> list[str]:
        values: list[str] = []
        in_section = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith(f"{section}:"):
                in_section = True
                continue
            if in_section and stripped.startswith("-"):
                values.append(stripped[1:].strip().strip('"').strip("'"))
            elif in_section and stripped and not stripped.startswith("-"):
                break
        return values

    @staticmethod
    def _parse_required_fields(text: str) -> dict[str, list[str]]:
        required: dict[str, list[str]] = {}
        in_section = False
        current_report_type: str | None = None
        for line in text.splitlines():
            if line.strip().startswith("required_fields_by_report_type:"):
                in_section = True
                continue
            if not in_section:
                continue
            if line and not line.startswith(" ") and not line.startswith("\t"):
                break
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.endswith(":") and not stripped.startswith("-"):
                current_report_type = stripped[:-1]
                required[current_report_type] = []
            elif stripped.startswith("-") and current_report_type:
                required[current_report_type].append(stripped[1:].strip().strip('"').strip("'"))
        return required

    def validate(
        self,
        output: dict[str, Any] | str,
        report_type: str = "weekly_report",
        *,
        tool_outputs: dict[str, Any] | None = None,
        skill_name: str | None = None,
        source_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        tool_outputs = tool_outputs or {}
        source_context = source_context or {}
        text = output if isinstance(output, str) else self._flatten_text(output)
        failed_rules: list[str] = []

        forbidden_hits = [phrase for phrase in self.rules.get("forbidden_wording", DEFAULT_FORBIDDEN) if phrase and phrase in text]
        if forbidden_hits:
            failed_rules.append("forbidden_wording")

        evidence_ids = self._collect_evidence_ids(output)
        evidence_ids.extend(self._collect_evidence_ids(tool_outputs))
        if source_context.get("evidence_id"):
            evidence_ids.append(str(source_context["evidence_id"]))
        evidence_ids = list(dict.fromkeys(str(item) for item in evidence_ids if item))

        if self._has_numeric_claim(text) and not evidence_ids and "evidence_id=" not in text and "tool_call_id=" not in text:
            failed_rules.append("required_evidence_rules")

        if self._needs_required_fields_check(output, skill_name):
            missing_fields = self._missing_required_fields(output, report_type)
            if missing_fields:
                failed_rules.append("required_fields_by_report_type")
        else:
            missing_fields = []

        if self._has_metric_claim(text) and not self._metric_claim_is_grounded(output, tool_outputs, evidence_ids):
            failed_rules.append("numeric_consistency_rules")

        if self._violates_source_boundary(text, output, source_context):
            failed_rules.append("source_boundary_rules")

        failed_rules = list(dict.fromkeys(failed_rules))
        return {
            "pass": not failed_rules,
            "report_type": report_type,
            "failed_rules": failed_rules,
            "forbidden_hits": forbidden_hits,
            "missing_required_fields": missing_fields,
            "evidence_ids": evidence_ids,
            "source_boundary_check": "pass" if "source_boundary_rules" not in failed_rules else "fail",
            "numeric_consistency_check": "pass" if "numeric_consistency_rules" not in failed_rules else "fail",
        }

    def _missing_required_fields(self, output: dict[str, Any] | str, report_type: str) -> list[str]:
        if not isinstance(output, dict):
            return []
        required = self.rules.get("required_fields_by_report_type", DEFAULT_REQUIRED_FIELDS).get(report_type, [])
        return [field for field in required if not self._has_field(output, field)]

    @staticmethod
    def _needs_required_fields_check(output: dict[str, Any] | str, skill_name: str | None) -> bool:
        if not isinstance(output, dict):
            return False
        if skill_name is None:
            return True
        return skill_name == "weekly_summary_skill"

    @staticmethod
    def _has_field(output: dict[str, Any], field: str) -> bool:
        candidates = FIELD_ALIASES.get(field, [field])
        return any(HarnessValidator._get_path(output, candidate) is not None for candidate in candidates)

    @staticmethod
    def _get_path(value: dict[str, Any], path: str) -> Any:
        current: Any = value
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
        return current

    @staticmethod
    def _collect_evidence_ids(value: Any) -> list[str]:
        ids: list[str] = []
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"evidence_id", "source_tool_call_id", "tool_call_id"} and item:
                    ids.append(str(item))
                elif key == "evidence_ids" and isinstance(item, list):
                    ids.extend(str(element) for element in item if element)
                else:
                    ids.extend(HarnessValidator._collect_evidence_ids(item))
        elif isinstance(value, list):
            for item in value:
                ids.extend(HarnessValidator._collect_evidence_ids(item))
        return ids

    @staticmethod
    def _has_numeric_claim(text: str) -> bool:
        return bool(NUMERIC_CLAIM_PATTERN.search(text))

    @staticmethod
    def _has_metric_claim(text: str) -> bool:
        lowered = text.lower()
        return bool(NUMERIC_CLAIM_PATTERN.search(text)) and any(keyword.lower() in lowered for keyword in NUMERIC_KEYWORDS)

    @staticmethod
    def _metric_claim_is_grounded(output: Any, tool_outputs: dict[str, Any], evidence_ids: list[str]) -> bool:
        if evidence_ids:
            return True
        return bool(HarnessValidator._collect_evidence_ids(output) or HarnessValidator._collect_evidence_ids(tool_outputs))

    @staticmethod
    def _violates_source_boundary(text: str, output: Any, source_context: dict[str, Any]) -> bool:
        flattened = text.lower()
        source_types = set(str(item) for item in source_context.get("source_types", []))
        if isinstance(output, dict):
            if output.get("source_type"):
                source_types.add(str(output["source_type"]))
            for source in output.get("sources", []) if isinstance(output.get("sources"), list) else []:
                if isinstance(source, dict) and source.get("source_type"):
                    source_types.add(str(source["source_type"]))
        has_synthetic = any(source.startswith("synthetic") for source in source_types) or "synthetic" in flattened or "演示数据" in text
        real_market_claim = any(
            phrase in text
            for phrase in ["真实全市场排名", "真实全市场分位", "覆盖真实全市场", "已完成官网实时验证"]
        )
        return bool(has_synthetic and real_market_claim)

    @staticmethod
    def _flatten_text(value: Any) -> str:
        if isinstance(value, dict):
            return " ".join(HarnessValidator._flatten_text(item) for item in value.values())
        if isinstance(value, list):
            return " ".join(HarnessValidator._flatten_text(item) for item in value)
        return str(value)
