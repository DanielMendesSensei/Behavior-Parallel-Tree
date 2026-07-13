#!/usr/bin/env python3
"""Execute hook of the placeholder adapter: stub.

A real adapter would implement the node inside the worktree, only in the node's
folders (kernel only if the plan authorized it). The placeholder knows no stack: it
returns an ok status with an empty payload and logs to stderr.
"""
import json
import sys

HOOK = "execute"


def main():
    try:
        req = json.load(sys.stdin)
    except Exception:
        req = {}
    node = req.get("node", {})
    sys.stderr.write("[%s] placeholder stub, no stack connected\n" % HOOK)
    sys.stdout.write(json.dumps(
        {"status": "ok", "hook": HOOK, "id": node.get("id"), "note": "placeholder stub"},
        ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
