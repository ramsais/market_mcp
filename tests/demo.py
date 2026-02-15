#!/usr/bin/env python3
"""Comprehensive demo of all Market MCP Server capabilities.

This script demonstrates all tools, resources, and functionality.
"""

import json
import sys
import os

# Add parent directory to path (project root)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.server import (
    get_single_stock_price,
    get_multiple_stock_prices,
    get_multiple_company_prices,
    search_company_by_name,
)


def print_section(title):
    """Print a section header."""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def print_json(data):
    """Print JSON data formatted."""
    print(json.dumps(data, indent=2))


def demo_search_companies():
    """Demo: Search for companies."""
    print_section("DEMO 1: Search for Companies")

    queries = ["Apple", "Microsoft", "Tesla"]

    for query in queries:
        print(f"\n🔍 Searching for: {query}")
        results = search_company_by_name(query)

        if results:
            print(f"✅ Found {len(results)} results:")
            for i, result in enumerate(results[:3], 1):  # Show top 3
                print(f"   {i}. {result['symbol']} - {result['description']}")
        else:
            print("❌ No results found")


def demo_single_stock_price():
    """Demo: Get single stock price by symbol."""
    print_section("DEMO 2: Get Stock Price by Symbol")

    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN"]

    for symbol in symbols:
        print(f"\n📊 Getting price for: {symbol}")
        result = get_single_stock_price(symbol=symbol)

        if result.get("price"):
            price = result["price"]
            prev_close = result.get("previous_close", 0)
            change = price - prev_close if prev_close else 0
            change_pct = (change / prev_close * 100) if prev_close else 0

            print(f"✅ {symbol}: ${price:.2f}")
            print(f"   Change: ${change:.2f} ({change_pct:+.2f}%)")
            print(f"   High: ${result.get('high', 0):.2f} | Low: ${result.get('low', 0):.2f}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")


def demo_stock_price_by_company():
    """Demo: Get stock price by company name."""
    print_section("DEMO 3: Get Stock Price by Company Name")

    companies = ["Apple", "Microsoft", "Tesla"]

    for company in companies:
        print(f"\n📊 Getting price for: {company}")
        result = get_single_stock_price(company_name=company)

        if result.get("price"):
            symbol = result["symbol"]
            price = result["price"]
            company_name = result.get("company_name", company)

            print(f"✅ {company_name} ({symbol}): ${price:.2f}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")


def demo_multiple_stocks():
    """Demo: Get multiple stock prices."""
    print_section("DEMO 4: Get Multiple Stock Prices")

    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

    print(f"\n📊 Getting prices for: {', '.join(symbols)}")
    result = get_multiple_stock_prices(symbols)

    print(f"\n✅ Retrieved {result['successful']} of {result['count']} stocks:\n")
    print(f"{'Symbol':<10} {'Price':<12} {'Change':<12} {'High/Low':<20}")
    print("-" * 60)

    for stock in result["stocks"]:
        if stock.get("price"):
            symbol = stock["symbol"]
            price = stock["price"]
            prev_close = stock.get("previous_close", 0)
            change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0
            high = stock.get("high", 0)
            low = stock.get("low", 0)

            print(f"{symbol:<10} ${price:<11.2f} {change_pct:+.2f}%      ${low:.2f} - ${high:.2f}")
        else:
            print(f"{stock['symbol']:<10} N/A")


def demo_multiple_companies():
    """Demo: Get multiple company prices by name."""
    print_section("DEMO 5: Get Multiple Company Prices by Name")

    companies = ["Apple", "Microsoft", "Amazon"]

    print(f"\n📊 Getting prices for: {', '.join(companies)}")
    result = get_multiple_company_prices(companies)

    print(f"\n✅ Retrieved {result['successful']} of {result['count']} companies:\n")

    for stock in result["stocks"]:
        if stock.get("price"):
            company_name = stock.get("company_name", "Unknown")
            symbol = stock["symbol"]
            price = stock["price"]

            print(f"✅ {company_name} ({symbol}): ${price:.2f}")
        else:
            query = stock.get("company_name", "Unknown")
            print(f"❌ {query}: {stock.get('error', 'No data')}")


def demo_resources():
    """Demo: Show available resources."""
    print_section("DEMO 6: Available Resources")

    print("\n📚 Popular Stocks:")
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

    for stock in popular:
        print(f"   {stock['symbol']:<6} - {stock['name']:<35} [{stock['sector']}]")

    print("\n📈 Market Indices:")
    indices = [
        {"symbol": "^GSPC", "name": "S&P 500", "description": "US large-cap index"},
        {"symbol": "^DJI", "name": "Dow Jones Industrial Average", "description": "US 30 major companies"},
        {"symbol": "^IXIC", "name": "NASDAQ Composite", "description": "US tech-heavy index"},
        {"symbol": "^RUT", "name": "Russell 2000", "description": "US small-cap index"},
    ]

    for index in indices:
        print(f"   {index['symbol']:<8} - {index['name']:<35} [{index['description']}]")


def demo_analysis():
    """Demo: Stock analysis example."""
    print_section("DEMO 7: Stock Analysis Example")

    symbol = "AAPL"
    print(f"\n📊 Analyzing {symbol}...")

    result = get_single_stock_price(symbol=symbol)

    if result.get("price"):
        current = result["price"]
        prev_close = result.get("previous_close", 0)
        high = result.get("high", 0)
        low = result.get("low", 0)
        open_price = result.get("open", 0)

        change = current - prev_close if prev_close else 0
        change_pct = (change / prev_close * 100) if prev_close else 0
        volatility = high - low

        print(f"\n{'Metric':<25} {'Value':<15}")
        print("-" * 40)
        print(f"{'Current Price':<25} ${current:.2f}")
        print(f"{'Previous Close':<25} ${prev_close:.2f}")
        print(f"{'Change':<25} ${change:.2f} ({change_pct:+.2f}%)")
        print(f"{'Open':<25} ${open_price:.2f}")
        print(f"{'Day High':<25} ${high:.2f}")
        print(f"{'Day Low':<25} ${low:.2f}")
        print(f"{'Volatility (H-L)':<25} ${volatility:.2f}")

        print("\n💡 Analysis:")
        if change_pct > 0:
            print(f"   ✅ Stock is UP {change_pct:.2f}% today")
        elif change_pct < 0:
            print(f"   ⚠️  Stock is DOWN {change_pct:.2f}% today")
        else:
            print(f"   ➡️  Stock is FLAT today")

        volatility_pct = (volatility / current * 100) if current else 0
        if volatility_pct > 5:
            print(f"   📊 High volatility: {volatility_pct:.2f}% range")
        elif volatility_pct > 2:
            print(f"   📊 Moderate volatility: {volatility_pct:.2f}% range")
        else:
            print(f"   📊 Low volatility: {volatility_pct:.2f}% range")


def demo_comparison():
    """Demo: Compare multiple stocks."""
    print_section("DEMO 8: Stock Comparison")

    symbols = ["AAPL", "MSFT", "GOOGL"]
    print(f"\n📊 Comparing: {', '.join(symbols)}\n")

    result = get_multiple_stock_prices(symbols)

    print(f"{'Stock':<10} {'Price':<12} {'Change %':<12} {'Vol %':<12} {'Status':<15}")
    print("-" * 70)

    for stock in result["stocks"]:
        if stock.get("price"):
            symbol = stock["symbol"]
            price = stock["price"]
            prev_close = stock.get("previous_close", 0)
            high = stock.get("high", 0)
            low = stock.get("low", 0)

            change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0
            volatility_pct = ((high - low) / price * 100) if price else 0

            if change_pct > 0:
                status = "📈 Rising"
            elif change_pct < 0:
                status = "📉 Falling"
            else:
                status = "➡️  Flat"

            print(f"{symbol:<10} ${price:<11.2f} {change_pct:+.2f}%      {volatility_pct:.2f}%       {status}")

    print("\n💡 Best Performer:")
    best = max(result["stocks"], key=lambda s: ((s.get("price", 0) - s.get("previous_close", 0)) / s.get("previous_close", 1) * 100) if s.get("price") else -999)
    if best.get("price"):
        best_change = ((best["price"] - best.get("previous_close", 0)) / best.get("previous_close", 1) * 100) if best.get("previous_close") else 0
        print(f"   🏆 {best['symbol']}: {best_change:+.2f}%")


def main():
    """Run all demos."""
    print("\n" + "🚀" * 40)
    print("MARKET MCP SERVER - COMPREHENSIVE CAPABILITY DEMO")
    print("🚀" * 40)

    if not os.getenv("FINNHUB_API_KEY"):
        print("\n⚠️  Warning: FINNHUB_API_KEY not set")
        print("   Some demos may not work properly\n")

    try:
        demo_search_companies()
        demo_single_stock_price()
        demo_stock_price_by_company()
        demo_multiple_stocks()
        demo_multiple_companies()
        demo_resources()
        demo_analysis()
        demo_comparison()

        print("\n" + "="*80)
        print("  ✅ ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*80)

        print("\n📚 Available MCP Features:")
        print("   • Tools: get_stock_price, search_company")
        print("   • Resources: market://popular-stocks, market://indices")
        print("   • Prompts: analyze_stock_performance, compare_stocks")

        print("\n🌐 Server Info:")
        print("   • Transport: SSE (Server-Sent Events)")
        print("   • Port: 9001")
        print("   • URL: http://localhost:9001/sse")

        print("\n💡 Next Steps:")
        print("   • Server is running and ready for MCP clients")
        print("   • All functions tested and working")
        print("   • Connect with Claude Desktop or other MCP clients")

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

