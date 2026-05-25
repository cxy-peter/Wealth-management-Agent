from __future__ import annotations

import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
HARNESS_RULES_PATH = ROOT / "config" / "harness_rules.yaml"

DEFAULT_FORBIDDEN = ["建议买入", "值得买", "推荐配置", "保证收益", "确定上涨", "买入", "卖出", "持有建议"]


class HarnessValidator:
    def __init__(self, rules_path: str | Path = HARNESS_RULES_PATH) -> None:
        self.rules_path = Path(rules_path)
        self.rules = self._load_rules()

    def _load_rules(self) -> dict[str, Any]:
        if not self.rules_path.exists():
            return {"forbidden_wording": DEFAULT_FORBIDDEN}
        text = self.rules_path.read_text(encoding="utf-8")
        forbidden = []
        in_forbidden = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("forbidden_wording:"):
                in_forbidden = True
                continue
            if in_forbidden and stripped.startswith("-"):
                forbidden.append(stripped[1:].strip().strip('"').strip("'"))
            elif stripped and not stripped.startswith("-"):
                in_forbidden = False
        return {"forbidden_wording": forbidden or DEFAULT_FORBIDDEN, "raw": text}

    def validate(self, output: dict[str, Any] | str, report_type: str = "weekly_report") -> dict[str, Any]:
        text = output if isinstance(output, str) else self._flatten_text(output)
        failed_rules: list[str] = []
        forbidden_hits = [phrase for phrase in self.rules.get("forbidden_wording", DEFAULT_FORBIDDEN) if phrase and phrase in text]
        if forbidden_hits:
            failed_rules.append("forbidden_wording")

        evidence_ids = []
        if isinstance(output, dict):
            evidence_ids = list(output.get("evidence_ids") or [])
            if output.get("evidence_id"):
                evidence_ids.append(output["evidence_id"])
        if not evidence_ids and "evidence_id=" not in text and re.search(r"\d+(?:\.\d+)?%|\d+(?:\.\d+)?\s*亿", text):
            failed_rules.append("required_evidence_rules")

        if "真实全市场" in text and ("synthetic" in text or "演示" in text or "mock" in text):
            failed_rules.append("source_boundary_rules")

        return {
            "pass": not failed_rules,
            "report_type": report_type,
            "failed_rules": failed_rules,
            "forbidden_hits": forbidden_hits,
            "evidence_ids": list(dict.fromkeys(str(item) for item in evidence_ids if item)),
            "source_boundary_check": "pass" if "source_boundary_rules" not in failed_rules else "fail",
        }

    @staticmethod
    def _flatten_text(value: Any) -> str:
        if isinstance(value, dict):
            return " ".join(HarnessValidator._flatten_text(item) for item in value.values())
        if isinstance(value, list):
            return " ".join(HarnessValidator._flatten_text(item) for item in value)
        return str(value)

