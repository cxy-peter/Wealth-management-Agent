"""News-risk analysis node with Qwen adapter fallback."""
from __future__ import annotations

from typing import Any

from backend.app.models.qwen_risk_adapter import QwenRiskClassifier
from backend.app.tools.news_risk import analyze_news, summarize_news


def news_risk_agent(state: dict[str, Any]) -> dict[str, Any]:
    request = state["request"]
    classifier = QwenRiskClassifier()
    signals = analyze_news(state["news_df"], classifier=classifier, symbol=request["symbol"])
    summary = summarize_news(signals)

    tool_calls = list(state.get("tool_calls", []))
    tool_calls.append(
        {
            "tool": "news_risk_classifier",
            "agent": "news_risk_agent",
            "success": True,
            "rows": int(len(signals)),
            "mode": classifier.metadata.mode,
        }
    )

    return {
        **state,
        "news_signals": [item.to_dict() for item in signals],
        "news_summary": summary,
        "model_metadata": {"qwen_risk_adapter": classifier.metadata.to_dict()},
        "tool_calls": tool_calls,
    }
