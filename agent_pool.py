#!/usr/bin/env python3
"""Minimal local-first agent pool orchestrator."""
import argparse
import json
import os
import sys
from typing import Dict, List

try:
    import httpx  # type: ignore
except Exception:
    httpx = None
import urllib.request


BASE_URL = os.environ.get("LITELLM_BASE_URL", "http://127.0.0.1:4000/v1")


def _load_key():
    for path in [
        os.path.expanduser("~/.config/litellm/master.key"),
        os.path.expanduser("~/.config/litellm/.env"),
    ]:
        try:
            with open(path) as f:
                for line in f:
                    if line.startswith("LITELLM_MASTER_KEY="):
                        return line.split("=", 1)[1].strip().split("#")[0].strip()
        except Exception:
            pass
    return os.environ.get("LITELLM_API_KEY", "")


def chat(messages: List[Dict], model: str = "fast-nothink", max_tokens: int = 512) -> str:
    key = _load_key()
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens}
    if httpx:
        try:
            resp = httpx.post(
                f"{BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json=payload,
                timeout=300.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return (data["choices"][0]["message"].get("content") or "").strip()
        except Exception as e:
            return f"ERR:{e}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(f"{BASE_URL}/chat/completions", data=data)
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=300.0) as r:
            d = json.loads(r.read().decode())
            return (d["choices"][0]["message"].get("content") or "").strip()
    except Exception as e:
        return f"ERR:{e}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--goal", required=True)
    p.add_argument("--model", default="fast-nothink")
    args = p.parse_args()
    print("=== AGENT POOL (local-first) ===")
    print("Goal:", args.goal)
    print("Model:", args.model)
    plan = chat(
        [
            {
                "role": "system",
                "content": "You are a planner. Return a short, concrete plan (3-5 steps max). Be concise.",
            },
            {"role": "user", "content": args.goal},
        ],
        model=args.model,
        max_tokens=256,
    )
    print("\n--- PLANNER ---")
    print(plan)
    code = chat(
        [
            {
                "role": "system",
                "content": "You are a coder. Write minimal, safe code to satisfy the goal. Return ONLY the answer - no preamble.",
            },
            {"role": "user", "content": f"Goal: {args.goal}\nPlan: {plan}"},
        ],
        model=args.model,
        max_tokens=512,
    )
    print("\n--- CODER ---")
    print(code)
    review = chat(
        [
            {
                "role": "system",
                "content": "You are a reviewer. Give 2-3 bullets of feedback + a verdict (OK/ISSUES).",
            },
            {
                "role": "user",
                "content": f"Goal: {args.goal}\nPlan: {plan}\nCode: {code}",
            },
        ],
        model=args.model,
        max_tokens=256,
    )
    print("\n--- REVIEWER ---")
    print(review)


if __name__ == "__main__":
    sys.exit(main())
