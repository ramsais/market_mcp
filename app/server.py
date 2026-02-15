"""Market Data MCP Server using FastMCP.

This server provides stock price and company search functionality using Finnhub API.
The MCP capabilities (tools, resources, prompts) are defined here and exposed via HTTP REST API.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastmcp import FastMCP

from .utils.logger import configure_logging, get_logger, kv
from .utils.timing import timed

log = get_logger(__name__)

configure_logging()
load_dotenv(override=False)

mcp = FastMCP("Market Data Server")

# Initialize Finnhub client
try:
    import finnhub

    _finnhub_client = finnhub.Client(api_key=os.getenv("FINNHUB_API_KEY"))
    log.info("app.finnhub_initialized")
except Exception as exc:
    log.error("app.finnhub_initialization_error %s", kv(error=str(exc)))
    _finnhub_client = None


def _normalize_symbol(symbol: str) -> str:
    """Normalize stock symbol to uppercase."""
    return (symbol or "").strip().upper()


@timed("app.search_company_by_name")
def search_company_by_name(company_name: str) -> List[Dict[str, Any]]:
    """Search for companies by name using Finnhub symbol lookup."""
    if _finnhub_client is None:
        log.error("app.client_not_initialized")
        return []

    try:
        results = _finnhub_client.symbol_lookup(company_name)
        matches = (results or {}).get("result") or []
        log.info("finnhub.search_results %s", kv(company_name=company_name, count=len(matches)))
        return [
            {
                "symbol": match.get("symbol"),
                "description": match.get("description"),
                "type": match.get("type"),
                "displaySymbol": match.get("displaySymbol"),
            }
            for match in matches
        ]
    except Exception as exc:
        log.error("finnhub.search_error %s", kv(company_name=company_name, error=str(exc)))
        return []


@timed("app.get_single_stock_price")
def get_single_stock_price(
    *, symbol: Optional[str] = None, company_name: Optional[str] = None
) -> Dict[str, Any]:
    """Get stock price for a single symbol or company name."""
    if _finnhub_client is None:
        return {"error": "Finnhub client not initialized.", "source": "finnhub"}

    if symbol:
        final_symbol = _normalize_symbol(symbol)
        resolved_company_name = None
    elif company_name:
        matches = search_company_by_name(company_name)
        if not matches:
            return {
                "symbol": None,
                "price": None,
                "currency": "USD",
                "timestamp": None,
                "source": "finnhub",
                "company_name": company_name,
                "error": f"No company found matching '{company_name}'",
            }
        final_symbol = matches[0].get("symbol")
        resolved_company_name = matches[0].get("description")
    else:
        return {"error": "No symbol or company name provided", "source": "finnhub"}

    try:
        quote = _finnhub_client.quote(final_symbol)
        current_price = (quote or {}).get("c")
        if not current_price:
            return {
                "symbol": final_symbol,
                "price": None,
                "currency": "USD",
                "timestamp": None,
                "source": "finnhub",
                "company_name": resolved_company_name,
                "error": f"No price data available for {final_symbol}",
            }
        return {
            "symbol": final_symbol,
            "price": current_price,
            "currency": "USD",
            "timestamp": (quote or {}).get("t"),
            "source": "finnhub",
            "company_name": resolved_company_name,
            "high": (quote or {}).get("h"),
            "low": (quote or {}).get("l"),
            "open": (quote or {}).get("o"),
            "previous_close": (quote or {}).get("pc"),
        }
    except Exception as exc:
        log.error("finnhub.api_error %s", kv(symbol=final_symbol, error=str(exc)))
        return {
            "symbol": final_symbol,
            "price": None,
            "currency": "USD",
            "timestamp": None,
            "source": "finnhub",
            "company_name": resolved_company_name,
            "error": f"Finnhub API error: {str(exc)}",
        }


@timed("app.get_multiple_stock_prices")
def get_multiple_stock_prices(symbols: List[str]) -> Dict[str, Any]:
    """Get stock prices for multiple symbols."""
    results: List[Dict[str, Any]] = []
    successful = 0
    failed = 0

    for sym in symbols:
        result = get_single_stock_price(symbol=sym)
        results.append(result)
        if result.get("price") is not None:
            successful += 1
        else:
            failed += 1

    return {
        "stocks": results,
        "source": "finnhub",
        "count": len(results),
        "successful": successful,
        "failed": failed,
    }


@timed("app.get_multiple_company_prices")
def get_multiple_company_prices(company_names: List[str]) -> Dict[str, Any]:
    """Get stock prices for multiple company names."""
    results: List[Dict[str, Any]] = []
    successful = 0
    failed = 0

    for company in company_names:
        result = get_single_stock_price(company_name=company)
        results.append(result)
        if result.get("price") is not None:
            successful += 1
        else:
            failed += 1

    return {
        "stocks": results,
        "source": "finnhub",
        "count": len(results),
        "successful": successful,
        "failed": failed,
    }


# MCP Tool Definitions
@mcp.tool()
def get_stock_price(
    symbol: Optional[str] = None,
    company_name: Optional[str] = None,
    symbols: Optional[List[str]] = None,
    company_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Fetch latest stock price(s) using Finnhub API.

    Args:
        symbol: Single stock symbol (e.g., "AAPL")
        company_name: Single company name (e.g., "Apple")
        symbols: List of stock symbols
        company_names: List of company names

    Returns:
        Stock price data with symbol, price, currency, timestamp, etc.
    """
    if _finnhub_client is None:
        return {"error": "Finnhub client not initialized.", "source": "finnhub"}

    if company_names and len(company_names) > 1:
        return get_multiple_company_prices(company_names)
    if company_names and len(company_names) == 1:
        return get_single_stock_price(company_name=company_names[0])
    if symbols and len(symbols) > 1:
        return get_multiple_stock_prices(symbols)
    if symbols and len(symbols) == 1:
        return get_single_stock_price(symbol=symbols[0])
    return get_single_stock_price(symbol=symbol, company_name=company_name)


@mcp.tool()
def search_company(company_name: str) -> List[Dict[str, Any]]:
    """Search for companies by name using Finnhub symbol lookup.

    Args:
        company_name: Company name to search for

    Returns:
        List of matching companies with symbols and descriptions
    """
    return search_company_by_name(company_name)


# MCP Resource Definitions
@mcp.resource("market://popular-stocks")
def get_popular_stocks() -> str:
    """Resource: List of popular stock symbols and their descriptions.

    This resource provides a reference list of commonly traded stocks.
    """
    popular = [
        {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
        {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology"},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology"},
        {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Cyclical"},
        {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Automotive"},
        {"symbol": "META", "name": "Meta Platforms Inc.", "sector": "Technology"},
        {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology"},
        {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financial"},
        {"symbol": "V", "name": "Visa Inc.", "sector": "Financial"},
        {"symbol": "WMT", "name": "Walmart Inc.", "sector": "Consumer Defensive"},
    ]

    import json
    return json.dumps(popular, indent=2)


@mcp.resource("market://indices")
def get_market_indices() -> str:
    """Resource: Major market indices symbols.

    This resource provides symbols for major stock market indices.
    """
    indices = [
        {"symbol": "^GSPC", "name": "S&P 500", "description": "US large-cap index"},
        {"symbol": "^DJI", "name": "Dow Jones Industrial Average", "description": "US 30 major companies"},
        {"symbol": "^IXIC", "name": "NASDAQ Composite", "description": "US tech-heavy index"},
        {"symbol": "^RUT", "name": "Russell 2000", "description": "US small-cap index"},
    ]

    import json
    return json.dumps(indices, indent=2)


# MCP Prompt Definitions
@mcp.prompt()
def analyze_stock_performance(symbol: str) -> str:
    """Prompt: Generate analysis prompt for stock performance.

    This prompt helps analyze a stock's performance based on price data.

    Args:
        symbol: Stock symbol to analyze
    """
    price_data = get_single_stock_price(symbol=symbol)

    if price_data.get("error"):
        return f"Unable to analyze {symbol}: {price_data.get('error')}"

    current = price_data.get("price", 0)
    prev_close = price_data.get("previous_close", 0)
    high = price_data.get("high", 0)
    low = price_data.get("low", 0)

    change = current - prev_close if prev_close else 0
    change_pct = (change / prev_close * 100) if prev_close else 0

    return f"""Analyze the stock performance for {symbol}:

Current Price: ${current:.2f}
Previous Close: ${prev_close:.2f}
Change: ${change:.2f} ({change_pct:+.2f}%)
Day High: ${high:.2f}
Day Low: ${low:.2f}

Based on this data:
1. Is the stock trending up or down today?
2. What is the volatility range (high - low)?
3. Should an investor be concerned or optimistic?
4. What additional information would help make an investment decision?

Provide a brief analysis with key insights."""


@mcp.prompt()
def compare_stocks(symbols: List[str]) -> str:
    """Prompt: Generate comparison prompt for multiple stocks.

    Args:
        symbols: List of stock symbols to compare
    """
    if not symbols or len(symbols) < 2:
        return "Please provide at least 2 stock symbols to compare."

    prices = get_multiple_stock_prices(symbols)
    stocks = prices.get("stocks", [])

    comparison_data = []
    for stock in stocks:
        sym = stock.get("symbol")
        price = stock.get("price")
        prev_close = stock.get("previous_close", 0)
        change_pct = ((price - prev_close) / prev_close * 100) if prev_close and price else 0

        comparison_data.append({
            "symbol": sym,
            "price": price,
            "change_pct": change_pct
        })

    table = "Symbol | Price | Change %\n"
    table += "-------|-------|----------\n"
    for item in comparison_data:
        table += f"{item['symbol']} | ${item['price']:.2f} | {item['change_pct']:+.2f}%\n"

    return f"""Compare the following stocks:

{table}

Analysis Questions:
1. Which stock has the best performance today?
2. Which stock is most volatile?
3. What are the key differences between these companies?
4. Which would you recommend for a long-term investment and why?

Provide a comparative analysis with recommendations."""


if __name__ == "__main__":
    # This file defines MCP capabilities (tools, resources, prompts)
    # Use start_server.py to run the HTTP REST API server
    print("This module defines MCP tools, resources, and prompts.")
    print("To start the HTTP REST API server, run:")
    print("  python start_server.py")
    print()
    print("Or use:")
    print("  python app/http_server.py")


