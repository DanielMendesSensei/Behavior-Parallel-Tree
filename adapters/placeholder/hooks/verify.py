#!/usr/bin/env python3
"""Hook verify do adapter placeholder: stub.

Um adapter real rodaria os cenarios da spec (na superficie do lado) mais os testes
unitarios, e checaria a direcao de import (behavior nunca importa behavior; kernel
nunca importa behavior). O placeholder nao conhece stack: retorna status ok com
payload vazio e loga em stderr.
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
    sys.stderr.write("[%s] placeholder stub, nenhuma stack conectada\n" % HOOK)
    sys.stdout.write(json.dumps(
        {"status": "ok", "hook": HOOK, "id": node.get("id"), "scenarios": [], "note": "placeholder stub"},
        ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
