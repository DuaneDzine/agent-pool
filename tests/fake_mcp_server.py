#!/usr/bin/env python3
"""Minimal stdio MCP server used by the agent-pool tests.

Speaks newline-delimited JSON-RPC like the real built-in servers, emits a
non-JSON line on stdout to prove the client skips junk, and returns an error
for an unknown method so error propagation can be tested.
"""
import json
import sys


def main() -> int:
    print("fake-mcp: ready", flush=True)  # non-JSON noise; client must skip it
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except ValueError:
            continue
        method = req.get("method")
        req_id = req.get("id")
        if req_id is None:
            continue  # notification
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "fake", "version": "0.0.1"},
            }
        elif method == "tools/list":
            result = {"tools": [{"name": "echo", "description": "echo text"}]}
        elif method == "tools/call":
            params = req.get("params") or {}
            if params.get("name") != "echo":
                print(json.dumps({"jsonrpc": "2.0", "id": req_id,
                                  "error": {"code": -32601, "message": "unknown tool"}}), flush=True)
                continue
            text = (params.get("arguments") or {}).get("text", "")
            result = {"content": [{"type": "text", "text": text}], "isError": False}
        else:
            print(json.dumps({"jsonrpc": "2.0", "id": req_id,
                              "error": {"code": -32601, "message": f"unknown method {method}"}}), flush=True)
            continue
        print(json.dumps({"jsonrpc": "2.0", "id": req_id, "result": result}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
