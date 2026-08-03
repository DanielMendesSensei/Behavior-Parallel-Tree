#!/usr/bin/env python3
"""Score the answers of experiment 03 against checklist.md.

Every item is decided by walking the syntax tree, not by matching text, because
a regex over source code says yes to a string that mentions `sorted` and no to a
line that wrapped. The items that cannot be decided that way are not scored
here: `--judge` asks a model the same questions and the disagreement between the
two readings is reported, which is how a bad rubric announces itself.

An item that does not apply to a target is not counted against it. The
denominator is per answer.

Usage:
    python3 experiments/03-exemplar/score.py
    python3 experiments/03-exemplar/score.py --judge
"""
import argparse
import ast
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "runs")
FENCE = re.compile(r"```[a-zA-Z0-9_+-]*\n(.*?)```", re.DOTALL)

# What each target's contract actually asks for, which is what decides whether an
# item applies. Read off the contracts, once, so no item is scored against an
# answer that had no occasion to satisfy it.
TARGETS = {
    "note-detail": {
        "id": "note.detail",
        "codes": {"INVALID_PARAMETER", "NOT_FOUND", "UNAUTHORIZED"},
        "has_constraints": False,   # note_id is presence only
        "has_literals": False,      # the contract fixes no default or bound
        "needs_ordering": True,     # tag names ordered by name
    },
    "tag-list": {
        "id": "tag.list",
        "codes": {"INVALID_PARAMETER", "UNAUTHORIZED"},
        "has_constraints": True,    # min_count has a bound
        "has_literals": True,       # min_count default 0
        "needs_ordering": True,
    },
    "note-archive": {
        "id": "note.archive",
        "codes": {"INVALID_PARAMETER", "NOT_FOUND", "ALREADY_ARCHIVED", "UNAUTHORIZED"},
        "has_constraints": False,
        "has_literals": False,
        "needs_ordering": False,
    },
}

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "docstring_form": {"type": "boolean"},
        "helpers_named_for_what_they_return": {"type": "boolean"},
        "no_stray_abstraction": {"type": "boolean"},
        "note": {"type": "string"},
    },
    "required": ["docstring_form", "helpers_named_for_what_they_return", "no_stray_abstraction"],
}

JUDGE_PROMPT = """Below is a Python module, and below it the reference module it should resemble.

Answer three yes or no questions about the FIRST module only. Do not judge whether it is good code.

1. docstring_form: does its module docstring open with the behaviour id, a colon, and a short statement of what the behaviour returns, the way the reference does?
2. helpers_named_for_what_they_return: are its private helpers named for the thing they return, the way the reference names _validated_input and _matching? Answer true when it has no helpers.
3. no_stray_abstraction: is it free of any class, dataclass, module level mutable state, or helper covering a case its contract does not describe?

--- MODULE UNDER REVIEW ---
%s
--- REFERENCE ---
%s
"""


def artifact(text):
    blocks = FENCE.findall(text or "")
    return max(blocks, key=len) if blocks else ""


def public_function(tree):
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
            return node
    return None


def score_one(code, target):
    """Ten items. None means the item does not apply to this target."""
    spec = TARGETS[target]
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {"parse_error": True}

    fn = public_function(tree)
    helpers = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("_")]
    doc = ast.get_docstring(tree) or ""
    items = {}

    # 1. module docstring opens with "<id>: ..."
    items["docstring"] = doc.strip().startswith(spec["id"] + ":")

    # 2. from kernel import <names>, never a plain import
    from_kernel = any(
        isinstance(n, ast.ImportFrom) and n.module == "kernel"
        and not any(a.name == "*" for a in n.names)
        for n in ast.walk(tree)
    )
    plain = any(
        isinstance(n, ast.Import) and any(a.name == "kernel" for a in n.names)
        for n in ast.walk(tree)
    )
    items["import_shape"] = from_kernel and not plain

    # 3. require_session is the first statement of the public function
    items["session_first"] = False
    if fn:
        body = [s for s in fn.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
        if body:
            first = body[0]
            call = first.value if isinstance(first, ast.Expr) else getattr(first, "value", None)
            items["session_first"] = (
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Name)
                and call.func.id == "require_session"
            )

    # 4. validation isolated in a helper that raises INVALID_PARAMETER
    if spec["has_constraints"]:
        items["validation_isolated"] = any(
            any(
                isinstance(r, ast.Raise) and "INVALID_PARAMETER" in ast.dump(r)
                for r in ast.walk(h)
            )
            for h in helpers
        )
    else:
        items["validation_isolated"] = None

    # 5. helpers exist and are private (the naming judgement goes to the model)
    items["helpers_private"] = None if not helpers else all(
        h.name.startswith("_") for h in helpers
    )

    # 6. contract literals hoisted into UPPER_CASE module constants
    if spec["has_literals"]:
        items["literals_as_constants"] = any(
            isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id.isupper() for t in n.targets)
            for n in tree.body
        )
    else:
        items["literals_as_constants"] = None

    # 7. every raise is AppError with a code the contract declares
    raises = [n for n in ast.walk(tree) if isinstance(n, ast.Raise) and n.exc is not None]
    ok = bool(raises)
    for r in raises:
        exc = r.exc
        if not (isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name) and exc.func.id == "AppError"):
            ok = False
            break
        for arg in exc.args:
            if isinstance(arg, ast.Constant) and arg.value not in spec["codes"]:
                ok = False
    items["errors_via_apperror"] = ok

    # 8. the public function returns a dict literal built in place
    items["output_inline"] = False
    if fn:
        returns = [n for n in ast.walk(fn) if isinstance(n, ast.Return) and n.value is not None]
        items["output_inline"] = bool(returns) and isinstance(returns[-1].value, ast.Dict)

    # 9. ordering expressed as sorted(..., key=...)
    if spec["needs_ordering"]:
        items["ordering_idiom"] = any(
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "sorted"
            and any(k.arg == "key" for k in n.keywords)
            for n in ast.walk(tree)
        )
    else:
        items["ordering_idiom"] = None

    # 10. no class, no module level mutable state
    has_class = any(isinstance(n, ast.ClassDef) for n in tree.body)
    module_mutable = any(
        isinstance(n, ast.Assign)
        and isinstance(n.value, (ast.List, ast.Dict, ast.Set))
        and not any(isinstance(t, ast.Name) and t.id.isupper() for t in n.targets)
        for n in tree.body
    )
    items["no_stray_abstraction"] = not has_class and not module_mutable

    return items


def judge(code, model="sonnet"):
    reference = open(os.path.join(HERE, "fixture", "exemplar.md"), encoding="utf-8").read()
    block = FENCE.findall(reference)
    reference = max(block, key=len) if block else reference
    cmd = [
        "claude", "-p", "--safe-mode", "--tools", "", "--strict-mcp-config",
        "--disable-slash-commands", "--no-session-persistence",
        "--output-format", "json", "--model", model,
        "--json-schema", json.dumps(JUDGE_SCHEMA),
    ]
    workdir = tempfile.mkdtemp(prefix="bpt-judge3-")
    try:
        proc = subprocess.run(cmd, input=JUDGE_PROMPT % (code, reference),
                              capture_output=True, text=True, timeout=300, cwd=workdir)
        return json.loads(json.loads(proc.stdout).get("result", "{}"))
    except Exception as exc:
        return {"error": str(exc)}
    finally:
        subprocess.run(["rm", "-rf", workdir], check=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", action="store_true")
    args = ap.parse_args()

    rows = []
    for name in sorted(os.listdir(RUNS)):
        if not name.endswith(".jsonl"):
            continue
        target = name[:-6]
        for line in open(os.path.join(RUNS, name), encoding="utf-8"):
            if not line.strip():
                continue
            rec = json.loads(line)
            if not rec.get("ok"):
                continue
            code = artifact(rec["output"])
            row = {"target": target, "arm": rec["arm"], "run": rec["run"], "code": code}
            row["items"] = score_one(code, target)
            rows.append(row)

    keys = ["docstring", "import_shape", "session_first", "validation_isolated",
            "helpers_private", "literals_as_constants", "errors_via_apperror",
            "output_inline", "ordering_idiom", "no_stray_abstraction"]

    print("%-24s %14s %14s" % ("item", "arm-a-island", "arm-b-exemplar"))
    for k in keys:
        cells = []
        for arm in ("arm-a-island", "arm-b-exemplar"):
            vals = [r["items"].get(k) for r in rows if r["arm"] == arm]
            vals = [v for v in vals if v is not None]
            cells.append("%d/%d" % (sum(1 for v in vals if v), len(vals)) if vals else "n/a")
        print("%-24s %14s %14s" % (k, cells[0], cells[1]))

    print()
    scores = defaultdict(list)
    for r in rows:
        vals = [v for v in r["items"].values() if isinstance(v, bool)]
        if vals:
            scores[r["arm"]].append(sum(vals) / len(vals))
    for arm in ("arm-a-island", "arm-b-exemplar"):
        s = scores[arm]
        print("%-16s consistency %.0f%%  (per answer: %s)" % (
            arm, statistics.mean(s) * 100,
            " ".join("%.0f" % (x * 100) for x in sorted(s))))
    a, b = scores["arm-a-island"], scores["arm-b-exemplar"]
    spread = max(max(a) - min(a), max(b) - min(b))
    print("\nwithin-arm spread (the baseline): %.0f points" % (spread * 100))
    print("gap between arms:                 %.0f points" % ((statistics.mean(b) - statistics.mean(a)) * 100))

    if args.judge:
        print("\nindependent model reading:")
        agree = total = 0
        for r in rows:
            v = judge(r["code"])
            if "error" in v:
                continue
            for key, mine in (("docstring_form", r["items"]["docstring"]),
                              ("no_stray_abstraction", r["items"]["no_stray_abstraction"])):
                total += 1
                agree += int(bool(v.get(key)) == bool(mine))
            r["judge"] = v
        if total:
            print("  agreement with the syntax tree reading: %.0f%%" % (100.0 * agree / total))
            if agree / total < 0.8:
                print("  >> below 80%: the rubric is the suspect, not the result")

    out = os.path.join(HERE, "scored.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump([{k: v for k, v in r.items() if k != "code"} for r in rows], fh, indent=2)
    print("\nwrote %s" % out)


if __name__ == "__main__":
    raise SystemExit(main())
