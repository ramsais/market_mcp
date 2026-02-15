#!/usr/bin/env python3
"""Quick demo of the SSE streaming endpoint."""

import requests
import json
import sys

def demo_streaming():
    """Demonstrate SSE streaming capability."""

    print("=" * 70)
    print("SSE STREAMING ENDPOINT DEMO")
    print("=" * 70)
    print()
    print("This demo shows the streamable HTTP protocol in action.")
    print("The server will send events in real-time using Server-Sent Events (SSE).")
    print()

    url = "http://localhost:9001/mcp/tools/call/stream"
    payload = {
        "tool": "get_stock_price",
        "arguments": {"symbol": "AAPL"}
    }

    print(f"POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()
    print("-" * 70)
    print("STREAMING RESPONSE:")
    print("-" * 70)

    try:
        # Stream the response
        with requests.post(url, json=payload, stream=True) as response:
            if response.status_code != 200:
                print(f"Error: HTTP {response.status_code}")
                print(response.text)
                return

            # Process SSE stream
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    print(line)

                    # Parse and format for display
                    if line.startswith("event:"):
                        event_type = line.split(":", 1)[1].strip()
                        print(f"  → Event Type: {event_type}")
                    elif line.startswith("data:"):
                        data_str = line.split(":", 1)[1].strip()
                        try:
                            data = json.loads(data_str)
                            print(f"  → Data: {json.dumps(data, indent=6)}")
                        except:
                            print(f"  → Data: {data_str}")
                    print()

        print("-" * 70)
        print("✓ Stream completed successfully!")
        print()

    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server.")
        print("   Make sure the server is running:")
        print("   python app/http_server.py")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(0)


def demo_comparison():
    """Compare regular vs streaming endpoints."""

    print("=" * 70)
    print("COMPARISON: Regular vs Streaming")
    print("=" * 70)
    print()

    # Regular endpoint
    print("[1] Regular Endpoint (POST /mcp/tools/call)")
    print("-" * 70)
    url = "http://localhost:9001/mcp/tools/call"
    payload = {
        "tool": "get_stock_price",
        "arguments": {"symbol": "AAPL"}
    }

    try:
        response = requests.post(url, json=payload)
        print(f"Status: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")
        print()

    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Start with: python app/http_server.py")
        return

    # Streaming endpoint
    print("[2] Streaming Endpoint (POST /mcp/tools/call/stream)")
    print("-" * 70)
    demo_streaming()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        demo_comparison()
    else:
        demo_streaming()

        print()
        print("=" * 70)
        print("TIP: Run with 'python demo_streaming.py compare' to see")
        print("     regular vs streaming endpoint comparison")
        print("=" * 70)

