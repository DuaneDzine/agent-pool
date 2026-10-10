#!/usr/bin/env python3
"""Agent pool that can call MCP tools via stdio."""
import json
import subprocess
import sys
from typing import Dict, Any, List, Optional


class MCPClient:
    def __init__(self, cmd: List[str]):
        self.cmd = cmd
        self.proc = None
        self._id = 0

    def start(self):
        self.proc = subprocess.Popen(
            self.cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        # initialize
        self._rpc("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "agent-pool", "version": "0.1.0"},
        })

    def _rpc(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.proc:
            raise RuntimeError("not started")
        self._id += 1
        req = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params or {}}
        self.proc.stdin.write(json.dumps(req) + "\n")
        self.proc.stdin.flush()
        while True:
            line = self.proc.stdout.readline()
            if not line:
                break
            try:
                obj = json.loads(line)
                if obj.get("id") == self._id and "result" in obj:
                    return obj["result"]
            except Exception:
                continue
        return {"error": "no result"}

    def list_tools(self):
        return self._rpc("tools/list")

    def call_tool(self, name: str, arguments: Dict[str, Any] = None):
        return self._rpc("tools/call", {"name": name, "arguments": arguments or {}})

    def close(self):
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except Exception:
                self.proc.kill()


def main():
    # try memory server first
    cmd = ["python3", "/home/dzine/Work/odysseus/mcp_servers/memory_server.py"]
    try:
        c = MCPClient(cmd)
        c.start()
        tools = c.list_tools()
        print("tools:", json.dumps(tools)[:200])
        # try a simple call if available
        if tools.get("tools"):
            t = tools["tools"][0]
            print("calling:", t["name"])
            res = c.call_tool(t["name"], {})
            print(json.dumps(res)[:200])
        c.close()
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
