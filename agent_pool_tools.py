#!/usr/bin/env python3
"""Agent pool tool client: call MCP servers over stdio.

The MCP stdio transport is newline-delimited JSON-RPC. A correct client keeps
the child process open, sends one request at a time, and reads responses until
it sees the matching ``id``. Closing stdin to "finish" the exchange (as an
earlier version did) is a race that drops every request after ``initialize``.
"""
import json
import os
import subprocess
import sys
import threading
from typing import Any, Dict, List, Optional

DEFAULT_MEMORY_SERVER = "/home/dzine/Work/odysseus/mcp_servers/memory_server.py"


def server_python() -> str:
    """Interpreter that can run the built-in MCP servers.

    Those servers use the v1 low-level ``Server`` decorator API, so they need
    ``mcp<2``. The system interpreter currently has ``mcp`` 2.x, which cannot
    import them; the dedicated venv (see setups/odysseus-mcp.sh) pins v1.
    """
    override = os.environ.get("MCP_SERVER_PYTHON")
    if override:
        return override
    for candidate in (
        "~/.local/share/odysseus-mcp/venv/bin/python",
        "~/.local/share/uv/tools/mcp-proxy/bin/python",
    ):
        path = os.path.expanduser(candidate)
        if os.path.exists(path):
            return path
    return sys.executable


class MCPError(RuntimeError):
    """Raised when the server cannot be reached, exits, or returns an error."""


class MCPClient:
    def __init__(self, cmd: List[str], version: str = "0.2.0"):
        self.cmd = cmd
        self.version = version
        self.proc: Optional[subprocess.Popen] = None
        self._id = 0
        self._stderr: List[str] = []
        self._stderr_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self.proc:
            return
        self.proc = subprocess.Popen(
            self.cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        self._stderr_thread = threading.Thread(target=self._drain_stderr, daemon=True)
        self._stderr_thread.start()
        try:
            self._rpc("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "agent-pool", "version": self.version},
            })
            self._notify("notifications/initialized")
        except MCPError:
            self.close()
            raise

    def _drain_stderr(self) -> None:
        stderr = self.proc.stderr if self.proc else None
        if not stderr:
            return
        for line in stderr:
            self._stderr.append(line.rstrip("\n"))
            if len(self._stderr) > 200:
                del self._stderr[0]

    def _stderr_tail(self) -> str:
        return "\n".join(self._stderr[-20:])

    def _write(self, obj: Dict[str, Any]) -> None:
        if not self.proc or not self.proc.stdin:
            raise MCPError("client not started")
        try:
            self.proc.stdin.write(json.dumps(obj) + "\n")
            self.proc.stdin.flush()
        except (BrokenPipeError, ValueError, OSError) as e:
            raise MCPError(f"server closed stdin ({e})\n{self._stderr_tail()}")

    def _notify(self, method: str, params: Optional[Dict[str, Any]] = None) -> None:
        self._write({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def _rpc(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        if not self.proc or not self.proc.stdout:
            raise MCPError("client not started")
        self._id += 1
        req_id = self._id
        self._write({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params or {}})
        while True:
            line = self.proc.stdout.readline()
            if not line:
                tail = self._stderr_tail()
                raise MCPError(
                    f"server exited before replying to {method}"
                    + (f"\n{tail}" if tail else "")
                )
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            if not isinstance(obj, dict) or obj.get("id") != req_id:
                continue
            if "error" in obj:
                raise MCPError(f"{method}: {obj['error']}")
            return obj.get("result")

    def list_tools(self) -> List[Dict[str, Any]]:
        result = self._rpc("tools/list") or {}
        return result.get("tools", [])

    def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        return self._rpc("tools/call", {"name": name, "arguments": arguments or {}})

    def close(self) -> None:
        proc, self.proc = self.proc, None
        if not proc:
            return
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            try:
                if stream:
                    stream.close()
            except Exception:
                pass

    def __enter__(self) -> "MCPClient":
        self.start()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


def main() -> int:
    server = os.environ.get("MCP_MEMORY_SERVER", DEFAULT_MEMORY_SERVER)
    cmd = [server_python(), server]
    try:
        with MCPClient(cmd) as client:
            tools = client.list_tools()
            print("tools:", json.dumps(tools)[:500])
            if tools:
                name = tools[0]["name"]
                print("calling:", name)
                print(json.dumps(client.call_tool(name, {}))[:500])
    except MCPError as e:
        print(f"MCP error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
