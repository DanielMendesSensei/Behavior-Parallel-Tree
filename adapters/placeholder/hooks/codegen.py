#!/usr/bin/env python3
"""Codegen hook of the placeholder adapter: stub.

A real adapter would materialize the neutral contract into the stack's types/validators,
writing to __generated__/ deterministically. The placeholder knows no stack: it returns
an ok status with an empty payload and logs to stderr.
"""
import json
import sys

HOOK = "codegen"


def main():
    try:
        req = json.load(sys.stdin)
    except Exception:
        req = {}
    node = req.get("node", {})
    sys.stderr.write("[%s] placeholder stub, no stack connected\n" % HOOK)
    sys.stdout.write(json.dumps(
        {"status": "ok", "hook": HOOK, "id": node.get("id"), "generated": [], "note": "placeholder stub"},
        ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
