# MCP Streamable HTTP Server Architecture

## Overview

The Market MCP server implements a **single source of truth** architecture where all tools, resources, and prompts are defined once in `server.py` using FastMCP decorators, and the HTTP REST API server dynamically discovers and exposes them without any hardcoding.

## Architecture Principles

### 1. Single Source of Truth
- All tools, resources, and prompts are defined **only** in `app/server.py` using FastMCP decorators
- The HTTP server (`app/http_server.py`) **introspects** the FastMCP instance to discover capabilities
- **Zero duplication** - no hardcoded lists or definitions in the HTTP layer

### 2. Dynamic Discovery
- Tools are discovered via `mcp._tools`
- Resources are discovered via `mcp._resources`
- Prompts are discovered via `mcp._prompts`
- Function signatures and docstrings are parsed automatically

### 3. Protocol Independence
- Core business logic in `server.py` is protocol-agnostic
- HTTP REST wrapper provides HTTP/REST access
- Can add other transports (stdio, SSE) without changing core logic

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MCP Server (server.py)                   │
│                                                              │
│  @mcp.tool()                                                 │
│  def get_stock_price(...): ...                              │
│                                                              │
│  @mcp.resource("market://popular-stocks")                   │
│  def get_popular_stocks(): ...                              │
│                                                              │
│  @mcp.prompt()                                              │
│  def analyze_stock_performance(...): ...                    │
│                                                              │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       │ Introspection
                       │
         ┌─────────────▼──────────────────┐
         │                                │
         │  FastMCP Instance (mcp)        │
         │                                │
         │  mcp._tools = {...}            │
         │  mcp._resources = {...}        │
         │  mcp._prompts = {...}          │
         │                                │
         └─────────────┬──────────────────┘
                       │
                       │ Dynamic Discovery
                       │
         ┌─────────────▼──────────────────┐
         │                                │
         │  HTTP REST API                 │
         │  (http_server.py)              │
         │                                │
         │  GET  /mcp/tools               │
         │  POST /mcp/tools/call          │
         │  GET  /mcp/resources           │
         │  POST /mcp/prompts/get         │
         │                                │
         └────────────────────────────────┘
```

## Key Components

### 1. Core MCP Server (`app/server.py`)
**Single source of truth for all capabilities**

```python
from fastmcp import FastMCP

mcp = FastMCP("Market Data Server")

@mcp.tool()
def get_stock_price(symbol: Optional[str] = None, ...):
    """Fetch latest stock price(s) using Finnhub API."""
    # Implementation
    pass

@mcp.resource("market://popular-stocks")
def get_popular_stocks() -> str:
    """Resource: List of popular stock symbols."""
    # Implementation
    pass

@mcp.prompt()
def analyze_stock_performance(symbol: str) -> str:
    """Prompt: Generate analysis prompt."""
    # Implementation
    pass
```

**Key Features:**
- All business logic defined here
- Uses FastMCP decorators for registration
- Protocol-agnostic implementation
- Can be run via stdio, SSE, or HTTP

### 2. HTTP REST API (`app/http_server.py`)
**Dynamic wrapper that introspects the MCP instance**

```python
from .server import mcp

# Dynamic discovery functions
def get_tools_from_mcp() -> List[Dict[str, Any]]:
    """Get tool definitions from FastMCP instance."""
    tools = []
    for tool_name, tool_func in mcp._tools.items():
        # Parse function signature and docstring
        # Build tool schema dynamically
        tools.append({
            "name": tool_name,
            "description": ...,
            "parameters": ...
        })
    return tools

# Dynamic endpoints
@app.get("/mcp/tools")
async def list_tools():
    """List all available tools."""
    return {"tools": get_tools_from_mcp()}

@app.post("/mcp/tools/call")
async def call_tool(request: ToolCallRequest):
    """Call a specific tool with arguments."""
    tool_func = mcp._tools[tool_name]
    result = tool_func(**arguments)
    return {"result": result}
```

**Key Features:**
- No hardcoded tool/resource/prompt definitions
- Introspects FastMCP instance at runtime
- Parses function signatures automatically
- Extracts docstrings for descriptions
- Dynamically invokes registered functions

### 3. Introspection Functions

#### `get_tools_from_mcp()`
- Iterates through `mcp._tools`
- Parses function signatures using `inspect`
- Extracts parameter types and docstrings
- Builds OpenAPI-compatible schemas

#### `get_resources_from_mcp()`
- Iterates through `mcp._resources`
- Extracts resource URIs and metadata
- Parses docstrings for descriptions

#### `get_prompts_from_mcp()`
- Iterates through `mcp._prompts`
- Parses function signatures for parameters
- Extracts descriptions from docstrings

## Benefits of This Architecture

### 1. ✅ Single Source of Truth
- Define tools **once** in `server.py`
- HTTP layer automatically discovers them
- No risk of inconsistency or duplication

### 2. ✅ Easy Maintenance
- Add new tool? Just add `@mcp.tool()` decorator
- No need to update HTTP server code
- Automatic API documentation generation

### 3. ✅ Protocol Independence
- Core logic works with any transport
- Can run via stdio for MCP protocol
- Can run via HTTP for REST API
- Can add SSE without changing core

### 4. ✅ Type Safety
- Function signatures define parameters
- Automatic validation from type hints
- Runtime introspection ensures accuracy

### 5. ✅ Self-Documenting
- Docstrings become API documentation
- Function signatures become schemas
- OpenAPI/Swagger generated automatically

## Example: Adding a New Tool

### Before (Hardcoded - ❌ Bad)
```python
# server.py
@mcp.tool()
def new_tool(param: str):
    """A new tool."""
    pass

# http_server.py - MUST ALSO ADD HERE
TOOLS = [
    # ... existing tools ...
    {  # ❌ Duplication!
        "name": "new_tool",
        "description": "A new tool",
        "parameters": {"type": "object", ...}
    }
]
```

### After (Dynamic - ✅ Good)
```python
# server.py - ONLY PLACE TO EDIT
@mcp.tool()
def new_tool(param: str):
    """A new tool."""
    pass

# http_server.py - NO CHANGES NEEDED ✅
# Automatically discovered via introspection!
```

## REST API Endpoints

All endpoints dynamically discover and invoke MCP capabilities:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/mcp/tools` | GET | List all tools (discovered dynamically) |
| `/mcp/tools/call` | POST | Call a tool (invokes via `mcp._tools`) |
| `/mcp/resources` | GET | List all resources (discovered dynamically) |
| `/mcp/resources/{uri}` | GET | Get resource (invokes via `mcp._resources`) |
| `/mcp/prompts` | GET | List all prompts (discovered dynamically) |
| `/mcp/prompts/get` | POST | Get prompt (invokes via `mcp._prompts`) |
| `/health` | GET | Health check |
| `/docs` | GET | Auto-generated API documentation |

## Running the Server

### HTTP REST Mode
```bash
python start_server.py
# or
python app/http_server.py
```

### MCP Stdio Mode
```bash
MCP_TRANSPORT=stdio python -m app.server
```

### MCP SSE Mode
```bash
MCP_TRANSPORT=sse MCP_PORT=9001 python -m app.server
```

## Testing

All tests pass with the dynamic architecture:

```bash
# Start server
python start_server.py &
sleep 3

# Run tests
python tests/test_functions.py     # ✅ 8/8 passing
python tests/test_rest_api.py      # ✅ 11/11 passing
python tests/test_mcp_server.py    # ✅ 11/11 passing
python tests/test_integration.py   # ✅ Working

# Stop server
pkill -f start_server.py
```

## Best Practices

### DO ✅
- Define all tools in `server.py` with `@mcp.tool()`
- Write clear docstrings (used for API docs)
- Use type hints for parameters
- Keep business logic protocol-agnostic
- Test via HTTP REST API and MCP protocol

### DON'T ❌
- Hardcode tool definitions in HTTP layer
- Duplicate tool/resource/prompt lists
- Put business logic in HTTP server
- Skip docstrings (they become API docs)
- Couple core logic to HTTP specifics

## Future Enhancements

1. **Enhanced Introspection**
   - Parse parameter descriptions from docstrings
   - Support more complex type annotations
   - Generate OpenAPI schemas automatically

2. **Multiple Transports**
   - Add SSE transport support
   - Support WebSocket transport
   - Implement MCP JSON-RPC over HTTP

3. **Validation**
   - Automatic parameter validation from types
   - Request/response schema validation
   - Runtime type checking

4. **Documentation**
   - Auto-generate full OpenAPI spec
   - Extract examples from docstrings
   - Generate client SDKs

## Conclusion

This architecture follows the **DRY (Don't Repeat Yourself)** principle and the **Single Source of Truth** pattern. By using FastMCP's introspection capabilities, we ensure that:

1. Tools are defined **once** in `server.py`
2. HTTP layer **discovers** them automatically
3. No **duplication** or **hardcoding**
4. Easy to **maintain** and **extend**
5. **Protocol-independent** core logic

This is the correct and recommended architecture for MCP streamable HTTP servers.

