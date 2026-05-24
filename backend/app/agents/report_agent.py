"""Report-generation node."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.app.utils.report_writer import render_report, write_report

ROOT = Path(__file__).resolve().parents[3]


def report_agent(state: dict[str, Any]) -> dict[str, Any]:
    request = state["request"]
    result = {
        "symbol": request["symbol"],
        "company": request["company"],
        "analysis_type": request.get("analysis_type", "full"),
        "run_id": state.get("run_id"),
        "planner_plan": state.get("planner_plan", {}),
        "data_profile": state.get("data_profile", {}),
        "metrics": state.get("metrics", {}),
        "fundamental_analysis": state.get("fundamental_analysis", {}),
        "valuation_analysis": state.get("valuation_analysis", {}),
        "technical_analysis": state.get("technical_analysis", {}),
        "news_signals": state.get("news_signals", []),
        "news_summary": state.get("news_summary", {}),
        "peer_summary": state.get("peer_summary", {}),
        "risk_flags": state.get("risk_flags", []),
        "tool_calls": state.get("tool_calls", []),
        "agent_events": state.get("agent_events", []),
        "model_metadata": state.get("model_metadata", {}),
        "compliance_boundary": state.get("compliance_boundary", {}),
    }
    report = render_report(result)
    requested_path = Path(request["output_path"])
    output_target = requested_path if requested_path.is_absolute() else ROOT / requested_path
    output_path = write_report(report, output_target)
    try:
        display_path = output_path.relative_to(ROOT).as_posix()
    except ValueError:
        display_path = str(output_path)

    tool_calls = list(state.get("tool_calls", []))
    tool_calls.append(
        {
            "tool_call_id": "tc_report_render_local",
            "tool_name": "render_markdown_report",
            "input_args": {"run_id": state.get("run_id")},
            "output": {"report_path": display_path},
            "evidence_ids": ["ev_report_snapshot"],
            "latency_ms": 0.0,
            "success": True,
            "error_type": None,
        }
    )
    result["tool_calls"] = tool_calls
    result["report_path"] = display_path
    result["report_markdown"] = report
    return {
        **state,
        "result": result,
        "tool_calls": tool_calls,
        "agent_events": [
            *state.get("agent_events", []),
            {
                "event_type": "agent_final",
                "agent_name": "report_agent",
                "payload": {"report_path": display_path},
            },
        ],
    }
