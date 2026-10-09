#!/usr/bin/env python3
"""Call MCP servers via stdio (no HTTP needed)."""
import json
import subprocess
import sys
from typing import List, Dict, Any


def list_tools(cmd: List[str]) -> Dict[str, Any]:
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    # Send initialize + tools/list
    init = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "agent-pool", "version": "0.1.0"}},
    }
    tools_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    try:
        out1, _ = proc.communicate(json.dumps(init) + "\n" + json.dumps(tools_req) + "\n", timeout=10)
    except Exception as e:
        proc.kill()
        return {"error": str(e)}
    # parse last json line with result
    for line in out1.splitlines():
        try:
            obj = json.loads(line)
            if obj.get("id") == 2 and "result" in obj:
                return obj
        except Exception:
            pass
    return {"error": "no result"}


if __name__ == "__main__":
    cmd = sys.argv[1:]
    if not cmd:
        print("usage: mcp_stdio.py <cmd...>")
        sys.exit(1)
    print(json.dumps(list_tools(cmd)))
