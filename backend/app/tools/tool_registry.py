"""Auditable local tool registry.

All default tools use sample/mock data from ``data/`` and return a common trace
shape. Optional live-data adapters can wrap the same registry contract later.
"""
from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any

from backend.app.utils.pandas_runtime import disable_optional_pandas_accelerators

disable_optional_pandas_accelerators()

import numpy as np
import pandas as pd

from backend.app.agents.valuation_agent import evaluate_valuation
from backend.app.tools.data_loader import load_fundamentals, load_nav, load_news as load_news_df, load_products
from backend.app.tools.metrics import compute_metrics, technical_snapshot
from backend.app.tools.news_risk import analyze_news, summarize_news
from backend.app.tools.product_benchmark import peer_summary


@dataclass(frozen=True)
class ToolCallRecord:
    tool_call_id: str
    tool_name: str
    input_args: dict[str, Any]
    output: Any
    evidence_ids: list[str]
    latency_ms: float
    success: bool
    error_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _tool_call_id(tool_name: str) -> str:
    return f"tc_{tool_name}_{uuid.uuid4().hex[:10]}"


def _jsonable(value: Any) -> Any:
    if isinstance(value, pd.DataFrame):
        return _jsonable(value.to_dict(orient="records"))
    if isinstance(value, pd.Series):
        return _jsonable(value.to_dict())
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.ndarray,)):
        return _jsonable(value.tolist())
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    frame = df.copy()
    for column in frame.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
        frame[column] = frame[column].dt.strftime("%Y-%m-%d")
    return _jsonable(frame.to_dict(orient="records"))


def _evidence(prefix: str, *parts: Any) -> str:
    safe = "_".join(str(part).replace(" ", "-") for part in parts if part is not None and str(part) != "")
    return f"ev_{prefix}_{safe}" if safe else f"ev_{prefix}"


def load_price_series(symbol: str) -> dict[str, Any]:
    df = load_nav(symbol)
    records = _records(df)
    return {
        "symbol": symbol,
        "records": records,
        "row_count": len(records),
        "value_column": "close",
    }


def calculate_metrics(symbol: str, price_records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if price_records is None:
        df = load_nav(symbol)
    else:
        df = pd.DataFrame(price_records)
    metrics = compute_metrics(df, symbol, value_col="close").to_dict()
    technical = technical_snapshot(df, symbol, value_col="close")
    return {
        "symbol": symbol,
        "metrics": _jsonable(metrics),
        "technical": _jsonable(technical),
        "source_tool": "calculate_metrics",
    }


def load_fundamental_snapshot(symbol: str) -> dict[str, Any]:
    df = load_fundamentals(symbol)
    if df.empty:
        return {"symbol": symbol, "available": False, "snapshot": {}}
    records = _records(df.tail(1))
    return {"symbol": symbol, "available": True, "snapshot": records[0]}


def load_valuation_snapshot(symbol: str) -> dict[str, Any]:
    df = load_fundamentals(symbol)
    return {"symbol": symbol, "valuation": _jsonable(evaluate_valuation(df))}


def load_news(symbol: str) -> dict[str, Any]:
    df = load_news_df(symbol)
    records = _records(df)
    return {"symbol": symbol, "records": records, "row_count": len(records)}


def _qwen_risk_classifier() -> Any:
    try:
        from backend.app.models.qwen_risk_adapter import QwenRiskClassifier

        return QwenRiskClassifier()
    except Exception as exc:  # pragma: no cover - import guard for optional runtime packaging
        error_type = exc.__class__.__name__

        class _FallbackClassifier:
            metadata = type(
                "Metadata",
                (),
                {"to_dict": lambda self: {"enabled": False, "mode": "rule-based-fallback", "reason": error_type}},
            )()

            def predict(self, text: str, symbol: str = "") -> dict[str, Any]:
                risk = 4 if any(term in str(text) for term in ["违约", "回撤", "风险", "监管"]) else 2
                return {
                    "sentiment_score": 3,
                    "risk_score": risk,
                    "raw_output": {"symbol": symbol, "fallback_error": error_type},
                    "model_mode": "rule-based-fallback",
                    "fallback_required": True,
                }

        return _FallbackClassifier()


def classify_news_risk(symbol: str, news_records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    df = pd.DataFrame(news_records) if news_records is not None else load_news_df(symbol)
    classifier = _qwen_risk_classifier()
    signals = analyze_news(df, classifier=classifier, symbol=symbol)
    return {
        "symbol": symbol,
        "signals": [signal.to_dict() for signal in signals],
        "summary": summarize_news(signals),
        "model_metadata": {"qwen_risk_adapter": classifier.metadata.to_dict()},
    }


def product_benchmark(
    asset_class: str | None = None,
    risk_level: str | None = None,
    channel: str | None = None,
    duration_bucket: str | None = None,
    liquidity_type: str | None = None,
    strategy_type: str | None = None,
) -> dict[str, Any]:
    filters = {
        key: value
        for key, value in {
            "asset_class": asset_class,
            "risk_level": risk_level,
            "channel": channel,
            "duration_bucket": duration_bucket,
            "liquidity_type": liquidity_type,
            "strategy_type": strategy_type,
        }.items()
        if value
    }
    return peer_summary(load_products(), filters=filters)


TOOL_REGISTRY: dict[str, Callable[..., dict[str, Any]]] = {
    "load_price_series": load_price_series,
    "calculate_metrics": calculate_metrics,
    "load_fundamental_snapshot": load_fundamental_snapshot,
    "load_valuation_snapshot": load_valuation_snapshot,
    "load_news": load_news,
    "classify_news_risk": classify_news_risk,
    "product_benchmark": product_benchmark,
}


def evidence_ids_for(tool_name: str, input_args: dict[str, Any], output: Any) -> list[str]:
    symbol = input_args.get("symbol")
    if tool_name == "load_price_series":
        return [_evidence("sample_nav", symbol, output.get("row_count"))]
    if tool_name == "calculate_metrics":
        return [_evidence("metrics", symbol)]
    if tool_name == "load_fundamental_snapshot":
        return [_evidence("fundamental", symbol)]
    if tool_name == "load_valuation_snapshot":
        return [_evidence("valuation", symbol)]
    if tool_name == "load_news":
        return [_evidence("sample_news", symbol, output.get("row_count"))]
    if tool_name == "classify_news_risk":
        return [_evidence("news_risk", symbol, len(output.get("signals", [])))]
    if tool_name == "product_benchmark":
        return [_evidence("product_benchmark", output.get("product_count", 0))]
    return [_evidence(tool_name, symbol)]


def _attach_source_tool_call_id(tool_name: str, output: Any, call_id: str) -> Any:
    if tool_name != "product_benchmark" or not isinstance(output, dict):
        return output
    for row in output.get("table", []):
        if isinstance(row, dict):
            row["source_tool_call_id"] = call_id
    output["source_tool_call_id"] = call_id
    return output


def execute_tool(tool_name: str, **input_args: Any) -> dict[str, Any]:
    started = time.perf_counter()
    call_id = _tool_call_id(tool_name)
    if tool_name not in TOOL_REGISTRY:
        return ToolCallRecord(
            tool_call_id=call_id,
            tool_name=tool_name,
            input_args=_jsonable(input_args),
            output={},
            evidence_ids=[],
            latency_ms=0.0,
            success=False,
            error_type="UnknownTool",
        ).to_dict()

    try:
        output = TOOL_REGISTRY[tool_name](**input_args)
        output = _jsonable(output)
        output = _attach_source_tool_call_id(tool_name, output, call_id)
        return ToolCallRecord(
            tool_call_id=call_id,
            tool_name=tool_name,
            input_args=_jsonable(input_args),
            output=output,
            evidence_ids=evidence_ids_for(tool_name, input_args, output),
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            success=True,
        ).to_dict()
    except Exception as exc:
        return ToolCallRecord(
            tool_call_id=call_id,
            tool_name=tool_name,
            input_args=_jsonable(input_args),
            output={},
            evidence_ids=[],
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            success=False,
            error_type=exc.__class__.__name__,
        ).to_dict()


def get_registered_tool_names() -> list[str]:
    return sorted(TOOL_REGISTRY)
