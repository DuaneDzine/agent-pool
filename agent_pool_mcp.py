#!/usr/bin/env python3
"""Agent pool discovery of MCP servers exposed over HTTP (SSE/JSON-RPC)."""
import json
import urllib.request
from typing import Dict, Any, List


def call_jsonrpc(url: str, method: str, params: Dict[str, Any] = None, timeout: float = 10.0) -> Dict[str, Any]:
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": 1,
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}


def discover_mcp() -> List[str]:
    urls = []
    for p in [8770, 8771, 8765, 8766, 8767, 8768, 8080, 8081, 8082, 5000, 3000]:
        for path in ["/mcp", "/rpc", "/jsonrpc", "/v1/mcp", "/sse"]:
            urls.append(f"http://127.0.0.1:{p}{path}")
    return urls


def main():
    for url in discover_mcp():
        res = call_jsonrpc(url, "tools/list")
        if "error" not in res:
            print("FOUND", url)
            print(json.dumps(res)[:100])
            return
    print("No MCP HTTP endpoints found")


if __name__ == "__main__":
    main()
