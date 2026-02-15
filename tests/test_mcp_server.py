"""Test suite for Market MCP REST API Server.

Tests all HTTP REST endpoints:
- GET /mcp/tools
- POST /mcp/tools/call
- GET /mcp/resources
- GET /mcp/resources/{uri}
- GET /mcp/prompts
- POST /mcp/prompts/get
- GET /health
"""

import json
import requests
import time


BASE_URL = "http://localhost:9001"


def test_health():
    """Test health endpoint."""
    print("\n" + "="*80)
    print("TEST: Health Check")
    print("="*80)

    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("✅ PASSED")


def test_list_tools():
    """Test listing tools."""
    print("\n" + "="*80)
    print("TEST: List Tools - GET /mcp/tools")
    print("="*80)

    response = requests.get(f"{BASE_URL}/mcp/tools")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Found {len(data['tools'])} tools:")
    for tool in data['tools']:
        print(f"  - {tool['name']}: {tool['description'][:60]}...")

    assert response.status_code == 200
    assert len(data["tools"]) == 2
    print("✅ PASSED")


def test_call_tool_get_stock_price():
    """Test calling get_stock_price tool."""
    print("\n" + "="*80)
    print("TEST: Call Tool - get_stock_price (symbol)")
    print("="*80)

    payload = {
        "tool": "get_stock_price",
        "arguments": {"symbol": "AAPL"}
    }

    response = requests.post(f"{BASE_URL}/mcp/tools/call", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response: {json.dumps(data, indent=2)}")

    assert response.status_code == 200
    result = data["result"]
    assert result["symbol"] == "AAPL"
    assert result["price"] is not None
    print(f"✅ PASSED - Got price: ${result['price']}")


def test_call_tool_search_company():
    """Test calling search_company tool."""
    print("\n" + "="*80)
    print("TEST: Call Tool - search_company")
    print("="*80)

    payload = {
        "tool": "search_company",
        "arguments": {"company_name": "Apple"}
    }

    response = requests.post(f"{BASE_URL}/mcp/tools/call", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Found {len(data['result'])} companies:")
    for company in data['result'][:3]:
        print(f"  - {company['symbol']}: {company['description']}")

    assert response.status_code == 200
    assert len(data["result"]) > 0
    print("✅ PASSED")


def test_call_tool_multiple_stocks():
    """Test calling get_stock_price with multiple symbols."""
    print("\n" + "="*80)
    print("TEST: Call Tool - get_stock_price (multiple symbols)")
    print("="*80)

    payload = {
        "tool": "get_stock_price",
        "arguments": {"symbols": ["AAPL", "MSFT", "GOOGL"]}
    }

    response = requests.post(f"{BASE_URL}/mcp/tools/call", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()
    result = data["result"]
    print(f"Retrieved {result['successful']}/{result['count']} stocks")

    for stock in result['stocks']:
        if stock.get('price'):
            print(f"  - {stock['symbol']}: ${stock['price']}")

    assert response.status_code == 200
    assert result["count"] == 3
    print("✅ PASSED")


def test_list_resources():
    """Test listing resources."""
    print("\n" + "="*80)
    print("TEST: List Resources - GET /mcp/resources")
    print("="*80)

    response = requests.get(f"{BASE_URL}/mcp/resources")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Found {len(data['resources'])} resources:")
    for resource in data['resources']:
        print(f"  - {resource['uri']}: {resource['name']}")

    assert response.status_code == 200
    assert len(data["resources"]) == 2
    print("✅ PASSED")


def test_get_resource_popular_stocks():
    """Test getting popular stocks resource."""
    print("\n" + "="*80)
    print("TEST: Get Resource - popular-stocks")
    print("="*80)

    response = requests.get(f"{BASE_URL}/mcp/resources/popular-stocks")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Found {len(data['data'])} popular stocks:")
    for stock in data['data'][:5]:
        print(f"  - {stock['symbol']}: {stock['name']} ({stock['sector']})")

    assert response.status_code == 200
    assert len(data["data"]) == 10
    print("✅ PASSED")


def test_get_resource_indices():
    """Test getting indices resource."""
    print("\n" + "="*80)
    print("TEST: Get Resource - indices")
    print("="*80)

    response = requests.get(f"{BASE_URL}/mcp/resources/indices")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Found {len(data['data'])} indices:")
    for index in data['data']:
        print(f"  - {index['symbol']}: {index['name']}")

    assert response.status_code == 200
    assert len(data["data"]) == 4
    print("✅ PASSED")


def test_list_prompts():
    """Test listing prompts."""
    print("\n" + "="*80)
    print("TEST: List Prompts - GET /mcp/prompts")
    print("="*80)

    response = requests.get(f"{BASE_URL}/mcp/prompts")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Found {len(data['prompts'])} prompts:")
    for prompt in data['prompts']:
        print(f"  - {prompt['name']}: {prompt['description']}")

    assert response.status_code == 200
    assert len(data["prompts"]) == 2
    print("✅ PASSED")


def test_get_prompt_analyze():
    """Test getting analyze_stock_performance prompt."""
    print("\n" + "="*80)
    print("TEST: Get Prompt - analyze_stock_performance")
    print("="*80)

    payload = {
        "prompt": "analyze_stock_performance",
        "arguments": {"symbol": "AAPL"}
    }

    response = requests.post(f"{BASE_URL}/mcp/prompts/get", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Prompt preview: {data['prompt'][:200]}...")

    assert response.status_code == 200
    assert "AAPL" in data["prompt"]
    print("✅ PASSED")


def test_get_prompt_compare():
    """Test getting compare_stocks prompt."""
    print("\n" + "="*80)
    print("TEST: Get Prompt - compare_stocks")
    print("="*80)

    payload = {
        "prompt": "compare_stocks",
        "arguments": {"symbols": ["AAPL", "MSFT"]}
    }

    response = requests.post(f"{BASE_URL}/mcp/prompts/get", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Prompt preview: {data['prompt'][:200]}...")

    assert response.status_code == 200
    assert "AAPL" in data["prompt"]
    assert "MSFT" in data["prompt"]
    print("✅ PASSED")


def run_all_tests():
    """Run all tests."""
    print("\n" + "🚀"*40)
    print("MARKET MCP REST API - COMPREHENSIVE TEST SUITE")
    print("🚀"*40)

    tests = [
        ("Health Check", test_health),
        ("List Tools", test_list_tools),
        ("Call Tool - get_stock_price", test_call_tool_get_stock_price),
        ("Call Tool - search_company", test_call_tool_search_company),
        ("Call Tool - Multiple Stocks", test_call_tool_multiple_stocks),
        ("List Resources", test_list_resources),
        ("Get Resource - Popular Stocks", test_get_resource_popular_stocks),
        ("Get Resource - Indices", test_get_resource_indices),
        ("List Prompts", test_list_prompts),
        ("Get Prompt - Analyze", test_get_prompt_analyze),
        ("Get Prompt - Compare", test_get_prompt_compare),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ FAILED: {test_name}")
            print(f"   Error: {e}")
            failed += 1
            import traceback
            traceback.print_exc()

    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total: {passed + failed}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")

    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
        return True
    else:
        print(f"\n💥 {failed} TEST(S) FAILED")
        return False


if __name__ == "__main__":
    # Wait for server to be ready
    print("Waiting for server to be ready...")
    time.sleep(2)

    success = run_all_tests()
    exit(0 if success else 1)

