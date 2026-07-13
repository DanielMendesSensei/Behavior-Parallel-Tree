#!/usr/bin/env python3
"""Reference validator for the Behavior Parallel Tree (BPT).

Development tooling, NOT the app stack. It reads bpt.config.yaml and the file
tree and runs the 7 core invariants. No side effects: it only reads, validates,
and reports. A real adapter may reimplement this in its own stack.

Usage:
    ./bpt validate                 # validate the project in the current directory
    python3 tools/bpt/validate.py [root-path]

Output:
    exit 0  -> everything valid (there may be warnings)
    exit 1  -> one or more invariants violated

Single dependency: PyYAML (pip install pyyaml). It is tooling, swappable.
"""
import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "error: PyYAML not found. Install with: pip install pyyaml\n"
        "(it is a tooling dependency of the validator, not of the app stack)\n"
    )
    raise SystemExit(2)

ID_RE = re.compile(r"^[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*){1,2}$")  # 2 to 3 segments
SUPPORTED_SCHEMA = {"bpt/v1"}

# Diagnostic accumulators.
ERRORS = []
WARNINGS = []


def err(inv, msg):
    ERRORS.append("[INV %s] %s" % (inv, msg))


def warn(inv, msg):
    WARNINGS.append("[INV %s] %s" % (inv, msg))


def load_config(root):
    path = os.path.join(root, "bpt.config.yaml")
    if not os.path.exists(path):
        err(0, "bpt.config.yaml not found in %s" % root)
        return None
    with open(path, encoding="utf-8") as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            err(0, "bpt.config.yaml invalid: %s" % e)
            return None


def node_path(node_id):
    return node_id.replace(".", "/")


def collect_dep_ids(node):
    """Return the flat list of ids referenced in deps (list or per-side) plus consumes."""
    refs = []
    deps = node.get("deps", [])
    if isinstance(deps, dict):
        for side_deps in deps.values():
            refs.extend(side_deps or [])
    elif isinstance(deps, list):
        refs.extend(deps)
    refs.extend(node.get("consumes", []) or [])
    return refs


def build_edges(nodes_by_id):
    """Edges dependent -> dependency, from deps and consumes."""
    edges = {}
    for nid, node in nodes_by_id.items():
        edges[nid] = set(r for r in collect_dep_ids(node) if r in nodes_by_id)
    return edges


def find_cycle(edges):
    """Kahn: if a node remains with in-degree > 0, there is a cycle. Returns a cycle path."""
    indeg = {n: 0 for n in edges}
    for n, deps in edges.items():
        for d in deps:
            indeg[n] += 1  # n depends on d, so n has an incoming edge
    queue = [n for n, g in indeg.items() if g == 0]
    seen = 0
    while queue:
        n = queue.pop()
        seen += 1
        for m, deps in edges.items():
            if n in deps:
                indeg[m] -= 1
                if indeg[m] == 0:
                    queue.append(m)
    if seen == len(edges):
        return None
    # nodes still stuck: rebuild a simple cycle via DFS among the remaining ones
    remaining = {n for n, g in indeg.items() if g > 0}
    return _trace_cycle(edges, remaining)


def _trace_cycle(edges, remaining):
    start = next(iter(remaining))
    path = [start]
    seen = {start}
    cur = start
    while True:
        nxt = next((d for d in edges[cur] if d in remaining), None)
        if nxt is None:
            return path
        if nxt in seen:
            return path[path.index(nxt):] + [nxt]
        path.append(nxt)
        seen.add(nxt)
        cur = nxt


def waves(edges):
    """Sort into topological waves (what the adapter runs in parallel per wave)."""
    indeg = {n: len(deps) for n, deps in edges.items()}
    result = []
    remaining = dict(indeg)
    while remaining:
        layer = sorted(n for n, g in remaining.items() if g == 0)
        if not layer:
            return None  # cycle
        result.append(layer)
        for n in layer:
            del remaining[n]
        for n in list(remaining):
            remaining[n] = len([d for d in edges[n] if d in remaining])
    return result


def validate(root):
    cfg = load_config(root)
    if cfg is None:
        return

    # INV 1: schema present and supported.
    schema = cfg.get("schema")
    if not schema:
        err(1, "field 'schema' missing in bpt.config.yaml")
    elif schema not in SUPPORTED_SCHEMA:
        err(1, "schema '%s' not supported (supported: %s)" % (schema, ", ".join(sorted(SUPPORTED_SCHEMA))))

    sides_cfg = cfg.get("sides", {}) or {}
    contracts_root = (cfg.get("contracts", {}) or {}).get("root", "packages/contracts")
    nodes = cfg.get("nodes", []) or []

    nodes_by_id = {}
    for node in nodes:
        nid = node.get("id")
        if not nid:
            err(2, "node without 'id' in nodes")
            continue
        # INV 2: unique id in domain.action format.
        if nid in nodes_by_id:
            err(2, "duplicate id: %s" % nid)
        if not ID_RE.match(nid):
            err(2, "id not in domain.action format (2 to 3 segments, lowercase): %s" % nid)
        nodes_by_id[nid] = node

    for nid, node in nodes_by_id.items():
        sides = node.get("sides") or []
        # INV 3: sides not empty and each side exists in the top-level sides.
        if not sides:
            err(3, "%s: 'sides' empty" % nid)
        for s in sides:
            if s not in sides_cfg:
                err(3, "%s: side '%s' not declared in top-level sides" % (nid, s))

        # INV 6: no id falls under a kernel folder.
        if nid.split(".")[0] == "kernel":
            err(6, "%s: domain 'kernel' is reserved (kernel lives outside the tree)" % nid)

        # INV 5: two-sided has a contract; one-sided has contract: none.
        contract_field = node.get("contract")
        two_sided = len(sides) >= 2
        if two_sided:
            if contract_field == "none":
                err(5, "%s is two-sided but declares contract: none" % nid)
        else:
            if contract_field != "none":
                err(5, "%s is one-sided; declare contract: none" % nid)

    # INV 4: refs exist, no self-dependency, acyclic graph.
    for nid, node in nodes_by_id.items():
        for ref in collect_dep_ids(node):
            if ref == nid:
                err(4, "%s depends on itself" % nid)
            if ref not in nodes_by_id:
                err(4, "%s references a nonexistent id: %s" % (nid, ref))
    edges = build_edges(nodes_by_id)
    cycle = find_cycle(edges)
    if cycle:
        err(4, "dependency cycle: %s" % " -> ".join(cycle))

    # INV 7: file trio exists (contract + spec + folder per side).
    for nid, node in nodes_by_id.items():
        sides = node.get("sides") or []
        p = node_path(nid)
        two_sided = len(sides) >= 2 and node.get("contract") != "none"
        spec = os.path.join(root, contracts_root, p, "spec.md")
        if not os.path.exists(spec):
            err(7, "%s: spec missing in %s" % (nid, os.path.relpath(spec, root)))
        if two_sided:
            contract = os.path.join(root, contracts_root, p, "contract.yaml")
            if not os.path.exists(contract):
                err(7, "%s: contract.yaml missing in %s" % (nid, os.path.relpath(contract, root)))
        for s in sides:
            side_root = (sides_cfg.get(s) or {}).get("root", os.path.join("apps", s, "behaviors"))
            folder = os.path.join(root, side_root, p)
            if not os.path.isdir(folder):
                err(7, "%s: folder for side '%s' missing in %s" % (nid, s, os.path.relpath(folder, root)))

    # Informational: parallelism waves (the core derives them, the adapter walks them).
    if not ERRORS:
        w = waves(edges)
        if w:
            print("parallelism waves (the adapter walks in this order):")
            for i, layer in enumerate(w, 1):
                print("  wave %d: %s" % (i, ", ".join(layer)))


def main(argv):
    root = os.path.abspath(argv[1]) if len(argv) > 1 else os.getcwd()
    print("bpt validate: %s" % root)
    validate(root)
    for w in WARNINGS:
        print("warning  %s" % w)
    if ERRORS:
        for e in ERRORS:
            print("ERROR   %s" % e)
        print("\nfailed: %d error(s), %d warning(s)" % (len(ERRORS), len(WARNINGS)))
        return 1
    print("\nok: bpt.config.yaml and the tree passed the 7 invariants (%d warning(s))" % len(WARNINGS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
