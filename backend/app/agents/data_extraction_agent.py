"""Data extraction node for the LangGraph workflow."""
from __future__ import annotations

from typing import Any

from backend.app.tools.data_loader import load_fundamentals, load_nav, load_news, load_products


def _records(df: Any) -> list[dict[str, Any]]:
    records = df.copy()
    for column in records.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
        records[column] = records[column].dt.strftime("%Y-%m-%d")
    return records.to_dict(orient="records")


def data_extraction_agent(state: dict[str, Any]) -> dict[str, Any]:
    request = state["request"]
    symbol = request["symbol"]

    nav_df = load_nav(symbol)
    news_df = load_news(symbol)
    products_df = load_products()
    fundamentals_df = load_fundamentals(symbol)

    tool_calls = list(state.get("tool_calls", []))
    tool_calls.extend(
        [
            {"tool": "load_nav", "agent": "data_extraction_agent", "success": True, "rows": int(len(nav_df))},
            {"tool": "load_news", "agent": "data_extraction_agent", "success": True, "rows": int(len(news_df))},
            {"tool": "load_products", "agent": "data_extraction_agent", "success": True, "rows": int(len(products_df))},
            {
                "tool": "load_fundamentals",
                "agent": "data_extraction_agent",
                "success": True,
                "rows": int(len(fundamentals_df)),
            },
        ]
    )

    return {
        **state,
        "nav_df": nav_df,
        "news_df": news_df,
        "products_df": products_df,
        "fundamentals_df": fundamentals_df,
        "data_profile": {
            "market_rows": int(len(nav_df)),
            "news_rows": int(len(news_df)),
            "product_rows": int(len(products_df)),
            "fundamental_rows": int(len(fundamentals_df)),
            "data_mode": "sample/mock",
            "market_sample": _records(nav_df.tail(5)),
            "news_sample": _records(news_df.tail(5)),
        },
        "tool_calls": tool_calls,
    }
