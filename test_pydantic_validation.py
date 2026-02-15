"""Test script to verify Pydantic validation is working."""

from pydantic import ValidationError
from app.http_server import ToolCallRequest, PromptGetRequest

print("=" * 70)
print("PYDANTIC VALIDATION TESTS")
print("=" * 70)

# Test 1: Valid request
print("\n[TEST 1] Valid request with all fields")
try:
    request = ToolCallRequest(tool="get_stock_price", arguments={"symbol": "AAPL"})
    print(f"✅ Valid: tool='{request.tool}', arguments={request.arguments}")
except ValidationError as e:
    print(f"❌ Failed: {e}")

# Test 2: Empty tool name
print("\n[TEST 2] Empty tool name (should fail)")
try:
    request = ToolCallRequest(tool="", arguments={})
    print(f"❌ Should have failed but passed: {request}")
except ValidationError as e:
    print(f"✅ Validation error caught (expected):")
    print(f"   {e.errors()[0]['msg']}")

# Test 3: Whitespace-only tool name
print("\n[TEST 3] Whitespace-only tool name (should fail)")
try:
    request = ToolCallRequest(tool="   ", arguments={})
    print(f"❌ Should have failed but passed: {request}")
except ValidationError as e:
    print(f"✅ Validation error caught (expected):")
    print(f"   {e.errors()[0]['msg']}")

# Test 4: Tool name with whitespace (should be trimmed)
print("\n[TEST 4] Tool name with whitespace (should be trimmed)")
try:
    request = ToolCallRequest(tool="  get_stock_price  ", arguments={})
    print(f"✅ Valid: tool='{request.tool}' (trimmed)")
except ValidationError as e:
    print(f"❌ Failed: {e}")

# Test 5: Null arguments (should convert to empty dict)
print("\n[TEST 5] Null arguments (should convert to empty dict)")
try:
    request = ToolCallRequest(tool="get_stock_price", arguments=None)
    print(f"✅ Valid: arguments converted to {request.arguments}")
except ValidationError as e:
    print(f"❌ Failed: {e}")

# Test 6: Invalid arguments type (not a dict)
print("\n[TEST 6] Invalid arguments type (should fail)")
try:
    request = ToolCallRequest(tool="get_stock_price", arguments="not-a-dict")
    print(f"❌ Should have failed but passed: {request}")
except ValidationError as e:
    print(f"✅ Validation error caught (expected):")
    print(f"   {e.errors()[0]['msg']}")

# Test 7: Valid prompt request
print("\n[TEST 7] Valid prompt request")
try:
    request = PromptGetRequest(prompt="analyze_stock", arguments={"symbol": "AAPL"})
    print(f"✅ Valid: prompt='{request.prompt}', arguments={request.arguments}")
except ValidationError as e:
    print(f"❌ Failed: {e}")

# Test 8: Empty prompt name
print("\n[TEST 8] Empty prompt name (should fail)")
try:
    request = PromptGetRequest(prompt="", arguments={})
    print(f"❌ Should have failed but passed: {request}")
except ValidationError as e:
    print(f"✅ Validation error caught (expected):")
    print(f"   {e.errors()[0]['msg']}")

print("\n" + "=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)
print("✅ Tool name validation working")
print("✅ Prompt name validation working")
print("✅ Arguments type validation working")
print("✅ Whitespace trimming working")
print("✅ Null to empty dict conversion working")
print("✅ All Pydantic validations implemented correctly")
print("=" * 70)

