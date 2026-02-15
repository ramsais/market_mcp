#!/bin/bash
# Quick start script for Market MCP Server

echo "🚀 Market MCP Server - Quick Start"
echo "=================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your FINNHUB_API_KEY"
    echo ""
fi

# Check if FINNHUB_API_KEY is set
if [ -z "$FINNHUB_API_KEY" ] && ! grep -q "^FINNHUB_API_KEY=.*[^_]$" .env 2>/dev/null; then
    echo "⚠️  Warning: FINNHUB_API_KEY not configured"
    echo "   Get your free API key from: https://finnhub.io/register"
    echo "   Then add it to .env file"
    echo ""
fi

echo "📦 Checking dependencies..."
if ! python -c "import fastmcp, finnhub, dotenv" 2>/dev/null; then
    echo "Installing required packages..."
    pip install -r requirements.txt
else
    echo "✅ Dependencies installed"
fi

echo ""
echo "Choose an option:"
echo "  1. Start REST API server (port 9001)"
echo "  2. Run REST API tests"
echo "  3. Run function tests"
echo "  4. Run comprehensive demo"
echo "  5. Show server status"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        echo ""
        echo "🚀 Starting Market MCP REST API Server..."
        echo "   URL: http://localhost:9001"
        echo "   API Docs: http://localhost:9001/docs"
        echo "   Press Ctrl+C to stop"
        echo ""
        python start_server.py
        ;;
    2)
        echo ""
        echo "🧪 Running REST API tests..."
        python tests/test_rest_api.py
        ;;
    3)
        echo ""
        echo "🔧 Running function tests..."
        python test_functions.py
        ;;
    4)
        echo ""
        echo "🎬 Running comprehensive demo..."
        python demo.py
        ;;
    5)
        echo ""
        if lsof -ti:9001 > /dev/null 2>&1; then
            echo "✅ Server is RUNNING on port 9001"
            echo "   PID: $(lsof -ti:9001)"
            echo ""
            echo "Test it:"
            echo "   curl http://localhost:9001/mcp/tools"
        else
            echo "❌ Server is NOT running"
            echo ""
            echo "Start it with:"
            echo "   python start_server.py"
        fi
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

