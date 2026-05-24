"""Lightweight Qwen-compatible risk classifier adapter.

This module intentionally avoids torch, transformers, peft, local model
weights, API keys, and GPU-only code. It gives the rest of the application a
stable adapter interface while defaulting to a deterministic rule-based
fallback for CI, Vercel cold starts, and local demos.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class QwenAdapterMetadata:
    enabled: bool = False
    mode: str = "rule-based-fallback"
    base_model_path: str = ""
    adapter_path: str = ""
    reason: str = "lightweight demo adapter; no local model weights loaded"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class QwenRiskClassifier:
    """Rule-based classifier with the public shape of a model adapter."""

    HIGH_RISK_TERMS = {
        "违约",
        "逾期",
        "下调",
        "回撤",
        "流动性",
        "兑付",
        "监管",
        "诉讼",
        "减值",
        "信用利差",
        "信用利差走阔",
        "净值回撤",
        "估值波动",
        "波动",
        "踏线",
        "风险",
        # Keep compatibility with mojibake fixtures from early Windows edits.
        "杩濈害",
        "閫炬湡",
        "涓嬭皟",
        "鍥炴挙",
        "娴佸姩",
        "鍏戜粯",
        "鐩戠",
        "璇夎",
        "鍑忓",
        "淇＄敤鍒╁樊",
        "璧伴様",
        "娉㈠姩",
        "韪╃嚎",
    }
    POSITIVE_TERMS = {
        "修复",
        "改善",
        "回升",
        "企稳",
        "达标",
        "增厚",
        "淇",
        "鏀瑰杽",
        "鍥炲崌",
        "浼佺ǔ",
        "杈炬爣",
        "澧炲帤",
    }
    NEGATIVE_TERMS = {
        "承压",
        "走阔",
        "下跌",
        "回落",
        "不达标",
        "亏损",
        "风险",
        "鎵垮帇",
        "璧伴様",
        "涓嬭穼",
        "鍥炶惤",
        "涓嶈揪鏍",
        "浜忔崯",
        "椋庨櫓",
    }

    def __init__(
        self,
        base_model_path: str | None = None,
        adapter_path: str | None = None,
        device: str = "cpu",
    ) -> None:
        self.base_model_path = base_model_path or ""
        self.adapter_path = adapter_path or ""
        self.device = device
        self.metadata = QwenAdapterMetadata(
            base_model_path=self.base_model_path,
            adapter_path=self.adapter_path,
        )

    @staticmethod
    def _count_terms(text: str, terms: set[str]) -> int:
        return sum(1 for term in terms if term in text)

    def predict(self, text: str, symbol: str = "") -> dict[str, Any]:
        normalized = re.sub(r"\s+", " ", str(text or "")).strip()
        high_risk_hits = self._count_terms(normalized, self.HIGH_RISK_TERMS)
        positive_hits = self._count_terms(normalized, self.POSITIVE_TERMS)
        negative_hits = self._count_terms(normalized, self.NEGATIVE_TERMS)

        risk_score = max(1, min(5, 2 + high_risk_hits + (1 if negative_hits >= 2 else 0)))
        sentiment_score = max(1, min(5, 3 + positive_hits - negative_hits))
        if not normalized:
            risk_score = 2
            sentiment_score = 3

        return {
            "sentiment_score": sentiment_score,
            "risk_score": risk_score,
            "raw_output": {
                "matched_high_risk_terms": sorted(term for term in self.HIGH_RISK_TERMS if term in normalized),
                "matched_positive_terms": sorted(term for term in self.POSITIVE_TERMS if term in normalized),
                "matched_negative_terms": sorted(term for term in self.NEGATIVE_TERMS if term in normalized),
                "symbol": symbol,
            },
            "model_mode": self.metadata.mode,
            "fallback_required": True,
        }
