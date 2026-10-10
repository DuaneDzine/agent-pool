#!/usr/bin/env python3
"""Call MCP servers via stdio (no HTTP bridge needed).

Wraps :class:`agent_pool_tools.MCPClient` so a full exchange (initialize ->
initialized -> tools/list / tools/call) can be run from the shell.
"""
import json
import sys
from typing import Any, Dict, List, Optional

from agent_pool_tools import MCPClient, MCPError


def list_tools(cmd: List[str]) -> Dict[str, Any]:
    with MCPClient(cmd) as client:
        return {"tools": client.list_tools()}


def call_tool(cmd: List[str], name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    with MCPClient(cmd) as client:
        return {"result": client.call_tool(name, arguments)}


def main(argv: List[str]) -> int:
    if len(argv) < 1:
        print("usage: mcp_stdio.py <cmd...> [--call TOOL [JSON_ARGS]]")
        return 2
    call_index = argv.index("--call") if "--call" in argv else -1
    if call_index != -1:
        cmd = argv[:call_index]
        name = argv[call_index + 1]
        args = json.loads(argv[call_index + 2]) if len(argv) > call_index + 2 else {}
    else:
        cmd, name, args = argv, None, None
    try:
        result = call_tool(cmd, name, args) if name else list_tools(cmd)
    except MCPError as e:
        print(json.dumps({"error": str(e)}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
