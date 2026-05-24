"""Deterministic news sentiment/risk tagging for the MVP.

This is deliberately simple. It gives Codex a safe baseline that can later be
replaced by a Qwen LoRA/QLoRA classifier while preserving the same output schema.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from backend.app.utils.pandas_runtime import disable_optional_pandas_accelerators

disable_optional_pandas_accelerators()

import pandas as pd

POSITIVE_KEYWORDS = ["改善", "回暖", "分红", "稳健", "增长", "盈利", "回报", "创新"]
NEGATIVE_KEYWORDS = ["监管", "压力", "分化", "下滑", "处罚", "违约", "召回", "亏损", "风险"]
HIGH_RISK_KEYWORDS = ["监管", "处罚", "违约", "召回", "亏损", "价格", "库存"]


@dataclass(frozen=True)
class NewsSignal:
    date: str
    title: str
    sentiment_score: int
    risk_score: int
    evidence: str
    model_mode: str = "rule-based-fallback"

    def to_dict(self) -> dict:
        return asdict(self)


def score_text(text: str) -> tuple[int, int, str]:
    text = text or ""
    pos = sum(kw in text for kw in POSITIVE_KEYWORDS)
    neg = sum(kw in text for kw in NEGATIVE_KEYWORDS)
    high_risk = sum(kw in text for kw in HIGH_RISK_KEYWORDS)

    if pos > neg:
        sentiment = 4 if pos == 1 else 5
    elif neg > pos:
        sentiment = 2 if neg == 1 else 1
    else:
        sentiment = 3

    if high_risk >= 2:
        risk = 4
    elif high_risk == 1 or neg >= 2:
        risk = 3
    else:
        risk = 2

    evidence = f"positive_hits={pos}; negative_hits={neg}; high_risk_hits={high_risk}"
    return sentiment, risk, evidence


def analyze_news(news_df: pd.DataFrame, classifier: Any | None = None, symbol: str = "") -> list[NewsSignal]:
    signals: list[NewsSignal] = []
    for _, row in news_df.iterrows():
        text = f"{row.get('title', '')} {row.get('summary', '')}"
        model_mode = "rule-based-fallback"
        if classifier is not None:
            prediction = classifier.predict(text, symbol=symbol)
            model_mode = str(prediction.get("model_mode") or model_mode)
            if not prediction.get("fallback_required") and prediction.get("sentiment_score") is not None:
                sentiment = int(prediction["sentiment_score"])
                risk = int(prediction["risk_score"])
                evidence = f"qwen_adapter={model_mode}; parsed_output=true"
            else:
                sentiment, risk, evidence = score_text(text)
                evidence = f"{evidence}; qwen_adapter={model_mode}; fallback=true"
        else:
            sentiment, risk, evidence = score_text(text)
        signals.append(
            NewsSignal(
                date=str(row["date"])[:10],
                title=str(row.get("title", "")),
                sentiment_score=sentiment,
                risk_score=risk,
                evidence=evidence,
                model_mode=model_mode,
            )
        )
    return signals


def summarize_news(signals: list[NewsSignal]) -> dict:
    if not signals:
        return {
            "avg_sentiment": 3.0,
            "avg_risk": 2.0,
            "top_risks": [],
            "signal_count": 0,
        }
    avg_sentiment = sum(s.sentiment_score for s in signals) / len(signals)
    avg_risk = sum(s.risk_score for s in signals) / len(signals)
    top_risks = [s.title for s in sorted(signals, key=lambda x: x.risk_score, reverse=True)[:3]]
    return {
        "avg_sentiment": round(avg_sentiment, 2),
        "avg_risk": round(avg_risk, 2),
        "top_risks": top_risks,
        "signal_count": len(signals),
    }
