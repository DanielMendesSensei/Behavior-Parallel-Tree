#!/usr/bin/env python3
"""Run every check BPT makes about itself, in one command.

Three things get checked, and the middle one is the point:

1. the tree is coherent (./bpt validate exits 0);
2. the gate turns red when it must. A validator that never fails proves
   nothing, so this feeds it configs it has to refuse and fails if any is
   accepted;
3. no doc cites a repository path that does not exist.

The same set runs in CI, but it lives here first: a check you cannot run on
your own machine is a check you do not trust, and it should not depend on
anyone's build minutes.

Usage:
    ./bpt check          (or: python3 tools/bpt/check.py [root])

Exit 0 when everything passes, 1 on the first failing group, with a summary.
Development tooling, stdlib only plus PyYAML for the validator.
"""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

# Each case is a config the validator MUST refuse, and the reason a person
# would write it by accident.
MUST_REFUSE = {
    "nodes written as a mapping": """schema: bpt/v1
project: case
adapter: placeholder
sides:
  backend:  { root: apps/backend/behaviors,  kernel: apps/backend/kernel }
  frontend: { root: apps/frontend/behaviors, kernel: apps/frontend/kernel }
contracts: { root: packages/contracts }
nodes:
  product.list: { sides: [backend, frontend], deps: [] }
""",
    "a dependency cycle": """schema: bpt/v1
project: case
adapter: placeholder
sides:
  backend:  { root: apps/backend/behaviors,  kernel: apps/backend/kernel }
  frontend: { root: apps/frontend/behaviors, kernel: apps/frontend/kernel }
contracts: { root: packages/contracts }
nodes:
  - id: product.list
    sides: [backend, frontend]
    deps: [product.detail]
  - id: product.detail
    sides: [backend, frontend]
    deps: [product.list]
""",
    "an unsupported schema": """schema: bpt/v99
project: case
adapter: placeholder
sides:
  backend:  { root: apps/backend/behaviors,  kernel: apps/backend/kernel }
  frontend: { root: apps/frontend/behaviors, kernel: apps/frontend/kernel }
contracts: { root: packages/contracts }
nodes:
  - id: product.list
    sides: [backend, frontend]
    deps: []
""",
    "a node whose id is not domain.action": """schema: bpt/v1
project: case
adapter: placeholder
sides:
  backend:  { root: apps/backend/behaviors,  kernel: apps/backend/kernel }
  frontend: { root: apps/frontend/behaviors, kernel: apps/frontend/kernel }
contracts: { root: packages/contracts }
nodes:
  - id: ProductList
    sides: [backend, frontend]
    deps: []
""",
    "a node under the reserved kernel domain": """schema: bpt/v1
project: case
adapter: placeholder
sides:
  backend:  { root: apps/backend/behaviors,  kernel: apps/backend/kernel }
  frontend: { root: apps/frontend/behaviors, kernel: apps/frontend/kernel }
contracts: { root: packages/contracts }
nodes:
  - id: kernel.auth
    sides: [backend, frontend]
    deps: []
""",
}


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def check_tree(root):
    proc = run([sys.executable, os.path.join(HERE, "validate.py"), root])
    if proc.returncode != 0:
        print(proc.stdout.strip())
        print(proc.stderr.strip())
        return False
    print("  " + proc.stdout.strip().splitlines()[-1])
    return True


def check_gate_turns_red(root):
    """Copy the tree, break the config on purpose, expect a refusal."""
    ok = True
    with tempfile.TemporaryDirectory(prefix="bpt-check-") as tmp:
        for name, config in MUST_REFUSE.items():
            case = os.path.join(tmp, "case")
            if os.path.exists(case):
                shutil.rmtree(case)
            shutil.copytree(
                root,
                case,
                ignore=shutil.ignore_patterns(".git", "__pycache__", ".bpt", "node_modules"),
            )
            with open(os.path.join(case, "bpt.config.yaml"), "w", encoding="utf-8") as f:
                f.write(config)
            proc = run([sys.executable, os.path.join(HERE, "validate.py"), case])
            if proc.returncode == 0:
                print("  FAILED: the validator accepted %s" % name)
                ok = False
            elif "Traceback" in proc.stderr:
                print("  FAILED: %s crashed the validator instead of being refused" % name)
                print("    " + proc.stderr.strip().splitlines()[-1])
                ok = False
            else:
                print("  refused: %s" % name)
    return ok


def check_docs(root):
    proc = run([sys.executable, os.path.join(HERE, "check_docs.py"), root])
    print("  " + (proc.stdout.strip().splitlines() or [""])[-1])
    return proc.returncode == 0


def main(argv):
    root = os.path.abspath(argv[1]) if len(argv) > 1 else os.getcwd()
    groups = [
        ("the tree is coherent", check_tree),
        ("the gate turns red when an invariant breaks", check_gate_turns_red),
        ("every path the docs cite exists", check_docs),
    ]
    failed = []
    for title, fn in groups:
        print("\n== %s" % title)
        if not fn(root):
            failed.append(title)

    print("\n== summary")
    for title, _ in groups:
        print("  %-45s %s" % (title, "FAILED" if title in failed else "ok"))
    if failed:
        print("\n%d group(s) failed." % len(failed))
        return 1
    print("\nall green.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
