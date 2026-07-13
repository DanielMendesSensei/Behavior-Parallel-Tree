#!/usr/bin/env python3
"""Scaffold hook of the placeholder adapter.

The only placeholder hook that does real work: it materializes a behavior's
mirrored folders and the spec and contract stubs, by convention, from the repo
root (current directory). It knows no stack and has no dependencies.

Request (stdin, JSON):
    {"node": {"id": "product.create",
              "sides": ["backend", "frontend"],
              "contract": "product/create" | "none"}}

Response (stdout, JSON):
    {"status": "ok", "hook": "scaffold", "id": ..., "created": [...]}
"""
import json
import os
import sys


def emit(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")


def touch(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        open(path, "w").close()
        return True
    return False


def write_if_absent(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return True


CONTRACT_STUB = """id: {id}
version: 1
kind: query
title: {id}

authorization:
  required: false
  roles: []

input: {{}}

output: {{}}

rules: []

errors: []
"""

SPEC_STUB = """---
id: {id}
title: {id}
surfaces: {{}}
contract: {contract}
consumes: []
status: {{}}
---

## Behavior
Describe the visible action, the surface, and the result.

## Rules

## Scenarios (given / when / then, by surface)

## Out of scope
"""


def main():
    try:
        req = json.load(sys.stdin)
    except Exception as e:
        emit({"status": "error", "hook": "scaffold", "error": "invalid json: %s" % e})
        return 1

    node = req.get("node", req)
    node_id = node.get("id")
    sides = node.get("sides") or []
    contract = node.get("contract")

    if not node_id or not sides:
        emit({"status": "error", "hook": "scaffold",
              "error": "node.id and node.sides are required"})
        return 1

    path = node_id.replace(".", "/")
    two_sided = len(sides) >= 2 and contract != "none"
    if contract in (None, ""):
        contract = "none" if len(sides) < 2 else path

    created = []
    for side in sides:
        for sub in ("src", "__generated__"):
            gk = os.path.join("apps", side, "behaviors", path, sub, ".gitkeep")
            if touch(gk):
                created.append(gk)

    sys.stderr.write("[scaffold] behavior %s on %s\n" % (node_id, ", ".join(sides)))

    spec_path = os.path.join("packages", "contracts", path, "spec.md")
    if write_if_absent(spec_path, SPEC_STUB.format(id=node_id, contract=contract)):
        created.append(spec_path)

    if two_sided:
        c_path = os.path.join("packages", "contracts", path, "contract.yaml")
        if write_if_absent(c_path, CONTRACT_STUB.format(id=node_id)):
            created.append(c_path)

    emit({"status": "ok", "hook": "scaffold", "id": node_id, "created": created})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
