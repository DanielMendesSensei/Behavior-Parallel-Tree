#!/usr/bin/env python3
"""Review hook of the placeholder adapter: stub.

A real adapter would do the semantic review (adherence to the spec, the contract, and
the kernel rule), returning approved or needs_changes. The placeholder knows no stack:
it returns an ok status with an empty approved verdict and logs to stderr.
"""
import json
import sys

HOOK = "review"


def main():
    try:
        req = json.load(sys.stdin)
    except Exception:
        req = {}
    node = req.get("node", {})
    sys.stderr.write("[%s] placeholder stub, no stack connected\n" % HOOK)
    sys.stdout.write(json.dumps(
        {"status": "ok", "hook": HOOK, "id": node.get("id"), "verdict": "approved", "note": "placeholder stub"},
        ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
