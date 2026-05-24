"""Product benchmark node for wealth-management product comparison."""
from __future__ import annotations

from typing import Any

from backend.app.tools.product_benchmark import peer_summary


def product_benchmark_agent(state: dict[str, Any]) -> dict[str, Any]:
    request = state["request"]
    filters = request.get("product_filters") or {}
    peer = peer_summary(state["products_df"], filters=filters)

    tool_calls = list(state.get("tool_calls", []))
    tool_calls.append(
        {
            "tool": "peer_summary",
            "agent": "product_benchmark_agent",
            "success": True,
            "rows": int(peer.get("product_count", 0)),
        }
    )

    return {
        **state,
        "peer_summary": peer,
        "tool_calls": tool_calls,
    }
