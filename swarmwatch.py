#!/usr/bin/env python3
"""swarmwatch - minimal supervisor for local services."""
import sys
from typing import Dict, Any
import os
import urllib.request

try:
    import httpx  # type: ignore
except Exception:
    httpx = None


def check_http(url: str, timeout: float = 5.0, auth: str = None) -> Dict[str, Any]:
    try:
        if httpx:
            headers = {"Authorization": auth} if auth else {}
            r = httpx.get(url, timeout=timeout, headers=headers)
            return {"ok": r.status_code < 500, "status": r.status_code}
        req = urllib.request.Request(url)
        if auth:
            req.add_header("Authorization", auth)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"ok": True, "status": r.getcode()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def main():
    key = ""
    for path in [os.path.expanduser("~/.config/litellm/master.key"), os.path.expanduser("~/.config/litellm/.env")]:
        try:
            with open(path) as f:
                for line in f:
                    if line.startswith("LITELLM_MASTER_KEY="):
                        key = line.split("=",1)[1].strip(); break
        except Exception:
            pass
    checks = [
        ("litellm", "http://127.0.0.1:4000/v1/models", key),
        ("ollama-fast", "http://127.0.0.1:11435", None),
        ("ollama", "http://127.0.0.1:11434", None),
        ("opencode", "http://127.0.0.1:4096/healthz", None),
    ]
    for name, url, auth in checks:
        if auth:
            res = check_http(url, auth=f"Bearer {auth}")
        else:
            res = check_http(url)
        status = "OK" if res.get("ok") else "DOWN"
        print(f"[{status}] {name} {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
