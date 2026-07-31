#!/usr/bin/env python3
"""Apply an experiment's rubric to its recorded runs and print the table.

Development tooling for the experiments in this directory, NOT the app stack.

Everything in the deterministic pass is literal matching, so two people scoring
the same output get the same number. The parts that need judgement are handled by
`--judge`, which asks an independent model the same questions and reports how far
the two readings disagree. High disagreement means the rubric is bad and has to
be fixed and reapplied. It never means the result should be reinterpreted.

The script also names, in plain words, which pre-registered criterion the numbers
hit. That is on purpose: the criteria were fixed in advance precisely because the
person reading the table has a favourite answer, and a table that reports its own
verdict is harder to talk out of.

Usage:
    python3 experiments/lib/score.py --plan experiments/01-hallucination-probe/plan.yaml
    python3 experiments/lib/score.py --plan ... --judge

Single dependency: PyYAML.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

try:
    import yaml
except ImportError:
    sys.stderr.write("error: PyYAML not found. Install with: pip install pyyaml\n")
    raise SystemExit(2)

FENCE_RE = re.compile(r"```([A-Za-z0-9_+-]*)\n(.*?)```", re.DOTALL)
KEY_LINE_RE = re.compile(r'^\s*"?([A-Za-z_][\w.-]*)"?\s*:', re.MULTILINE)
TYPE_VALUE_RE = re.compile(r'"?type"?\s*:\s*"?([A-Za-z_][\w-]*)"?', re.IGNORECASE)

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "primary_format": {
            "type": "string",
            "description": "the single format the answer is mostly written in",
        },
        "standards_used": {
            "type": "array",
            "items": {"type": "string"},
            "description": "named public standards the answer uses or reproduces, lowercase",
        },
        "invented_own_format": {
            "type": "boolean",
            "description": "true when the answer defines a bespoke format rather than using a standard",
        },
        "proposed_filename": {"type": "string"},
    },
    "required": ["primary_format", "standards_used", "invented_own_format"],
}

JUDGE_PROMPT = """Below is an answer another model gave when asked to design a file.

Classify it. Do not judge whether it is good. Only report what it is:
- primary_format: the one format the answer is mostly written in
- standards_used: which named public standards it uses or reproduces, lowercase
  (for example: json-schema, openapi, protobuf, graphql, gherkin, typespec, nx,
  turborepo). Empty list when it uses none.
- invented_own_format: true when it defines a bespoke shape rather than using a
  standard
- proposed_filename: the filename it proposes, or an empty string

--- BEGIN ANSWER ---
%s
--- END ANSWER ---
"""


def load_jsonl(path):
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def walk_keys(node, into):
    if isinstance(node, dict):
        for key, value in node.items():
            if isinstance(key, str):
                into.add(key.lower())
            walk_keys(value, into)
    elif isinstance(node, list):
        for item in node:
            walk_keys(item, into)


def produced_keys(text):
    """Every key name the answer proposes, from parsed blocks where possible."""
    keys = set()
    blocks = FENCE_RE.findall(text)
    for lang, body in blocks:
        parsed = None
        if lang.lower() in ("", "yaml", "yml", "json", "jsonc"):
            try:
                parsed = yaml.safe_load(body)
            except yaml.YAMLError:
                parsed = None
        if isinstance(parsed, (dict, list)):
            walk_keys(parsed, keys)
        else:
            for match in KEY_LINE_RE.finditer(body):
                keys.add(match.group(1).lower())
    if not blocks:
        for match in KEY_LINE_RE.finditer(text):
            keys.add(match.group(1).lower())
    return keys


def detect_standards(text, rubric):
    low = text.lower()
    found = []
    for name, spec in rubric["standards"].items():
        hits = sum(1 for marker in spec["markers"] if marker.lower() in low)
        if hits >= spec.get("min_hits", 1):
            found.append(name)
    return sorted(found)


def score_one(text, rubric):
    ignored = {k.lower() for k in rubric.get("ignored_keys", [])}
    bpt = {k.lower() for k in rubric["bpt_keys"]} - ignored
    produced = produced_keys(text) - ignored

    types = [t.lower() for t in TYPE_VALUE_RE.findall(text)]
    vocab = rubric["type_vocabulary"]
    in_dist = [t for t in types if t in {v.lower() for v in vocab["in_distribution"]}]
    bpt_only = [t for t in types if t in {v.lower() for v in vocab["bpt_only"]}]

    req = rubric["required_convention"]
    filenames = sorted(set(re.findall(rubric["filename_pattern"], text)))

    return {
        "standards": detect_standards(text, rubric),
        "produced_keys": sorted(produced),
        "bpt_keys_hit": sorted(produced & bpt),
        "bpt_coverage": (len(produced & bpt) / len(bpt)) if bpt else 0.0,
        "foreign_keys": sorted(produced - bpt),
        "foreign_rate": (len(produced - bpt) / len(produced)) if produced else 0.0,
        "types_in_distribution": sorted(set(in_dist)),
        "types_bpt_only": sorted(set(bpt_only)),
        "required_object_level": bool(re.search(req["object_level_list"], text)),
        "required_per_field": bool(re.search(req["per_field_flag"], text)),
        "filename_exts": sorted({f.rsplit(".", 1)[-1].lower() for f in filenames}),
        "chars": len(text),
    }


def judge_one(text, model="sonnet"):
    """Second, independent reading of the same answer, by a model."""
    cmd = [
        "claude", "-p", "--safe-mode", "--tools", "", "--strict-mcp-config",
        "--disable-slash-commands", "--no-session-persistence",
        "--output-format", "json", "--model", model,
        "--json-schema", json.dumps(JUDGE_SCHEMA),
    ]
    workdir = tempfile.mkdtemp(prefix="bpt-judge-")
    try:
        proc = subprocess.run(
            cmd, input=JUDGE_PROMPT % text[:60000],
            capture_output=True, text=True, timeout=300, cwd=workdir,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"error": str(exc)}
    finally:
        subprocess.run(["rm", "-rf", workdir], check=False)
    if proc.returncode != 0:
        return {"error": proc.stderr.strip()[:300]}
    try:
        envelope = json.loads(proc.stdout)
        return json.loads(envelope.get("result", "{}"))
    except ValueError:
        return {"error": "judge did not return JSON"}


def mean(values):
    return sum(values) / len(values) if values else 0.0


def verdict_for_cell(cell, rows):
    """State which pre-registered criterion these numbers hit."""
    if not rows:
        return None
    n = len(rows)
    if cell == "b-contract":
        hits = sum(1 for r in rows if {"json-schema", "openapi"} & set(r["standards"]))
        rate = hits / n
        if rate > 0.60:
            return (
                "criterion 1 HIT (%d/%d = %.0f%% reached for JSON Schema or OpenAPI): "
                "BPT's contract notation is a tax, and experiment 02 becomes a "
                "confirmation rather than a discovery." % (hits, n, rate * 100)
            )
        return (
            "criterion 1 NOT hit (%d/%d = %.0f%%, threshold was 60%%): the contract "
            "prompt did not converge on a public standard." % (hits, n, rate * 100)
        )
    if cell == "a-declaration":
        both = sum(1 for r in rows if {"id", "deps"} <= set(r["bpt_keys_hit"]))
        return (
            "criterion 2 reading: %d/%d runs produced an identity plus a dependency "
            "list unprompted. Judge the per-target list by eye in the raw output "
            "before calling this hit." % (both, n)
        )
    if cell == "z-contamination":
        return "read the raw answers by hand: this cell is a yes or no, not a rate."
    return None


def main():
    ap = argparse.ArgumentParser(description="Score recorded experiment runs against the rubric.")
    ap.add_argument("--plan", required=True)
    ap.add_argument("--rubric", default=None, help="defaults to rubric.yaml next to the plan")
    ap.add_argument("--judge", action="store_true", help="add an independent model reading")
    ap.add_argument("--judge-model", default="sonnet")
    args = ap.parse_args()

    base = os.path.dirname(os.path.abspath(args.plan))
    with open(args.plan, encoding="utf-8") as fh:
        plan = yaml.safe_load(fh)
    rubric_path = args.rubric or os.path.join(base, "rubric.yaml")
    with open(rubric_path, encoding="utf-8") as fh:
        rubric = yaml.safe_load(fh)

    runs_dir = os.path.join(base, plan.get("runs_dir", "runs"))
    scored = []
    agreements = []

    for cell in plan["cells"]:
        for record in load_jsonl(os.path.join(runs_dir, cell["name"] + ".jsonl")):
            if not record.get("ok"):
                continue
            row = score_one(record.get("output") or "", rubric)
            row.update(
                {
                    "cell": record["cell"],
                    "model": record["model"],
                    "run": record["run"],
                    "cost_usd": record.get("cost_usd"),
                }
            )
            if args.judge:
                verdict = judge_one(record.get("output") or "", args.judge_model)
                row["judge"] = verdict
                if "error" not in verdict:
                    judged = {s.lower() for s in verdict.get("standards_used", [])}
                    detected = set(row["standards"])
                    agreements.append(bool(judged & detected) or (not judged and not detected))
            scored.append(row)

    if not scored:
        print("no successful runs recorded yet. Run the runner first.")
        return 1

    out_path = os.path.join(base, "scored.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(scored, fh, indent=2, ensure_ascii=False)

    all_standards = sorted({s for row in scored for s in row["standards"]})
    for cell in plan["cells"]:
        rows = [r for r in scored if r["cell"] == cell["name"]]
        if not rows:
            continue
        print("\n=== %s  (%d runs)" % (cell["name"], len(rows)))
        for standard in all_standards:
            hits = sum(1 for r in rows if standard in r["standards"])
            if hits:
                print("  %-18s %d/%d" % (standard, hits, len(rows)))
        print("  bpt key coverage   %.0f%%" % (mean([r["bpt_coverage"] for r in rows]) * 100))
        print("  foreign key rate   %.0f%%" % (mean([r["foreign_rate"] for r in rows]) * 100))
        types_bpt = sorted({t for r in rows for t in r["types_bpt_only"]})
        types_dist = sorted({t for r in rows for t in r["types_in_distribution"]})
        print("  types seen         in-distribution=%s  bpt-only=%s" % (types_dist or "-", types_bpt or "-"))
        obj = sum(1 for r in rows if r["required_object_level"])
        fld = sum(1 for r in rows if r["required_per_field"])
        print("  required as list %d/%d, per field %d/%d" % (obj, len(rows), fld, len(rows)))
        exts = sorted({e for r in rows for e in r["filename_exts"]})
        print("  file extensions    %s" % (", ".join(exts) or "-"))
        verdict = verdict_for_cell(cell["name"], rows)
        if verdict:
            print("  >> %s" % verdict)

    if agreements:
        rate = mean([1.0 if a else 0.0 for a in agreements])
        print("\nrubric agreement with the independent model reading: %.0f%%" % (rate * 100))
        if rate < 0.80:
            print("  >> below 80%: the rubric is the suspect, not the result. Fix it and re-score.")

    print("\nwrote %s" % out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
