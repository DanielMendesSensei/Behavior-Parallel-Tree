#!/usr/bin/env python3
"""Hook execute do adapter placeholder: stub.

Um adapter real implementaria o no dentro do worktree, so nas pastas do no (kernel
apenas se o plano autorizou). O placeholder nao conhece stack: retorna status ok
com payload vazio e loga em stderr.
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
    sys.stderr.write("[%s] placeholder stub, nenhuma stack conectada\n" % HOOK)
    sys.stdout.write(json.dumps(
        {"status": "ok", "hook": HOOK, "id": node.get("id"), "note": "placeholder stub"},
        ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
