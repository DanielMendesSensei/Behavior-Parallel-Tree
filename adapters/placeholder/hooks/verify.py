#!/usr/bin/env python3
"""Verify hook of the placeholder adapter: stub.

A real adapter would run the spec scenarios (on the side's surface) plus the unit
tests, and check import direction (a behavior never imports a behavior; the kernel
never imports a behavior). The placeholder knows no stack: it returns an ok status
with an empty payload and logs to stderr.
"""
import json
import sys

HOOK = "verify"


def main():
    try:
        req = json.load(sys.stdin)
    except Exception:
        req = {}
    node = req.get("node", {})
    sys.stderr.write("[%s] placeholder stub, no stack connected\n" % HOOK)
    sys.stdout.write(json.dumps(
        {"status": "ok", "hook": HOOK, "id": node.get("id"), "scenarios": [], "note": "placeholder stub"},
        ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
