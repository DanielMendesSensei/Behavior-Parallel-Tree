#!/usr/bin/env python3
"""Plan hook of the placeholder adapter: stub.

A real adapter would produce a technical plan here from the spec, the contract, and
the existing code, without writing product code. The placeholder knows no stack: it
returns an ok status with an empty payload and logs to stderr.
"""
import json
import sys

HOOK = "plan"


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
