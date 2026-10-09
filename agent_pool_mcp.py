#!/usr/bin/env python3
"""Agent pool that can call MCP tools via JSON-RPC over HTTP if available."""
import json
import os
import urllib.request


def call_mcp(server_url, method, params=None, timeout=30.0):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": 1,
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(server_url, data=data)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Try to list tools from a known MCP (e.g. memory server if HTTP exposed)
    for url in ["http://127.0.0.1:8765/mcp", "http://127.0.0.1:8081/mcp", "http://127.0.0.1:8080/mcp"]:
        print(call_mcp(url, "tools/list"))
        break
