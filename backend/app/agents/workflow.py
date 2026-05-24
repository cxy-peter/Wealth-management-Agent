"""LangGraph orchestration for the wealth research assistant."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, TypedDict

try:
    from langgraph.graph import END, START, StateGraph

    LANGGRAPH_AVAILABLE = True
except Exception:  # pragma: no cover - local dependency fallback
    END = "END"
    START = "START"
    StateGraph = None
    LANGGRAPH_AVAILABLE = False

from backend.app.agents.data_extraction_agent import data_extraction_agent
from backend.app.agents.fundamental_agent import fundamental_agent
from backend.app.agents.news_risk_agent import news_risk_agent
from backend.app.agents.product_benchmark_agent import product_benchmark_agent
from backend.app.agents.report_agent import report_agent
from backend.app.agents.risk_guardrail_agent import risk_guardrail_agent
from backend.app.agents.technical_agent import technical_agent


@dataclass
class ResearchRequest:
    symbol: str
    company: str
    analysis_type: str = "full"
    output_path: str = "reports/demo_report.md"
    product_filters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResearchState(TypedDict, total=False):
    request: dict[str, Any]
    nav_df: Any
    news_df: Any
    products_df: Any
    fundamentals_df: Any
    data_profile: dict[str, Any]
    fundamental_analysis: dict[str, Any]
    valuation_analysis: dict[str, Any]
    technical_analysis: dict[str, Any]
    metrics: dict[str, Any]
    news_signals: list[dict[str, Any]]
    news_summary: dict[str, Any]
    peer_summary: dict[str, Any]
    risk_flags: list[str]
    compliance_boundary: dict[str, Any]
    model_metadata: dict[str, Any]
    tool_calls: list[dict[str, Any]]
    result: dict[str, Any]


def _build_langgraph():
    if not LANGGRAPH_AVAILABLE:
        return None

    graph = StateGraph(ResearchState)
    graph.add_node("data_extraction_agent", data_extraction_agent)
    graph.add_node("fundamental_agent", fundamental_agent)
    graph.add_node("technical_agent", technical_agent)
    graph.add_node("news_risk_agent", news_risk_agent)
    graph.add_node("product_benchmark_agent", product_benchmark_agent)
    graph.add_node("risk_guardrail_agent", risk_guardrail_agent)
    graph.add_node("report_agent", report_agent)

    graph.add_edge(START, "data_extraction_agent")
    graph.add_edge("data_extraction_agent", "fundamental_agent")
    graph.add_edge("fundamental_agent", "technical_agent")
    graph.add_edge("technical_agent", "news_risk_agent")
    graph.add_edge("news_risk_agent", "product_benchmark_agent")
    graph.add_edge("product_benchmark_agent", "risk_guardrail_agent")
    graph.add_edge("risk_guardrail_agent", "report_agent")
    graph.add_edge("report_agent", END)
    return graph.compile()


_GRAPH = _build_langgraph()


def _run_sequential(state: ResearchState) -> ResearchState:
    for node in [
        data_extraction_agent,
        fundamental_agent,
        technical_agent,
        news_risk_agent,
        product_benchmark_agent,
        risk_guardrail_agent,
        report_agent,
    ]:
        state = node(state)
    return state


def run_workflow(request: ResearchRequest) -> dict[str, Any]:
    state: ResearchState = {"request": request.to_dict(), "tool_calls": []}
    final_state = _GRAPH.invoke(state) if _GRAPH is not None else _run_sequential(state)
    result = final_state["result"]
    result["workflow_engine"] = "langgraph" if _GRAPH is not None else "sequential-fallback"
    result["workflow_nodes"] = [
        "data_extraction_agent",
        "fundamental_agent",
        "technical_agent",
        "news_risk_agent",
        "product_benchmark_agent",
        "risk_guardrail_agent",
        "report_agent",
    ]
    return result
