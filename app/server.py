"""Enhanced Market Data MCP Server using FastMCP with best practices.

This module demonstrates MCP architecture and FastMCP best practices:
- Type-safe responses with Pydantic models
- Service layer with dependency injection
- Comprehensive error handling
- Rich documentation with examples
- Input validation
- Separation of concerns
"""

from __future__ import annotations

from typing import Annotated, List

from fastmcp import FastMCP
from pydantic import Field, validate_call

from .config import settings
from .exceptions import (
    CompanyNotFoundError,
    MCPError,
    SymbolNotFoundError,
    ServiceUnavailableError
)
from .models import (
    CompanySearchResponse,
    MultiStockResponse,
    StockPriceData
)
from .services import get_finnhub_service
from .utils.logger import configure_logging, get_logger, kv
from .utils.timing import timed

log = get_logger(__name__)
configure_logging()

# Initialize FastMCP with configuration
mcp = FastMCP(
    name=settings.app_name,
    instructions="""You are a market data assistant with access to real-time stock prices.
    Use the provided tools to fetch stock prices, search for companies, and analyze market data.
    Always provide clear, accurate information and acknowledge any limitations."""
)

# Get service instance
finnhub_service = get_finnhub_service()


# ==============================================================================
# MCP TOOLS - Stock Price Operations
# ==============================================================================


@validate_call
@timed("mcp.get_stock_price_single")
def get_stock_price(
    symbol: Annotated[
        str,
        Field(
            description="Stock ticker symbol (e.g., 'AAPL', 'GOOGL', 'MSFT')",
            min_length=1,
            max_length=10
        )
    ]
) -> StockPriceData:
    """Fetch current stock price for a single symbol.

    This tool retrieves real-time stock price data from Finnhub API including
    current price, day high/low, opening price, and previous close.

    Args:
        symbol: Stock ticker symbol in uppercase (e.g., "AAPL" for Apple Inc.)

    Returns:
        StockPriceData: Complete stock price information

    Examples:
        get_stock_price("AAPL") -> Returns Apple stock price
        get_stock_price("GOOGL") -> Returns Google stock price
    """
    log.info("mcp.tool.get_stock_price %s", kv(symbol=symbol))

    try:
        symbol = symbol.strip().upper()
        result = finnhub_service.get_quote(symbol)
        log.info("mcp.tool.get_stock_price.success %s", kv(symbol=symbol, price=result.price))
        return result

    except (SymbolNotFoundError, ServiceUnavailableError):
        raise
    except Exception as exc:
        log.error("mcp.tool.get_stock_price.error %s", kv(symbol=symbol, error=str(exc)))
        raise MCPError(f"Failed to get stock price: {str(exc)}")


@mcp.tool()
@validate_call
@timed("mcp.get_stock_price_by_company")
def get_stock_price_by_company(
    company_name: Annotated[
        str,
        Field(
            description="Company name to search for (e.g., 'Apple', 'Microsoft')",
            min_length=2,
            max_length=100
        )
    ]
) -> StockPriceData:
    """Fetch stock price by company name."""
    log.info("mcp.tool.get_stock_price_by_company %s", kv(company_name=company_name))

    try:
        result = finnhub_service.get_quote_by_company_name(company_name)
        log.info("mcp.tool.get_stock_price_by_company.success %s", kv(company_name=company_name, symbol=result.symbol))
        return result

    except (CompanyNotFoundError, ServiceUnavailableError):
        raise
    except Exception as exc:
        log.error("mcp.tool.get_stock_price_by_company.error %s", kv(company_name=company_name, error=str(exc)))
        raise MCPError(f"Failed to get stock price: {str(exc)}")


@mcp.tool()
@validate_call
@timed("mcp.get_multiple_stock_prices")
def get_multiple_stock_prices(
    symbols: Annotated[
        List[str],
        Field(
            description="List of stock ticker symbols",
            min_length=1,
            max_length=20
        )
    ]
) -> MultiStockResponse:
    """Fetch stock prices for multiple symbols."""
    log.info("mcp.tool.get_multiple_stock_prices %s", kv(count=len(symbols)))

    stocks: List[StockPriceData] = []
    successful = 0
    failed = 0

    for symbol in symbols:
        try:
            result = finnhub_service.get_quote(symbol)
            stocks.append(result)
            successful += 1
        except Exception as exc:
            stocks.append(StockPriceData(
                symbol=symbol.upper(),
                price=None,
                error=str(exc)
            ))
            failed += 1

    log.info("mcp.tool.get_multiple_stock_prices.complete %s", kv(total=len(symbols), successful=successful, failed=failed))

    return MultiStockResponse(
        stocks=stocks,
        source="finnhub",
        count=len(stocks),
        successful=successful,
        failed=failed
    )


@mcp.tool()
@validate_call
@timed("mcp.search_company")
def search_company(
    company_name: Annotated[
        str,
        Field(
            description="Company name to search for",
            min_length=2,
            max_length=100
        )
    ]
) -> CompanySearchResponse:
    """Search for companies by name."""
    log.info("mcp.tool.search_company %s", kv(query=company_name))

    try:
        results = finnhub_service.search_companies(company_name)
        log.info("mcp.tool.search_company.success %s", kv(query=company_name, count=len(results)))

        return CompanySearchResponse(
            results=results,
            query=company_name,
            count=len(results)
        )

    except ServiceUnavailableError:
        raise
    except Exception as exc:
        log.error("mcp.tool.search_company.error %s", kv(query=company_name, error=str(exc)))
        raise MCPError(f"Failed to search companies: {str(exc)}")


# ==============================================================================
# MCP RESOURCES
# ==============================================================================

@mcp.resource("market://popular-stocks")
def get_popular_stocks() -> str:
    """List of popular stock symbols."""
    import json

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

    log.info("mcp.resource.popular_stocks %s", kv(count=len(popular)))
    return json.dumps(popular, indent=2)


@mcp.resource("market://indices")
def get_market_indices() -> str:
    """Major market indices symbols."""
    import json

    indices = [
        {"symbol": "^GSPC", "name": "S&P 500", "description": "US large-cap index"},
        {"symbol": "^DJI", "name": "Dow Jones Industrial Average", "description": "US 30 major companies"},
        {"symbol": "^IXIC", "name": "NASDAQ Composite", "description": "US tech-heavy index"},
        {"symbol": "^RUT", "name": "Russell 2000", "description": "US small-cap index"},
    ]

    log.info("mcp.resource.market_indices %s", kv(count=len(indices)))
    return json.dumps(indices, indent=2)


# ==============================================================================
# MCP PROMPTS
# ==============================================================================

@mcp.prompt()
@validate_call
def analyze_stock_performance(
    symbol: Annotated[str, Field(description="Stock symbol to analyze")]
) -> str:
    """Generate analysis prompt for stock performance."""
    try:
        price_data = finnhub_service.get_quote(symbol)

        if price_data.has_error:
            return f"Unable to analyze {symbol}: {price_data.error}"

        current = price_data.price or 0
        prev_close = price_data.previous_close or 0
        high = price_data.high or 0
        low = price_data.low or 0

        change = price_data.change or 0
        change_pct = price_data.change_percent or 0

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

    except Exception as exc:
        log.error("mcp.prompt.analyze_stock_performance.error %s", kv(symbol=symbol, error=str(exc)))
        return f"Error analyzing {symbol}: {str(exc)}"


@mcp.prompt()
@validate_call
def compare_stocks(
    symbols: Annotated[List[str], Field(description="Stock symbols to compare", min_length=2)]
) -> str:
    """Generate comparison prompt for multiple stocks."""
    if len(symbols) < 2:
        return "Please provide at least 2 stock symbols to compare."

    comparison_data = []
    for symbol in symbols:
        try:
            stock = finnhub_service.get_quote(symbol)
            comparison_data.append({
                "symbol": stock.symbol,
                "price": stock.price,
                "change_pct": stock.change_percent or 0
            })
        except Exception as exc:
            log.warning("mcp.prompt.compare_stocks.symbol_error %s", kv(symbol=symbol, error=str(exc)))
            comparison_data.append({
                "symbol": symbol.upper(),
                "price": None,
                "change_pct": 0
            })

    table = "Symbol | Price | Change %\n"
    table += "-------|-------|----------\n"
    for item in comparison_data:
        price_str = f"${item['price']:.2f}" if item['price'] else "N/A"
        table += f"{item['symbol']} | {price_str} | {item['change_pct']:+.2f}%\n"

    return f"""Compare the following stocks:

{table}

Analysis Questions:
1. Which stock has the best performance today?
2. Which stock is most volatile?
3. What are the key differences between these companies?
4. Which would you recommend for a long-term investment and why?

Provide a comparative analysis with recommendations."""


if __name__ == "__main__":
    print("This module defines MCP tools, resources, and prompts.")
    print("To start the HTTP REST API server, run:")
    print("  python start_server.py")

