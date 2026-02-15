# Market MCP Server

A streamable HTTP MCP (Model Context Protocol) server that provides stock market data through the Finnhub API.

## Features

- **Tools**: Get stock prices, search companies
- **Resources**: Popular stocks list, market indices
- **Prompts**: Stock analysis and comparison prompts
- **HTTP Streaming**: SSE (Server-Sent Events) transport on port 9001

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Edit `.env` and add your Finnhub API key:
```
FINNHUB_API_KEY=your_actual_api_key_here
```

Get a free API key from: https://finnhub.io/register

### 3. Start the Server

**Option A: Using start_server.py (recommended)**
```bash
python start_server.py
```

**Option B: Using server.py directly**
```bash
# SSE transport (HTTP streaming)
MCP_TRANSPORT=sse MCP_PORT=9001 python server.py

# stdio transport (for direct MCP integration)
MCP_TRANSPORT=stdio python server.py
```

The server will start on `http://localhost:9001`

## Testing

Run the comprehensive test suite:

```bash
# Make sure the server is running first
python test_mcp_server.py
```

The test suite validates:
- Server info endpoint
- Tool listing and execution
- Resource access
- Prompt generation
- Error handling

### Manual Testing with curl

**List tools:**
```bash
curl http://localhost:9001/mcp/tools
```

**Get stock price:**
```bash
curl -X POST http://localhost:9001/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool":"get_stock_price",
    "arguments":{"symbol":"AAPL"}
  }'
```

**Search company:**
```bash
curl -X POST http://localhost:9001/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool":"search_company",
    "arguments":{"company_name":"Microsoft"}
  }'
```

**List resources:**
```bash
curl http://localhost:9001/mcp/resources
```

**Read resource:**
```bash
curl http://localhost:9001/mcp/resources/popular-stocks
```

## Available Tools

### get_stock_price
Get latest stock price(s) from Finnhub.

**Parameters:**
- `symbol` (optional): Single stock symbol (e.g., "AAPL")
- `company_name` (optional): Single company name (e.g., "Apple")
- `symbols` (optional): List of stock symbols
- `company_names` (optional): List of company names

**Example:**
```json
{
  "symbol": "AAPL",
  "price": 150.25,
  "currency": "USD",
  "timestamp": 1708012800,
  "high": 151.50,
  "low": 149.80,
  "open": 150.00,
  "previous_close": 149.90
}
```

### search_company
Search for companies by name.

**Parameters:**
- `company_name`: Company name to search for

**Example:**
```json
[
  {
    "symbol": "MSFT",
    "description": "Microsoft Corporation",
    "type": "Common Stock",
    "displaySymbol": "MSFT"
  }
]
```

## Available Resources

- `market://popular-stocks` - List of popular stock symbols
- `market://indices` - Major market indices symbols

## Available Prompts

- `analyze_stock_performance` - Generate stock analysis prompt
- `compare_stocks` - Generate stock comparison prompt

## Project Structure

```
market_mcp/
├── server.py              # Main MCP server
├── logger.py              # Structured logging
├── timing.py              # Timing decorators
├── requirements.txt       # Python dependencies
├── start_server.py        # Server startup script
├── test_mcp_server.py     # Comprehensive test suite
├── .env.example           # Environment configuration template
└── README.md              # This file
```

## Environment Variables

- `FINNHUB_API_KEY` - Your Finnhub API key (required)
- `MCP_TRANSPORT` - Transport type: "sse" or "stdio" (default: "sse")
- `MCP_PORT` - Port for SSE transport (default: 9001)
- `LOG_LEVEL` - Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)

## Troubleshooting

### Server won't start
- Check if port 9001 is already in use
- Verify FINNHUB_API_KEY is set in .env
- Check logs for errors

### Tests fail
- Ensure server is running before running tests
- Verify FINNHUB_API_KEY is valid
- Check network connectivity

### No stock data returned
- Verify API key is valid and not rate-limited
- Check if stock symbol is correct
- Try a different stock symbol (e.g., "AAPL", "MSFT")

## License

MIT

