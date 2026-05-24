"""Shared helpers for ReAct-style tool agents with deterministic fallback."""
from __future__ import annotations

import os
from typing import Any

from backend.app.tools.tool_registry import execute_tool

try:
    from langgraph.prebuilt import create_react_agent

    CREATE_REACT_AGENT_AVAILABLE = True
except Exception:  # pragma: no cover
    create_react_agent = None
    CREATE_REACT_AGENT_AVAILABLE = False


def build_optional_react_agent(tools: list[Any]) -> Any | None:
    if not CREATE_REACT_AGENT_AVAILABLE or not os.getenv("OPENAI_COMPATIBLE_API_KEY"):
        return None
    try:  # pragma: no cover - requires configured live model
        from langchain_openai import ChatOpenAI

        model = ChatOpenAI(
            api_key=os.getenv("OPENAI_COMPATIBLE_API_KEY"),
            base_url=os.getenv("OPENAI_COMPATIBLE_BASE_URL") or None,
            model=os.getenv("OPENAI_COMPATIBLE_MODEL", "qwen-plus"),
            temperature=0,
        )
        return create_react_agent(model, tools)
    except Exception:
        return None


def tool_allowed(tool_name: str, allowed_tools: list[str]) -> bool:
    return tool_name in allowed_tools


def call_registry_tool(state: dict[str, Any], agent_name: str, tool_name: str, **kwargs: Any) -> dict[str, Any]:
    record = execute_tool(tool_name, **kwargs)
    tool_calls = [*state.get("tool_calls", []), record]
    event = {
        "event_type": "tool_call",
        "agent_name": agent_name,
        "payload": {
            "tool_call_id": record["tool_call_id"],
            "tool_name": tool_name,
            "success": record["success"],
            "evidence_ids": record.get("evidence_ids", []),
            "fallback_mode": "deterministic_tool_pipeline",
        },
    }
    return {
        "record": record,
        "tool_calls": tool_calls,
        "agent_events": [*state.get("agent_events", []), event],
    }


def final_event(agent_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_type": "agent_final",
        "agent_name": agent_name,
        "payload": payload,
    }
