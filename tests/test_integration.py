"""Simple integration test for Market MCP Server SSE endpoints.

This test validates that the server is running and endpoints are accessible.
"""

import json
import os
import subprocess
import sys
import time

import requests


def check_port_in_use(port: int) -> bool:
    """Check if port is in use."""
    result = subprocess.run(
        ["lsof", "-ti", f":{port}"],
        capture_output=True,
        text=True
    )
    return result.returncode == 0


def test_rest_endpoints():
    """Test REST API endpoints."""
    print("\n" + "="*80)
    print("TEST: REST API Endpoints")
    print("="*80)

    try:
        # Test health endpoint
        response = requests.get("http://localhost:9001/health", timeout=2)
        print(f"✅ Health endpoint: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ Health check failed")
            return False

        # Test tools endpoint
        response = requests.get("http://localhost:9001/mcp/tools", timeout=2)
        print(f"✅ Tools endpoint: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data.get('tools', []))} tools")
            print("✅ REST API endpoints are accessible")
            return True
        else:
            print(f"❌ Tools endpoint returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def test_with_mcp_client():
    """Test using MCP client library if available."""
    print("\n" + "="*80)
    print("TEST: Using MCP Client")
    print("="*80)

    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        print("✅ MCP client library available")
        # Note: SSE transport would need different client setup
        print("⚠️  SSE transport requires SSE-specific client (not implemented in this test)")
        return True
    except ImportError:
        print("⚠️  MCP client library not available")
        print("   Install with: pip install mcp")
        return True  # Not a failure, just a skip


def main():
    """Run simple integration tests."""
    print("\n" + "🚀" * 40)
    print("MARKET MCP SERVER - SIMPLE INTEGRATION TEST")
    print("🚀" * 40)

    # Check if server is running
    print("\n📊 Checking server status...")
    if not check_port_in_use(9001):
        print("❌ Server is not running on port 9001")
        print("\nTo start the server, run:")
        print("  python start_server.py")
        print("\nor")
        print("  MCP_TRANSPORT=sse MCP_PORT=9001 python server.py")
        return False

    print("✅ Server is running on port 9001")

    # Test REST API endpoints
    if not test_rest_endpoints():
        return False

    # Try MCP client
    test_with_mcp_client()

    print("\n" + "="*80)
    print("INTEGRATION TEST INFORMATION")
    print("="*80)
    print("""
The server is running in SSE (Server-Sent Events) mode on port 9001.

SSE is a streaming protocol that maintains a persistent connection.
To properly test the MCP tools, resources, and prompts, you need to:

1. Use an MCP client library that supports SSE transport
2. Or use the stdio transport mode for simpler testing

STDIO MODE TEST:
To test with stdio mode (easier for testing):
  python -c "import json; import subprocess; proc = subprocess.Popen(
    ['python', 'server.py'], 
    env={'MCP_TRANSPORT': 'stdio'},
    stdin=subprocess.PIPE, 
    stdout=subprocess.PIPE, 
    stderr=subprocess.PIPE
  ); print('Server started in stdio mode')"

DIRECT FUNCTION TEST:
You can also test the functions directly:
  python -c "from app.server import get_single_stock_price; print(get_single_stock_price(symbol='AAPL'))"

SSE CLIENT:
For SSE mode, you need an SSE-compatible MCP client.
The FastMCP SSE transport is designed for integration with Claude Desktop
or other MCP-compatible applications.
""")

    print("\n✅ Basic integration tests passed!")
    print("   The server is running and accessible.")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

