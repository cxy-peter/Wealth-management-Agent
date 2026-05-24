"""MCP client helpers.

The workflow can run without this client. When MCP dependencies are available,
``get_mcp_tools`` returns LangChain-compatible tools backed by the local sample
server.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]


def local_mcp_config() -> dict[str, Any]:
    return {
        "wealth_research_local": {
            "command": "python",
            "args": ["-m", "backend.app.mcp.local_server"],
            "transport": "stdio",
            "cwd": str(ROOT),
        }
    }


async def get_mcp_tools() -> list[Any]:
    from langchain_mcp_adapters.client import MultiServerMCPClient

    client = MultiServerMCPClient(local_mcp_config())
    return await client.get_tools()


def mcp_available() -> bool:
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient  # noqa: F401
        from langchain_mcp_adapters.tools import load_mcp_tools  # noqa: F401

        return True
    except Exception:
        return False
