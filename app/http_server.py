"""Streamable HTTP REST API Server for Market MCP.

This server provides REST API endpoints for stock market data:
- GET /app/tools - List all available tools
- POST /app/tools/call - Call a specific tool
- GET /app/resources - List all resources
- GET /app/resources/{uri} - Get a specific resource
- GET /app/prompts - List all prompts
- POST /app/prompts/get - Get a specific prompt
- GET /health - Health check
"""

import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Import server functions
from .server import (
    get_single_stock_price,
    get_multiple_stock_prices,
    get_multiple_company_prices,
    search_company_by_name,
    _finnhub_client
)
from .utils.logger import get_logger, kv, set_correlation_id

load_dotenv(override=False)
log = get_logger(__name__)

app = FastAPI(
    title="Market MCP REST API",
    description="Streamable HTTP REST API for stock market data",
    version="1.0.0"
)


# Request/Response Models
class ToolCallRequest(BaseModel):
    tool: str
    arguments: Dict[str, Any]


class PromptGetRequest(BaseModel):
    prompt: str
    arguments: Dict[str, Any]


# Tool definitions
TOOLS = [
    {
        "name": "get_stock_price",
        "description": "Fetch latest stock price(s) using Finnhub API. Supports single symbol, company name, or multiple symbols/companies.",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Single stock symbol (e.g., 'AAPL')"
                },
                "company_name": {
                    "type": "string",
                    "description": "Single company name (e.g., 'Apple')"
                },
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of stock symbols"
                },
                "company_names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of company names"
                }
            }
        }
    },
    {
        "name": "search_company",
        "description": "Search for companies by name using Finnhub symbol lookup",
        "parameters": {
            "type": "object",
            "properties": {
                "company_name": {
                    "type": "string",
                    "description": "Company name to search for"
                }
            },
            "required": ["company_name"]
        }
    }
]

# Resource definitions
RESOURCES = [
    {
        "uri": "market://popular-stocks",
        "name": "Popular Stocks",
        "description": "List of popular stock symbols and their descriptions"
    },
    {
        "uri": "market://indices",
        "name": "Market Indices",
        "description": "Major market indices symbols"
    }
]

# Prompt definitions
PROMPTS = [
    {
        "name": "analyze_stock_performance",
        "description": "Generate analysis prompt for stock performance",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock symbol to analyze"
                }
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "compare_stocks",
        "description": "Generate comparison prompt for multiple stocks",
        "parameters": {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of stock symbols to compare"
                }
            },
            "required": ["symbols"]
        }
    }
]


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Market MCP REST API",
        "version": "1.0.0",
        "description": "Streamable HTTP REST API for stock market data",
        "endpoints": {
            "tools": "/app/tools",
            "resources": "/app/resources",
            "prompts": "/app/prompts",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    finnhub_status = "connected" if _finnhub_client else "not_configured"
    return {
        "status": "healthy",
        "finnhub": finnhub_status,
        "server": "running"
    }


@app.get("/mcp/tools")
async def list_tools():
    """List all available tools."""
    set_correlation_id()
    log.info("app.list_tools %s", kv(count=len(TOOLS)))
    return {
        "tools": TOOLS
    }


@app.post("/mcp/tools/call")
async def call_tool(request: ToolCallRequest):
    """Call a specific tool with arguments."""
    set_correlation_id()
    tool_name = request.tool
    arguments = request.arguments

    log.info("app.call_tool %s", kv(tool=tool_name, arguments=arguments))

    try:
        if tool_name == "get_stock_price":
            # Handle different parameter combinations
            symbol = arguments.get("symbol")
            company_name = arguments.get("company_name")
            symbols = arguments.get("symbols")
            company_names = arguments.get("company_names")

            if company_names and len(company_names) > 1:
                result = get_multiple_company_prices(company_names)
            elif company_names and len(company_names) == 1:
                result = get_single_stock_price(company_name=company_names[0])
            elif symbols and len(symbols) > 1:
                result = get_multiple_stock_prices(symbols)
            elif symbols and len(symbols) == 1:
                result = get_single_stock_price(symbol=symbols[0])
            else:
                result = get_single_stock_price(symbol=symbol, company_name=company_name)

            return {"result": result}

        elif tool_name == "search_company":
            company_name = arguments.get("company_name")
            if not company_name:
                raise HTTPException(status_code=400, detail="company_name is required")

            result = search_company_by_name(company_name)
            return {"result": result}

        else:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    except Exception as e:
        log.error("app.tool_call_error %s", kv(tool=tool_name, error=str(e)))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/resources")
async def list_resources():
    """List all available resources."""
    set_correlation_id()
    log.info("app.list_resources %s", kv(count=len(RESOURCES)))
    return {
        "resources": RESOURCES
    }


@app.get("/mcp/resources/{resource_uri:path}")
async def get_resource(resource_uri: str):
    """Get a specific resource by URI."""
    set_correlation_id()
    log.info("app.get_resource %s", kv(uri=resource_uri))

    # Add market:// prefix if not present
    if not resource_uri.startswith("market://"):
        resource_uri = f"market://{resource_uri}"

    try:
        if resource_uri == "market://popular-stocks":
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
            return {"data": popular}

        elif resource_uri == "market://indices":
            indices = [
                {"symbol": "^GSPC", "name": "S&P 500", "description": "US large-cap index"},
                {"symbol": "^DJI", "name": "Dow Jones Industrial Average", "description": "US 30 major companies"},
                {"symbol": "^IXIC", "name": "NASDAQ Composite", "description": "US tech-heavy index"},
                {"symbol": "^RUT", "name": "Russell 2000", "description": "US small-cap index"},
            ]
            return {"data": indices}

        else:
            raise HTTPException(status_code=404, detail=f"Resource '{resource_uri}' not found")

    except HTTPException:
        raise
    except Exception as e:
        log.error("app.resource_error %s", kv(uri=resource_uri, error=str(e)))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/prompts")
async def list_prompts():
    """List all available resources."""
    set_correlation_id()
    log.info("app.list_prompts %s", kv(count=len(PROMPTS)))
    return {
        "prompts": PROMPTS
    }


@app.post("/mcp/prompts/get")
async def get_prompt(request: PromptGetRequest):
    """Get a specific prompt with arguments."""
    set_correlation_id()
    prompt_name = request.prompt
    arguments = request.arguments

    log.info("app.get_prompt %s", kv(prompt=prompt_name, arguments=arguments))

    try:
        if prompt_name == "analyze_stock_performance":
            symbol = arguments.get("symbol")
            if not symbol:
                raise HTTPException(status_code=400, detail="symbol is required")

            price_data = get_single_stock_price(symbol=symbol)

            if price_data.get("error"):
                return {"prompt": f"Unable to analyze {symbol}: {price_data.get('error')}"}

            current = price_data.get("price", 0)
            prev_close = price_data.get("previous_close", 0)
            high = price_data.get("high", 0)
            low = price_data.get("low", 0)

            change = current - prev_close if prev_close else 0
            change_pct = (change / prev_close * 100) if prev_close else 0

            prompt_text = f"""Analyze the stock performance for {symbol}:

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

            return {"prompt": prompt_text}

        elif prompt_name == "compare_stocks":
            symbols = arguments.get("symbols", [])
            if not symbols or len(symbols) < 2:
                raise HTTPException(status_code=400, detail="At least 2 symbols are required")

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

            prompt_text = f"""Compare the following stocks:

{table}

Analysis Questions:
1. Which stock has the best performance today?
2. Which stock is most volatile?
3. What are the key differences between these companies?
4. Which would you recommend for a long-term investment and why?

Provide a comparative analysis with recommendations."""

            return {"prompt": prompt_text}

        else:
            raise HTTPException(status_code=404, detail=f"Prompt '{prompt_name}' not found")

    except HTTPException:
        raise
    except Exception as e:
        log.error("app.prompt_error %s", kv(prompt=prompt_name, error=str(e)))
        raise HTTPException(status_code=500, detail=str(e))


def start_server(host: str = "0.0.0.0", port: int = 9001):
    """Start the FastAPI server."""
    log.info("http_api.starting %s", kv(host=host, port=port))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    port = int(os.getenv("MCP_PORT", "9001"))
    start_server(port=port)

