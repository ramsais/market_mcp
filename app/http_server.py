"""HTTP REST API Server for Market MCP.

This server provides REST API endpoints for stock market data by dynamically
introspecting the FastMCP instance. Tools, resources, and prompts are discovered
at runtime from the MCP server definition, ensuring a single source of truth.

Architecture:
- Uses FastMCP instance as the single source of truth
- Dynamically discovers tools, resources, and prompts via introspection
- Provides HTTP REST API wrapper around MCP protocol
- No hardcoded definitions - all come from server.py decorators

Endpoints:
- GET  /mcp/tools          - List all available tools
- POST /mcp/tools/call     - Call a specific tool
- GET  /mcp/resources      - List all resources
- GET  /mcp/resources/{uri} - Get a specific resource
- GET  /mcp/prompts        - List all prompts
- POST /mcp/prompts/get    - Get a specific prompt
- GET  /health             - Health check
- GET  /docs               - Interactive API documentation
"""

import os
import json
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
import uvicorn
from dotenv import load_dotenv

# Import MCP instance and server functions
from .server import mcp, _finnhub_client
from .utils.logger import get_logger, kv, set_correlation_id

load_dotenv(override=False)
log = get_logger(__name__)

app = FastAPI(
    title="Market MCP REST API",
    description="HTTP REST API for stock market data",
    version="1.0.0"
)


# Helper functions to dynamically introspect MCP instance
def get_tools_list() -> List[Dict[str, Any]]:
    """Dynamically get list of tools from MCP instance."""
    tools = []
    for tool_name, tool_obj in mcp._tool_manager._tools.items():
        # FunctionTool objects have name, description, and parameters attributes
        tools.append({
            "name": tool_obj.name,
            "description": tool_obj.description.strip().split("\n")[0] if tool_obj.description else "No description available",
            "parameters": tool_obj.parameters if hasattr(tool_obj, 'parameters') else {}
        })
    return tools


def get_resources_list() -> List[Dict[str, Any]]:
    """Dynamically get list of resources from MCP instance."""
    resources = []
    for uri, resource_obj in mcp._resource_manager._resources.items():
        # Extract description from the resource function
        doc = ""
        if hasattr(resource_obj, 'fn') and resource_obj.fn.__doc__:
            doc = resource_obj.fn.__doc__
        elif hasattr(resource_obj, '__doc__') and resource_obj.__doc__:
            doc = resource_obj.__doc__

        resources.append({
            "uri": uri,
            "name": uri.split("://")[1] if "://" in uri else uri,
            "description": doc.strip().split("\n")[0] if doc else "No description available",
            "mimeType": "application/json"
        })
    return resources


def get_prompts_list() -> List[Dict[str, Any]]:
    """Dynamically get list of prompts from MCP instance."""
    prompts = []
    for prompt_name, prompt_obj in mcp._prompt_manager._prompts.items():
        # Extract description and parameters from the prompt function
        doc = ""
        if hasattr(prompt_obj, 'fn') and prompt_obj.fn.__doc__:
            doc = prompt_obj.fn.__doc__
        elif hasattr(prompt_obj, '__doc__') and prompt_obj.__doc__:
            doc = prompt_obj.__doc__

        # Get parameters from function annotations
        params = {}
        if hasattr(prompt_obj, 'fn'):
            annotations = getattr(prompt_obj.fn, "__annotations__", {})
            for param_name, param_type in annotations.items():
                if param_name != "return":
                    params[param_name] = {
                        "type": str(param_type.__name__ if hasattr(param_type, "__name__") else param_type)
                    }

        prompts.append({
            "name": prompt_name,
            "description": doc.strip().split("\n")[0] if doc else "No description available",
            "parameters": params
        })
    return prompts


# Request/Response Models
class ToolCallRequest(BaseModel):
    tool: str
    arguments: Dict[str, Any] = {}

    @field_validator('tool')
    @classmethod
    def validate_tool_name(cls, v: str) -> str:
        """Validate tool name is not empty."""
        if not v or not v.strip():
            raise ValueError("Tool name cannot be empty")
        return v.strip()


class PromptGetRequest(BaseModel):
    prompt: str
    arguments: Dict[str, Any] = {}

    @field_validator('prompt')
    @classmethod
    def validate_prompt_name(cls, v: str) -> str:
        """Validate prompt name is not empty."""
        if not v or not v.strip():
            raise ValueError("Prompt name cannot be empty")
        return v.strip()



@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Market MCP REST API",
        "version": "1.0.0",
        "description": "HTTP REST API for stock market data",
        "endpoints": {
            "tools": "/mcp/tools",
            "resources": "/mcp/resources",
            "prompts": "/mcp/prompts",
            "health": "/health",
            "docs": "/docs"
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
    """List all available tools dynamically from MCP instance."""
    set_correlation_id()
    tools = get_tools_list()
    log.info("app.list_tools %s", kv(count=len(tools)))
    return {
        "tools": tools
    }


@app.post("/mcp/tools/call")
async def call_tool(request: ToolCallRequest):
    """Call a specific tool dynamically via MCP instance."""
    set_correlation_id()
    tool_name = request.tool
    arguments = request.arguments

    log.info("app.call_tool %s", kv(tool=tool_name, arguments=arguments))

    try:
        # Check if tool exists in MCP instance
        if tool_name not in mcp._tool_manager._tools:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

        # Get the tool object and call its function
        tool_obj = mcp._tool_manager._tools[tool_name]
        result = tool_obj.fn(**arguments)

        return {"result": result}

    except TypeError as e:
        # Handle missing or invalid arguments
        log.error("app.tool_argument_error %s", kv(tool=tool_name, error=str(e)))
        raise HTTPException(status_code=400, detail=f"Invalid arguments for tool '{tool_name}': {str(e)}")
    except ValueError as e:
        # Handle validation errors
        log.error("app.tool_validation_error %s", kv(tool=tool_name, error=str(e)))
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        log.error("app.tool_call_error %s", kv(tool=tool_name, error=str(e)))
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/mcp/resources")
async def list_resources():
    """List all available resources dynamically from MCP instance."""
    set_correlation_id()
    resources = get_resources_list()
    log.info("app.list_resources %s", kv(count=len(resources)))
    return {
        "resources": resources
    }


@app.get("/mcp/resources/{resource_uri:path}")
async def get_resource(resource_uri: str):
    """Get a specific resource by URI dynamically via MCP instance."""
    set_correlation_id()
    log.info("app.get_resource %s", kv(uri=resource_uri))

    # Add market:// prefix if not present
    if not resource_uri.startswith("market://"):
        resource_uri = f"market://{resource_uri}"

    try:
        # Check if resource exists in MCP instance
        if resource_uri not in mcp._resource_manager._resources:
            raise HTTPException(status_code=404, detail=f"Resource '{resource_uri}' not found")

        # Get the resource object and call its function dynamically
        resource_obj = mcp._resource_manager._resources[resource_uri]
        result = resource_obj.fn() if hasattr(resource_obj, 'fn') else resource_obj()

        # Parse JSON result if it's a string
        if isinstance(result, str):
            try:
                data = json.loads(result)
            except json.JSONDecodeError:
                data = result
        else:
            data = result

        return {"data": data}

    except HTTPException:
        raise
    except Exception as e:
        log.error("app.resource_error %s", kv(uri=resource_uri, error=str(e)))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/prompts")
async def list_prompts():
    """List all available prompts dynamically from MCP instance."""
    set_correlation_id()
    prompts = get_prompts_list()
    log.info("app.list_prompts %s", kv(count=len(prompts)))
    return {
        "prompts": prompts
    }


@app.post("/mcp/prompts/get")
async def get_prompt(request: PromptGetRequest):
    """Get a specific prompt with arguments - dynamically invoked via MCP instance."""
    set_correlation_id()
    prompt_name = request.prompt
    arguments = request.arguments

    log.info("app.get_prompt %s", kv(prompt=prompt_name, arguments=arguments))

    try:
        # Check if prompt exists in MCP instance
        if prompt_name not in mcp._prompt_manager._prompts:
            raise HTTPException(status_code=404, detail=f"Prompt '{prompt_name}' not found")

        # Get the prompt object and call its function
        prompt_obj = mcp._prompt_manager._prompts[prompt_name]
        prompt_text = prompt_obj.fn(**arguments) if hasattr(prompt_obj, 'fn') else prompt_obj(**arguments)

        return {"prompt": prompt_text}

    except TypeError as e:
        # Handle missing or invalid arguments
        log.error("app.prompt_argument_error %s", kv(prompt=prompt_name, error=str(e)))
        raise HTTPException(status_code=400, detail=f"Invalid arguments for prompt '{prompt_name}': {str(e)}")
    except ValueError as e:
        # Handle validation errors
        log.error("app.prompt_validation_error %s", kv(prompt=prompt_name, error=str(e)))
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")
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

