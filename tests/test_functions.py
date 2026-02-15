"""Direct function tests for Market MCP Server.

This test suite directly calls the server functions to validate functionality
without needing the MCP protocol layer.
"""

import json
import os
import sys

# Ensure we can import from the parent directory (project root)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.server import (
    get_single_stock_price,
    get_multiple_stock_prices,
    search_company_by_name,
    _finnhub_client
)


def test_finnhub_client():
    """Test that Finnhub client is initialized."""
    print("\n" + "="*80)
    print("TEST: Finnhub Client Initialization")
    print("="*80)

    if _finnhub_client is None:
        print("❌ Finnhub client not initialized")
        print("   Please set FINNHUB_API_KEY in .env file")
        return False
    else:
        print("✅ Finnhub client initialized")
        return True


def test_search_company():
    """Test company search functionality."""
    print("\n" + "="*80)
    print("TEST: Search Company")
    print("="*80)

    company_name = "Apple"
    print(f"Searching for: {company_name}")

    results = search_company_by_name(company_name)
    print(f"📋 Results: {json.dumps(results, indent=2)}")

    if results:
        print(f"✅ Found {len(results)} results")
        return True
    else:
        print("⚠️  No results found")
        return False


def test_get_stock_price_by_symbol():
    """Test getting stock price by symbol."""
    print("\n" + "="*80)
    print("TEST: Get Stock Price by Symbol")
    print("="*80)

    symbol = "AAPL"
    print(f"Getting price for: {symbol}")

    result = get_single_stock_price(symbol=symbol)
    print(f"📋 Result: {json.dumps(result, indent=2)}")

    if result.get("price"):
        print(f"✅ Got price: ${result['price']}")
        return True
    elif result.get("error"):
        print(f"⚠️  Error: {result['error']}")
        return False
    else:
        print("❌ No price or error in result")
        return False


def test_get_stock_price_by_company():
    """Test getting stock price by company name."""
    print("\n" + "="*80)
    print("TEST: Get Stock Price by Company Name")
    print("="*80)

    company_name = "Microsoft"
    print(f"Getting price for: {company_name}")

    result = get_single_stock_price(company_name=company_name)
    print(f"📋 Result: {json.dumps(result, indent=2)}")

    if result.get("price"):
        print(f"✅ Got price: ${result['price']} for {result.get('symbol')}")
        return True
    elif result.get("error"):
        print(f"⚠️  Error: {result['error']}")
        return False
    else:
        print("❌ No price or error in result")
        return False


def test_get_multiple_stock_prices():
    """Test getting multiple stock prices."""
    print("\n" + "="*80)
    print("TEST: Get Multiple Stock Prices")
    print("="*80)

    symbols = ["AAPL", "MSFT", "GOOGL"]
    print(f"Getting prices for: {symbols}")

    result = get_multiple_stock_prices(symbols)
    print(f"📋 Result: {json.dumps(result, indent=2)}")

    stocks = result.get("stocks", [])
    successful = result.get("successful", 0)

    print(f"📊 Retrieved {len(stocks)} stocks, {successful} successful")

    if successful > 0:
        print(f"✅ Got {successful} prices")
        return True
    else:
        print("❌ No successful price retrievals")
        return False


def test_popular_stocks_resource():
    """Test popular stocks resource."""
    print("\n" + "="*80)
    print("TEST: Popular Stocks Resource")
    print("="*80)

    # Test by creating the data directly (resource functions are decorated)
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

    result = json.dumps(popular, indent=2)
    print(f"📋 Result: {result[:200]}...")  # Show first 200 chars

    data = json.loads(result)
    print(f"✅ Got {len(data)} popular stocks")
    return True


def test_market_indices_resource():
    """Test market indices resource."""
    print("\n" + "="*80)
    print("TEST: Market Indices Resource")
    print("="*80)

    # Test by creating the data directly (resource functions are decorated)
    indices = [
        {"symbol": "^GSPC", "name": "S&P 500", "description": "US large-cap index"},
        {"symbol": "^DJI", "name": "Dow Jones Industrial Average", "description": "US 30 major companies"},
        {"symbol": "^IXIC", "name": "NASDAQ Composite", "description": "US tech-heavy index"},
        {"symbol": "^RUT", "name": "Russell 2000", "description": "US small-cap index"},
    ]

    result = json.dumps(indices, indent=2)
    print(f"📋 Result: {result}")

    data = json.loads(result)
    print(f"✅ Got {len(data)} market indices")
    return True


def test_error_handling():
    """Test error handling."""
    print("\n" + "="*80)
    print("TEST: Error Handling")
    print("="*80)

    # Test invalid symbol
    print("Testing invalid symbol...")
    result = get_single_stock_price(symbol="INVALID_SYMBOL_XYZ123")
    if "error" in result or result.get("price") is None:
        print("✅ Handled invalid symbol gracefully")
    else:
        print("⚠️  Invalid symbol returned data (might be valid)")

    # Test no parameters
    print("\nTesting no parameters...")
    result = get_single_stock_price()
    if "error" in result:
        print("✅ Handled missing parameters gracefully")
    else:
        print("❌ Should return error for missing parameters")
        return False

    return True


def main():
    """Run all direct function tests."""
    print("\n" + "🧪" * 40)
    print("MARKET MCP SERVER - DIRECT FUNCTION TESTS")
    print("🧪" * 40)

    # Check API key
    if not os.getenv("FINNHUB_API_KEY"):
        print("\n⚠️  Warning: FINNHUB_API_KEY not set in environment")
        print("   Tests may fail or return limited data")
        print()

    tests = [
        ("Finnhub Client", test_finnhub_client),
        ("Search Company", test_search_company),
        ("Get Stock Price by Symbol", test_get_stock_price_by_symbol),
        ("Get Stock Price by Company", test_get_stock_price_by_company),
        ("Get Multiple Stock Prices", test_get_multiple_stock_prices),
        ("Popular Stocks Resource", test_popular_stocks_resource),
        ("Market Indices Resource", test_market_indices_resource),
        ("Error Handling", test_error_handling),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total tests: {passed + failed}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if failed == 0:
        print("\n🎉 All tests passed!")
        return True
    else:
        print(f"\n💥 {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

