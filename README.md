# agent-pool (minimal local-first orchestrator)

A tiny orchestrator that talks to LiteLLM (127.0.0.1:4000) with a 3-agent
pool: planner, coder, reviewer. Runs fully offline by default (uses
gateway/fast, gateway/fast-nothink, gateway/big) and falls back to cloud
only if explicitly requested.

## Goals
- Keep it simple (stdlib + httpx if present, else urllib)
- One file: agent_pool.py
- Deterministic flow for small tasks
- Easy to extend to more agents

## Quick start
python agent_pool.py --goal "write a hello world script"

## MCP tools (stdio)

`agent_pool_tools.py` is a minimal MCP stdio client (initialize -> initialized
-> tools/list / tools/call) that keeps the child process open and matches
responses by request id. `mcp_stdio.py` is a thin CLI over it:

```
MCP_SERVER_PYTHON=~/.local/share/odysseus-mcp/venv/bin/python \
  python3 mcp_stdio.py "$MCP_SERVER_PYTHON" /path/to/server.py
MCP_SERVER_PYTHON=... python3 mcp_stdio.py ... --call manage_memory '{"action":"list"}'
```

The built-in Odysseus MCP servers use the v1 low-level `Server` decorator API,
so they must run under an interpreter with `mcp<2` (the system interpreter has
`mcp` 2.x and cannot import them). `server_python()` picks that interpreter
automatically; see `setups/odysseus-mcp.sh` to create the pinned venv.

## Tests
python tests/test_pool.py
