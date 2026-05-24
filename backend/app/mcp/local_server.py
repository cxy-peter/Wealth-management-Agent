"""Local MCP server exposing sample/mock research tools."""
from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from backend.app.tools.tool_registry import execute_tool

mcp = FastMCP("wealth-research-agent-local")


@mcp.tool()
def load_price_series(symbol: str) -> dict[str, Any]:
    return execute_tool("load_price_series", symbol=symbol)


@mcp.tool()
def calculate_metrics(symbol: str) -> dict[str, Any]:
    return execute_tool("calculate_metrics", symbol=symbol)


@mcp.tool()
def load_fundamental_snapshot(symbol: str) -> dict[str, Any]:
    return execute_tool("load_fundamental_snapshot", symbol=symbol)


@mcp.tool()
def load_valuation_snapshot(symbol: str) -> dict[str, Any]:
    return execute_tool("load_valuation_snapshot", symbol=symbol)


@mcp.tool()
def load_news(symbol: str) -> dict[str, Any]:
    return execute_tool("load_news", symbol=symbol)


@mcp.tool()
def classify_news_risk(symbol: str) -> dict[str, Any]:
    news_call = execute_tool("load_news", symbol=symbol)
    return execute_tool(
        "classify_news_risk",
        symbol=symbol,
        news_records=news_call.get("output", {}).get("records", []),
    )


@mcp.tool()
def product_benchmark(
    asset_class: str | None = None,
    risk_level: str | None = None,
    channel: str | None = None,
) -> dict[str, Any]:
    return execute_tool(
        "product_benchmark",
        asset_class=asset_class,
        risk_level=risk_level,
        channel=channel,
    )


if __name__ == "__main__":
    mcp.run()
