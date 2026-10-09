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
