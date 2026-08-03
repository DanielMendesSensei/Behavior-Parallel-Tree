#!/usr/bin/env python3
"""Fire N identical runs of an experiment cell and record the raw output.

Development tooling for the experiments in this directory, NOT the app stack and
not part of BPT itself. It reads a plan.yaml, runs each cell N times per model in
a clean session, and appends one JSON object per run to runs/<cell>.jsonl.

Three properties matter more than anything else here, because they are what makes
the numbers trustworthy:

1. Isolation. Every run executes in a fresh empty directory with the executor
   flags the plan declares, so there is no repository, no memory and no user
   configuration leaking into the answer. The exact command is written into every
   record, so a reader can reproduce it without reading this file.
2. Resumability. A run already recorded as ok is skipped. An interrupted sweep
   continues where it stopped instead of paying twice for the same tokens.
3. Prompt integrity. The sha256 of the prompt goes into every record. Editing a
   prompt after runs exist is the easiest way to quietly invalidate an
   experiment, so the runner refuses to add runs to a file whose recorded hash no
   longer matches, unless it is told to.

Usage:
    python3 experiments/lib/runner.py --plan experiments/01-hallucination-probe/plan.yaml
    python3 experiments/lib/runner.py --plan ... --dry-run
    python3 experiments/lib/runner.py --plan ... --budget-usd 5 --only-cell b-contract

Exit 0 when every planned run is recorded, 1 when any run failed or the budget
stopped the sweep early.

Single dependency: PyYAML. It is tooling, swappable.
"""
import argparse
import datetime
import getpass
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

FENCE_RE = re.compile(r"```([A-Za-z0-9_+-]*)\n(.*?)```", re.DOTALL)
# stdlib unittest reports "Ran 12 tests" and then OK, or FAILED (failures=3, errors=1).
RAN_RE = re.compile(r"^Ran (\d+) test", re.MULTILINE)
TALLY_RE = re.compile(r"(failures|errors)=(\d+)")

try:
    import yaml
except ImportError:
    sys.stderr.write(
        "error: PyYAML not found. Install with: pip install pyyaml\n"
        "(a tooling dependency of the experiments, not of any app stack)\n"
    )
    raise SystemExit(2)


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def scrub(text):
    """Strip machine identity out of anything that lands in runs/.

    These files are raw model output committed to a public repository, and a
    model told it is an agent will happily print an `ls -la` of its working
    directory. The first sweep did exactly that and put an operating system
    username into a public commit. Nothing about who ran an experiment is part
    of its result, so it is removed at the boundary rather than trusted not to
    appear.
    """
    if not text:
        return text
    home = os.path.expanduser("~")
    if home and home != "/":
        text = text.replace(home, "<home>")
    try:
        user = getpass.getuser()
    except Exception:
        user = ""
    if user and len(user) >= 4:
        text = re.sub(r"\b%s\b" % re.escape(user), "<user>", text)
    return text


def read_prompt(path):
    """Return the prompt body, dropping the YAML front matter if there is one.

    The front matter documents what the cell targets and which words were kept
    out of the prompt. It must never reach the model: it names the very
    vocabulary the probe is testing for.
    """
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if text.startswith("---\n"):
        end = text.find("\n---\n", 3)
        if end != -1:
            text = text[end + 5 :]
    return text.strip() + "\n"


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def render_prompt(text, variables):
    """Substitute {name} placeholders with file contents.

    Plain replacement, not str.format, because the interpolated files are YAML
    and Python and are full of braces of their own. format() would either crash
    on them or silently eat them, and a prompt that silently lost a line is the
    kind of defect that produces a clean looking table of nothing.
    """
    for name, value in variables.items():
        text = text.replace("{%s}" % name, value.rstrip("\n"))
    leftover = re.findall(r"\{([a-z_]+)\}", text)
    if leftover:
        raise SystemExit("error: prompt has unfilled placeholders: %s" % sorted(set(leftover)))
    return text


def extract_artifact(output):
    """The largest fenced block. The prompts ask for exactly one."""
    blocks = FENCE_RE.findall(output or "")
    if not blocks:
        return None
    return max(blocks, key=lambda pair: len(pair[1]))[1]


def run_harness(base, harness, artifact):
    """Materialise the artifact in a copy of the scaffold and run the check."""
    if artifact is None:
        return {"harness_ok": False, "harness_error": "no fenced code block in the answer"}
    workdir = tempfile.mkdtemp(prefix="bpt-harness-")
    target = os.path.join(workdir, "run")
    try:
        shutil.copytree(os.path.join(base, harness["scaffold"]), target)
        with open(os.path.join(target, harness["artifact"]), "w", encoding="utf-8") as fh:
            fh.write(artifact)
        proc = subprocess.run(
            harness["verify"],
            capture_output=True,
            text=True,
            timeout=harness.get("timeout_s", 180),
            cwd=target,
        )
        # unittest writes its report to stderr, so both streams are kept.
        tail = ((proc.stdout or "") + (proc.stderr or ""))[-6000:]
        ran = RAN_RE.search(tail)
        ran = int(ran.group(1)) if ran else 0
        tally = {kind: int(count) for kind, count in TALLY_RE.findall(tail)}
        failed = tally.get("failures", 0) + tally.get("errors", 0)
        passed = max(ran - failed, 0)
        return {
            "harness_ok": proc.returncode == 0,
            "harness_passed": passed,
            "harness_failed": failed,
            "harness_returncode": proc.returncode,
            "harness_output": scrub(tail),
        }
    except subprocess.TimeoutExpired:
        return {"harness_ok": False, "harness_error": "verify timed out"}
    except OSError as exc:
        return {"harness_ok": False, "harness_error": "could not run verify: %s" % exc}
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def load_jsonl(path):
    if not os.path.exists(path):
        return []
    records = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def append_jsonl(path, record):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_command(executor, model):
    cmd = [executor["command"]]
    for arg in executor.get("args", []):
        cmd.append(str(arg).replace("{model}", model))
    return cmd


def run_once(cmd, prompt, timeout_s, prompt_via):
    """Run the executor in a throwaway directory and parse its JSON envelope."""
    workdir = tempfile.mkdtemp(prefix="bpt-probe-")
    try:
        stdin_text = prompt if prompt_via == "stdin" else None
        argv = cmd if prompt_via == "stdin" else cmd + [prompt]
        proc = subprocess.run(
            argv,
            input=stdin_text,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            cwd=workdir,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout after %ss" % timeout_s}
    except OSError as exc:
        return {"ok": False, "error": "could not run executor: %s" % exc}
    finally:
        # Tools are off, so the directory should still be empty. Recording what
        # is in it anyway is cheap, and a non-empty list would mean the isolation
        # is not what the plan claims.
        try:
            leftovers = sorted(os.listdir(workdir))
        except OSError:
            leftovers = []
        shutil.rmtree(workdir, ignore_errors=True)

    if proc.returncode != 0:
        return {
            "ok": False,
            "error": "exit %s: %s" % (proc.returncode, proc.stderr.strip()[:400]),
        }
    try:
        envelope = json.loads(proc.stdout)
    except ValueError:
        return {"ok": False, "error": "executor did not return JSON", "raw": proc.stdout[:2000]}

    return {
        "ok": not envelope.get("is_error", False),
        "output": scrub(envelope.get("result", "")),
        "cost_usd": envelope.get("total_cost_usd"),
        "usage": envelope.get("usage"),
        "model_usage": envelope.get("modelUsage"),
        "duration_ms": envelope.get("duration_ms"),
        "num_turns": envelope.get("num_turns"),
        "stop_reason": envelope.get("stop_reason"),
        "leftover_files": leftovers,
    }


def main():
    ap = argparse.ArgumentParser(description="Run an experiment plan and record raw output.")
    ap.add_argument("--plan", required=True, help="path to plan.yaml")
    ap.add_argument("--dry-run", action="store_true", help="print what would run, spend nothing")
    ap.add_argument("--budget-usd", type=float, default=None, help="stop the sweep past this cost")
    ap.add_argument("--only-cell", default=None, help="run a single cell by name")
    ap.add_argument("--only-arm", default=None, help="run a single arm by name")
    ap.add_argument("--only-model", default=None, help="run a single model")
    ap.add_argument("--n", type=int, default=None, help="override the run count per cell")
    ap.add_argument(
        "--allow-prompt-change",
        action="store_true",
        help="record runs even though the prompt hash differs from earlier runs",
    )
    args = ap.parse_args()

    plan_path = os.path.abspath(args.plan)
    base = os.path.dirname(plan_path)
    with open(plan_path, encoding="utf-8") as fh:
        plan = yaml.safe_load(fh)

    executor = plan["executor"]
    runs_dir = os.path.join(base, plan.get("runs_dir", "runs"))
    models = [args.only_model] if args.only_model else plan["models"]
    default_n = args.n or plan.get("n", 5)

    spent = 0.0
    failures = 0
    stopped_by_budget = False

    # Files interpolated into every prompt, identical for every arm.
    shared = {}
    for name, path in (plan.get("includes") or {}).items():
        with open(os.path.join(base, path), encoding="utf-8") as fh:
            shared[name] = fh.read()

    # A plan without arms behaves as one unnamed arm, so experiment 01 keeps
    # working unchanged.
    arms = plan.get("arms") or [{"name": None}]

    for cell in plan["cells"]:
        if args.only_cell and cell["name"] != args.only_cell:
            continue
        template = read_prompt(os.path.join(base, cell["prompt"]))
        jsonl = os.path.join(runs_dir, cell["name"] + ".jsonl")
        recorded = load_jsonl(jsonl)
        harness = cell.get("harness")
        n = args.n or cell.get("n", default_n)

        for arm in arms:
            if args.only_arm and arm["name"] != args.only_arm:
                continue
            # Variables layer: plan-wide includes, then whatever the cell varies,
            # then whatever the arm varies. An experiment that changes the
            # contract per arm and one that changes the context per arm are the
            # same mechanism, so neither gets its own special case.
            variables = dict(shared)
            for source in (cell.get("vars") or {}, arm.get("vars") or {}):
                for name, path in source.items():
                    with open(os.path.join(base, path), encoding="utf-8") as fh:
                        variables[name] = fh.read()
            if arm.get("contract"):  # shorthand kept for experiment 02
                with open(os.path.join(base, arm["contract"]), encoding="utf-8") as fh:
                    variables["contract"] = fh.read()
            prompt = render_prompt(template, variables)
            prompt_hash = sha256(prompt)

            same_arm = [r for r in recorded if r.get("arm") == arm["name"]]
            stale = {r["prompt_sha256"] for r in same_arm if r.get("prompt_sha256")} - {prompt_hash}
            if stale and not args.allow_prompt_change:
                sys.stderr.write(
                    "error: %s already holds %s runs made with a different prompt (%s).\n"
                    "Something was edited after those runs. Start a new runs directory, or\n"
                    "pass --allow-prompt-change if you know the edit is cosmetic.\n"
                    % (jsonl, arm["name"] or "unnamed-arm", ", ".join(sorted(stale)))
                )
                return 1

            done = {(r["model"], r["run"]) for r in same_arm if r.get("ok")}

            for model in models:
                cmd = build_command(executor, model)
                for index in range(n):
                    if (model, index) in done:
                        continue
                    label = "%s/%s/%s run %d" % (
                        cell["name"], arm["name"] or "-", model, index,
                    )
                    if args.dry_run:
                        print("would run %s (prompt %s)" % (label, prompt_hash))
                        continue
                    if args.budget_usd is not None and spent >= args.budget_usd:
                        sys.stderr.write(
                            "budget reached (%.2f of %.2f usd), stopping before %s\n"
                            % (spent, args.budget_usd, label)
                        )
                        stopped_by_budget = True
                        break

                    sys.stderr.write("running %s ... " % label)
                    sys.stderr.flush()
                    result = run_once(
                        cmd,
                        prompt,
                        executor.get("timeout_s", 420),
                        executor.get("prompt_via", "stdin"),
                    )
                    record = {
                        "experiment": plan["experiment"],
                        "plan_revision": plan.get("revision"),
                        "cell": cell["name"],
                        "arm": arm["name"],
                        "model": model,
                        "run": index,
                        "ts": now_iso(),
                        "prompt_sha256": prompt_hash,
                        "command": cmd,
                    }
                    record.update(result)
                    if harness and result.get("ok"):
                        record.update(
                            run_harness(base, harness, extract_artifact(result.get("output")))
                        )
                    append_jsonl(jsonl, record)

                    if result.get("ok"):
                        spent += result.get("cost_usd") or 0.0
                        note = ""
                        if harness:
                            note = " | tests %s passed, %s failed" % (
                                record.get("harness_passed", "?"),
                                record.get("harness_failed", "?"),
                            )
                        sys.stderr.write(
                            "ok (%.4f usd, %d chars)%s\n"
                            % (result.get("cost_usd") or 0.0, len(result.get("output") or ""), note)
                        )
                    else:
                        failures += 1
                        sys.stderr.write("FAILED: %s\n" % result.get("error"))
                if stopped_by_budget:
                    break
            if stopped_by_budget:
                break
        if stopped_by_budget:
            break

    if not args.dry_run:
        print("\nspent %.4f usd, %d failure(s)" % (spent, failures))
    return 1 if (failures or stopped_by_budget) else 0


if __name__ == "__main__":
    raise SystemExit(main())
