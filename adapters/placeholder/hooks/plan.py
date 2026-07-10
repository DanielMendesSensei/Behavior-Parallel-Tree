#!/usr/bin/env python3
"""Hook plan do adapter placeholder: stub.

Um adapter real produziria aqui um plano tecnico a partir da spec, do contrato e
do codigo existente, sem escrever produto. O placeholder nao conhece stack: retorna
status ok com payload vazio e loga em stderr.
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
    sys.stderr.write("[%s] placeholder stub, nenhuma stack conectada\n" % HOOK)
    sys.stdout.write(json.dumps(
        {"status": "ok", "hook": HOOK, "id": node.get("id"), "note": "placeholder stub"},
        ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
