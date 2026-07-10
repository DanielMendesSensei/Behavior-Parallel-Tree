#!/usr/bin/env python3
"""Hook review do adapter placeholder: stub.

Um adapter real faria a revisao semantica (aderencia a spec, ao contrato e a regra
de kernel), retornando approved ou needs_changes. O placeholder nao conhece stack:
retorna status ok com veredito approved vazio e loga em stderr.
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
    sys.stderr.write("[%s] placeholder stub, nenhuma stack conectada\n" % HOOK)
    sys.stdout.write(json.dumps(
        {"status": "ok", "hook": HOOK, "id": node.get("id"), "verdict": "approved", "note": "placeholder stub"},
        ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
