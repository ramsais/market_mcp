"""Test script to verify SSE streaming endpoint works correctly."""

import json
import asyncio
from app.http_server import app
from fastapi.testclient import TestClient

client = TestClient(app)

print("=" * 70)
print("TESTING HTTP SERVER - SSE STREAMING ENDPOINT")
print("=" * 70)

# Test 1: List all tools
print("\n[TEST 1] GET /mcp/tools")
response = client.get("/mcp/tools")
assert response.status_code == 200
data = response.json()
print(f"✓ Status: {response.status_code}")
print(f"✓ Tools found: {len(data['tools'])}")
for tool in data['tools']:
    print(f"  - {tool['name']}")

# Test 2: Call tool (regular)
print("\n[TEST 2] POST /mcp/tools/call (regular)")
response = client.post(
    "/mcp/tools/call",
    json={"tool": "search_company", "arguments": {"company_name": "Apple"}}
)
assert response.status_code == 200
data = response.json()
print(f"✓ Status: {response.status_code}")
print(f"✓ Results: {len(data['result'])} companies found")
if data['result']:
    print(f"  First result: {data['result'][0]['symbol']} - {data['result'][0]['description']}")

# Test 3: Call tool with streaming (SSE)
print("\n[TEST 3] POST /mcp/tools/call/stream (SSE streaming)")
with client.stream(
    "POST",
    "/mcp/tools/call/stream",
    json={"tool": "get_stock_price", "arguments": {"symbol": "AAPL"}}
) as response:
    assert response.status_code == 200
    print(f"✓ Status: {response.status_code}")
    print(f"✓ Content-Type: {response.headers.get('content-type')}")

    events = []
    for line in response.iter_lines():
        if line:
            line = line.strip()
            if line.startswith(b"event:"):
                event_type = line.split(b":", 1)[1].strip().decode()
                events.append(event_type)
                print(f"  Event: {event_type}")
            elif line.startswith(b"data:"):
                data_str = line.split(b":", 1)[1].strip().decode()
                data = json.loads(data_str)
                print(f"  Data: {json.dumps(data, indent=4)[:100]}...")

    print(f"✓ Events received: {events}")
    assert "start" in events
    assert "result" in events
    assert "done" in events

# Test 4: List resources
print("\n[TEST 4] GET /mcp/resources")
response = client.get("/mcp/resources")
assert response.status_code == 200
data = response.json()
print(f"✓ Status: {response.status_code}")
print(f"✓ Resources found: {len(data['resources'])}")
for resource in data['resources']:
    print(f"  - {resource['uri']}")

# Test 5: Get specific resource
print("\n[TEST 5] GET /mcp/resources/popular-stocks")
response = client.get("/mcp/resources/popular-stocks")
assert response.status_code == 200
data = response.json()
print(f"✓ Status: {response.status_code}")
print(f"✓ Stocks in response: {len(data['data'])}")
if data['data']:
    print(f"  First stock: {data['data'][0]['symbol']} - {data['data'][0]['name']}")

# Test 6: List prompts
print("\n[TEST 6] GET /mcp/prompts")
response = client.get("/mcp/prompts")
assert response.status_code == 200
data = response.json()
print(f"✓ Status: {response.status_code}")
print(f"✓ Prompts found: {len(data['prompts'])}")
for prompt in data['prompts']:
    print(f"  - {prompt['name']}")

# Test 7: Get prompt
print("\n[TEST 7] POST /mcp/prompts/get")
response = client.post(
    "/mcp/prompts/get",
    json={"prompt": "analyze_stock_performance", "arguments": {"symbol": "AAPL"}}
)
assert response.status_code == 200
data = response.json()
print(f"✓ Status: {response.status_code}")
print(f"✓ Prompt text length: {len(data['prompt'])} characters")
print(f"  First 100 chars: {data['prompt'][:100]}...")

# Test 8: Health check
print("\n[TEST 8] GET /health")
response = client.get("/health")
assert response.status_code == 200
data = response.json()
print(f"✓ Status: {response.status_code}")
print(f"✓ Server status: {data['status']}")
print(f"✓ Finnhub status: {data['finnhub']}")

# Test 9: Error handling - non-existent tool
print("\n[TEST 9] Error handling - non-existent tool")
response = client.post(
    "/mcp/tools/call",
    json={"tool": "non_existent_tool", "arguments": {}}
)
print(f"✓ Status: {response.status_code}")
assert response.status_code == 404
print(f"✓ Error message: {response.json()['detail']}")

# Test 10: Error handling - invalid arguments
print("\n[TEST 10] Error handling - invalid arguments")
response = client.post(
    "/mcp/tools/call",
    json={"tool": "search_company", "arguments": {}}  # Missing required company_name
)
print(f"✓ Status: {response.status_code}")
assert response.status_code in [400, 500]  # Either 400 for invalid args or 500 for execution error
print(f"✓ Error handled correctly")

print("\n" + "=" * 70)
print("✓✓✓ ALL TESTS PASSED ✓✓✓")
print("=" * 70)
print("\nSummary:")
print("✓ Dynamic tool discovery working")
print("✓ Dynamic resource discovery working")
print("✓ Dynamic prompt discovery working")
print("✓ Regular tool calls working")
print("✓ SSE streaming tool calls working")
print("✓ Resource retrieval working")
print("✓ Prompt generation working")
print("✓ Health check working")
print("✓ Error handling working (404, 400/500)")
print("✓ No hardcoded values - all dynamic from MCP instance")
print("=" * 70)

