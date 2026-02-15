#!/usr/bin/env python3
"""Start the Market MCP REST API Server.

This is the main entry point for starting the HTTP REST API server.
The server provides standard REST endpoints for stock market data.

Usage:
    python start_server.py

Endpoints:
    - GET  /mcp/tools             - List all tools
    - POST /mcp/tools/call        - Call a tool
    - GET  /mcp/resources         - List all resources
    - GET  /mcp/resources/{uri}   - Get a resource
    - GET  /mcp/prompts           - List all prompts
    - POST /mcp/prompts/get       - Get a prompt
    - GET  /health                - Health check
    - GET  /docs                  - Interactive API documentation
"""

import os
import sys

# Set default environment variables
os.environ.setdefault("MCP_PORT", "9001")
os.environ.setdefault("LOG_LEVEL", "INFO")

# Check for FINNHUB_API_KEY
if not os.getenv("FINNHUB_API_KEY"):
    print("⚠️  Warning: FINNHUB_API_KEY not set!")
    print("   Please set it in .env file or environment")
    print("   Get a free key from: https://finnhub.io/register")
    print()

# Import and run server
port = int(os.getenv("MCP_PORT", "9001"))

print("="*70)
print("🚀 Market MCP REST API Server")
print("="*70)
print(f"Port:     {port}")
print(f"URL:      http://localhost:{port}")
print(f"API Docs: http://localhost:{port}/docs")
print("="*70)
print()
print("Available endpoints:")
print(f"  GET  http://localhost:{port}/mcp/tools")
print(f"  POST http://localhost:{port}/mcp/tools/call")
print(f"  GET  http://localhost:{port}/mcp/resources")
print(f"  GET  http://localhost:{port}/mcp/prompts")
print(f"  GET  http://localhost:{port}/health")
print(f"  GET  http://localhost:{port}/docs")
print()
print("Press Ctrl+C to stop the server")
print("="*70)
print()

try:
    # Start the HTTP server - import from app package
    from app.http_server import start_server as start_http_server
    start_http_server(port=port)
except KeyboardInterrupt:
    print("\n\n✅ Server stopped")
    sys.exit(0)
except Exception as e:
    print(f"\n❌ Error starting server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

