"""Conditional LangGraph orchestration for the wealth research assistant."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, TypedDict

try:
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.graph import END, START, StateGraph

    LANGGRAPH_AVAILABLE = True
except Exception:  # pragma: no cover - dependency fallback
    END = "END"
    START = "START"
    MemorySaver = None
    StateGraph = None
    LANGGRAPH_AVAILABLE = False

from backend.app.agents.fundamental_react_agent import fundamental_react_agent
from backend.app.agents.human_review_agent import human_review_agent, should_trigger_review
from backend.app.agents.news_react_agent import news_react_agent
from backend.app.agents.planner_agent import planner_agent
from backend.app.agents.product_benchmark_agent import product_benchmark_agent
from backend.app.agents.report_agent import report_agent
from backend.app.agents.risk_guardrail_agent import risk_guardrail_agent
from backend.app.agents.technical_react_agent import technical_react_agent
from backend.app.agents.valuation_react_agent import valuation_react_agent
from backend.app.agents.verifier_agent import verifier_agent
from backend.app.storage import (
    add_event,
    add_report_snapshot,
    add_tool_call,
    create_run,
    new_run_id,
    update_run,
)


@dataclass
class ResearchRequest:
    symbol: str
    company: str
    analysis_type: str = "full"
    risk_preference: str = "balanced"
    output_path: str = "reports/demo_report.md"
    product_filters: dict[str, Any] = field(default_factory=dict)
    run_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResearchState(TypedDict, total=False):
    run_id: str
    request: dict[str, Any]
    planner_plan: dict[str, Any]
    price_series: dict[str, Any]
    fundamental_analysis: dict[str, Any]
    valuation_analysis: dict[str, Any]
    technical_analysis: dict[str, Any]
    metrics: dict[str, Any]
    news_records: dict[str, Any]
    news_signals: list[dict[str, Any]]
    news_summary: dict[str, Any]
    peer_summary: dict[str, Any]
    risk_flags: list[str]
    compliance_boundary: dict[str, Any]
    verification_result: dict[str, Any]
    human_review: dict[str, Any]
    model_metadata: dict[str, Any]
    tool_calls: list[dict[str, Any]]
    agent_events: list[dict[str, Any]]
    run_trace: dict[str, Any]
    result: dict[str, Any]


def _required(state: ResearchState, tool_name: str) -> bool:
    return tool_name in state.get("planner_plan", {}).get("required_tools", [])


def _next_after_planner(state: ResearchState) -> str:
    if _required(state, "load_fundamental_snapshot"):
        return "fundamental_react_agent"
    if _required(state, "calculate_metrics") or _required(state, "load_price_series"):
        return "technical_react_agent"
    if _required(state, "load_valuation_snapshot"):
        return "valuation_react_agent"
    if _required(state, "classify_news_risk") or _required(state, "load_news"):
        return "news_react_agent"
    if _required(state, "product_benchmark"):
        return "product_benchmark_agent"
    return "risk_guardrail_agent"


def _next_after_fundamental(state: ResearchState) -> str:
    if _required(state, "calculate_metrics") or _required(state, "load_price_series"):
        return "technical_react_agent"
    if _required(state, "load_valuation_snapshot"):
        return "valuation_react_agent"
    if _required(state, "classify_news_risk") or _required(state, "load_news"):
        return "news_react_agent"
    if _required(state, "product_benchmark"):
        return "product_benchmark_agent"
    return "risk_guardrail_agent"


def _next_after_technical(state: ResearchState) -> str:
    if _required(state, "load_valuation_snapshot"):
        return "valuation_react_agent"
    if _required(state, "classify_news_risk") or _required(state, "load_news"):
        return "news_react_agent"
    if _required(state, "product_benchmark"):
        return "product_benchmark_agent"
    return "risk_guardrail_agent"


def _next_after_valuation(state: ResearchState) -> str:
    if _required(state, "classify_news_risk") or _required(state, "load_news"):
        return "news_react_agent"
    if _required(state, "product_benchmark"):
        return "product_benchmark_agent"
    return "risk_guardrail_agent"


def _next_after_news(state: ResearchState) -> str:
    if _required(state, "product_benchmark"):
        return "product_benchmark_agent"
    return "risk_guardrail_agent"


def _next_after_verifier(state: ResearchState) -> str:
    return "human_review_agent" if should_trigger_review(state) else END


def _build_langgraph():
    if not LANGGRAPH_AVAILABLE:
        return None

    graph = StateGraph(ResearchState)
    graph.add_node("planner_agent", planner_agent)
    graph.add_node("fundamental_react_agent", fundamental_react_agent)
    graph.add_node("technical_react_agent", technical_react_agent)
    graph.add_node("valuation_react_agent", valuation_react_agent)
    graph.add_node("news_react_agent", news_react_agent)
    graph.add_node("product_benchmark_agent", product_benchmark_agent)
    graph.add_node("risk_guardrail_agent", risk_guardrail_agent)
    graph.add_node("report_agent", report_agent)
    graph.add_node("verifier_agent", verifier_agent)
    graph.add_node("human_review_agent", human_review_agent)

    graph.add_edge(START, "planner_agent")
    graph.add_conditional_edges("planner_agent", _next_after_planner)
    graph.add_conditional_edges("fundamental_react_agent", _next_after_fundamental)
    graph.add_conditional_edges("technical_react_agent", _next_after_technical)
    graph.add_conditional_edges("valuation_react_agent", _next_after_valuation)
    graph.add_conditional_edges("news_react_agent", _next_after_news)
    graph.add_edge("product_benchmark_agent", "risk_guardrail_agent")
    graph.add_edge("risk_guardrail_agent", "report_agent")
    graph.add_edge("report_agent", "verifier_agent")
    graph.add_conditional_edges("verifier_agent", _next_after_verifier)
    graph.add_edge("human_review_agent", END)
    checkpointer = MemorySaver() if MemorySaver is not None else None
    return graph.compile(checkpointer=checkpointer)


_GRAPH = _build_langgraph()


def _run_sequential(state: ResearchState) -> ResearchState:
    state = planner_agent(state)
    node_name = _next_after_planner(state)
    while node_name != END:
        node = {
            "fundamental_react_agent": fundamental_react_agent,
            "technical_react_agent": technical_react_agent,
            "valuation_react_agent": valuation_react_agent,
            "news_react_agent": news_react_agent,
            "product_benchmark_agent": product_benchmark_agent,
            "risk_guardrail_agent": risk_guardrail_agent,
            "report_agent": report_agent,
            "verifier_agent": verifier_agent,
            "human_review_agent": human_review_agent,
        }[node_name]
        state = node(state)
        if node_name == "fundamental_react_agent":
            node_name = _next_after_fundamental(state)
        elif node_name == "technical_react_agent":
            node_name = _next_after_technical(state)
        elif node_name == "valuation_react_agent":
            node_name = _next_after_valuation(state)
        elif node_name == "news_react_agent":
            node_name = _next_after_news(state)
        elif node_name == "product_benchmark_agent":
            node_name = "risk_guardrail_agent"
        elif node_name == "risk_guardrail_agent":
            node_name = "report_agent"
        elif node_name == "report_agent":
            node_name = "verifier_agent"
        elif node_name == "verifier_agent":
            node_name = _next_after_verifier(state)
        else:
            node_name = END
    return state


def _persist_final_state(final_state: ResearchState) -> None:
    run_id = final_state["run_id"]
    result = final_state.get("result", {})
    for event in final_state.get("agent_events", []):
        add_event(run_id, event.get("event_type", "event"), event.get("agent_name", "unknown"), event.get("payload", {}))
    for record in result.get("tool_calls", final_state.get("tool_calls", [])):
        add_tool_call(run_id, record)
    if result.get("report_markdown"):
        add_report_snapshot(run_id, result["report_markdown"], result.get("report_path"))
    update_run(
        run_id,
        status=result.get("human_review", {}).get("status", "completed"),
        planner_json=final_state.get("planner_plan", {}),
        verifier_json=final_state.get("verification_result", {}),
        guardrail_json=final_state.get("compliance_boundary", {}),
    )


def run_workflow(request: ResearchRequest, persist: bool = True) -> dict[str, Any]:
    run_id = request.run_id or new_run_id()
    request.run_id = run_id
    if persist:
        create_run(
            run_id,
            request.symbol,
            request.company,
            request.analysis_type,
            request.risk_preference,
            status="running",
        )

    state: ResearchState = {
        "run_id": run_id,
        "request": request.to_dict(),
        "tool_calls": [],
        "agent_events": [],
        "run_trace": {},
    }
    if _GRAPH is not None:
        final_state = _GRAPH.invoke(state, config={"configurable": {"thread_id": run_id}})
    else:
        final_state = _run_sequential(state)

    result = final_state["result"]
    result["run_id"] = run_id
    result["workflow_engine"] = "langgraph" if _GRAPH is not None else "sequential-fallback"
    result["workflow_nodes"] = [event["agent_name"] for event in final_state.get("agent_events", []) if event["event_type"] == "agent_final"]
    result["planner_plan"] = final_state.get("planner_plan", {})
    result["agent_events"] = final_state.get("agent_events", [])
    result["tool_calls"] = final_state.get("tool_calls", result.get("tool_calls", []))
    result["verification_result"] = final_state.get("verification_result", result.get("verification_result", {}))
    result["human_review"] = final_state.get("human_review", result.get("human_review", {"status": "auto_cleared"}))

    if persist:
        final_state["result"] = result
        _persist_final_state(final_state)
    return result
