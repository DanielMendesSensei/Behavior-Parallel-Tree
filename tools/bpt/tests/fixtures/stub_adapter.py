#!/usr/bin/env python3
"""Scriptable stub adapter for the runner tests.

It honors the real protocol (one JSON in, one JSON out, logs on stderr, exit 0
for a business result) and knows no stack, which is the point: the runner must
be exercised without any language being involved.

Driven by two environment variables:
  BPT_STUB_LOG   path of a JSONL file; every request envelope it receives is
                 appended, so a test can assert on what the core actually sent
  BPT_STUB_PLAN  JSON, all keys optional:
                 {"fail": {"verify": 2}}  -> verify returns needs_changes while
                                             attempt <= 2
                 {"always_fail": ["review"]}
                 {"broken": ["execute"]}  -> exit != 0, the adapter itself broke
                 {"tokens": 100}          -> reported per hook call
"""
import json
import os
import sys

HOOKS = ["scaffold", "plan", "execute", "verify", "review", "codegen"]


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in HOOKS:
        sys.stderr.write("usage: stub_adapter <hook>\n")
        return 2
    hook = sys.argv[1]
    try:
        req = json.load(sys.stdin)
    except Exception:
        req = {}

    log = os.environ.get("BPT_STUB_LOG")
    if log:
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(req, ensure_ascii=False) + "\n")

    plan = json.loads(os.environ.get("BPT_STUB_PLAN") or "{}")
    attempt = req.get("attempt", 1)

    if hook in (plan.get("broken") or []):
        sys.stderr.write("[%s] pretending the adapter itself broke\n" % hook)
        return 3

    fail_until = (plan.get("fail") or {}).get(hook)
    always = hook in (plan.get("always_fail") or [])
    failing = always or (fail_until is not None and attempt <= fail_until)

    out = {"status": "needs_changes" if failing else "ok"}
    if failing:
        out["findings"] = [{"hook": hook, "attempt": attempt, "detail": "stub failure"}]
    if hook == "plan":
        out["artifacts"] = {"plan": "plan-for-attempt-%d" % attempt}
    if plan.get("tokens"):
        out["usage"] = {"tokens": int(plan["tokens"])}

    sys.stderr.write("[%s] attempt %s -> %s\n" % (hook, attempt, out["status"]))
    sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
