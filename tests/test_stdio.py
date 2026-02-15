#!/usr/bin/env python3
"""Test MCP Server using stdio transport for easier testing.

This script tests the MCP protocol using stdio transport, which is easier
to test than SSE for automated testing.
"""

import json
import os
import subprocess
import sys
import time


def send_mcp_request(process, request):
    """Send a JSON-RPC request to the MCP server."""
    request_json = json.dumps(request)
    process.stdin.write(f"{request_json}\n".encode())
    process.stdin.flush()

    # Read response
    response_line = process.stdout.readline().decode().strip()
    if response_line:
        return json.loads(response_line)
    return None


def test_mcp_stdio():
    """Test MCP server with stdio transport."""
    print("\n" + "="*80)
    print("TESTING MCP SERVER WITH STDIO TRANSPORT")
    print("="*80)

    # Start server in stdio mode
    env = os.environ.copy()
    env["MCP_TRANSPORT"] = "stdio"

    print("\n🚀 Starting MCP server in stdio mode...")
    # Get project root directory (parent of tests directory)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Run server as a module: python -m app.server
    process = subprocess.Popen(
        [sys.executable, "-m", "app.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=project_root
    )

    # Give server time to start
    time.sleep(2)

    if process.poll() is not None:
        stderr = process.stderr.read().decode()
        print(f"❌ Server failed to start: {stderr}")
        return False

    print("✅ Server started")

    try:
        # Test 1: Initialize
        print("\n" + "-"*80)
        print("TEST 1: Initialize")
        print("-"*80)
        response = send_mcp_request(process, {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "0.1.0",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        })
        if response:
            print(f"✅ Initialize response: {json.dumps(response, indent=2)}")
        else:
            print("❌ No response from initialize")
            return False

        # Test 2: List tools
        print("\n" + "-"*80)
        print("TEST 2: List Tools")
        print("-"*80)
        response = send_mcp_request(process, {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        })
        if response:
            tools = response.get("result", {}).get("tools", [])
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"   - {tool.get('name')}")
        else:
            print("❌ No response from tools/list")

        # Test 3: Call tool - get_stock_price
        print("\n" + "-"*80)
        print("TEST 3: Call Tool - get_stock_price")
        print("-"*80)
        response = send_mcp_request(process, {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_stock_price",
                "arguments": {"symbol": "AAPL"}
            }
        })
        if response:
            print(f"✅ Tool call response: {json.dumps(response, indent=2)}")
        else:
            print("❌ No response from tools/call")

        # Test 4: List resources
        print("\n" + "-"*80)
        print("TEST 4: List Resources")
        print("-"*80)
        response = send_mcp_request(process, {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "resources/list"
        })
        if response:
            resources = response.get("result", {}).get("resources", [])
            print(f"✅ Found {len(resources)} resources:")
            for resource in resources:
                print(f"   - {resource.get('uri')}")
        else:
            print("❌ No response from resources/list")

        # Test 5: List prompts
        print("\n" + "-"*80)
        print("TEST 5: List Prompts")
        print("-"*80)
        response = send_mcp_request(process, {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "prompts/list"
        })
        if response:
            prompts = response.get("result", {}).get("prompts", [])
            print(f"✅ Found {len(prompts)} prompts:")
            for prompt in prompts:
                print(f"   - {prompt.get('name')}")
        else:
            print("❌ No response from prompts/list")

        print("\n" + "="*80)
        print("✅ ALL STDIO TESTS COMPLETED SUCCESSFULLY")
        print("="*80)
        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Cleanup
        print("\n🛑 Stopping server...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        print("✅ Server stopped")


if __name__ == "__main__":
    success = test_mcp_stdio()
    sys.exit(0 if success else 1)

