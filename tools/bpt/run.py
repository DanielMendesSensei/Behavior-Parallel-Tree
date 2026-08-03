#!/usr/bin/env python3
"""Reference runner for the Behavior Parallel Tree (BPT).

Development tooling, NOT the app stack. It walks the waves the validator
derives, gives every execution unit its own worktree, and drives the adapter
through the build loop.

Why this lives in the core and not in an adapter. `docs/ADAPTER.md` says the
core assembles the request envelope, and that envelope carries `attempt`,
`feedback` from the previous attempt, `prior_artifacts` from earlier hooks, and
the worktree and branch of the unit. None of those five can be read off the
tree, the contract or the spec: they only exist while a loop is running. The
adapter cannot produce them either, because it is invoked once per hook and
keeps nothing between invocations. So the protocol already required a runner on
this side of the line. What stays in the adapter is everything behind the six
hooks, which is the only part that knows a language.

Usage:
    ./bpt run                     walk every wave with the declared adapter
    ./bpt run --dry-run           print the plan, touch nothing
    ./bpt run --only product.list restrict to one node (repeatable)
    ./bpt run --jobs 4            run the units of a wave concurrently
    ./bpt run --mode yolo         review still runs, but stops being a gate
    ./bpt run --kernel            run the serialized kernel pre-wave first

Exit 0 when every unit ended ok, 1 when any unit ended blocked or the tree does
not validate.

Single dependency: PyYAML, same as the validator.
"""
import argparse
import concurrent.futures
import contextlib
import datetime
import io
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate as v  # noqa: E402  (same folder, same single dependency)

# The build loop of docs/ADAPTER.md. `scaffold` is not in it: it materialises a
# node once, before there is anything to build.
BUILD_LOOP = ["codegen", "plan", "execute", "verify", "review"]
MAX_ATTEMPTS = 3
STATE_DIR = ".bpt"


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def git(root, *args, **kw):
    return subprocess.run(
        ["git", "-C", root] + list(args), capture_output=True, text=True, **kw
    )


def die(msg):
    sys.stderr.write("error: %s\n" % msg)
    raise SystemExit(1)


def load_tree(root):
    """Refuse to run on a tree that does not validate.

    An incoherent tree produces a wave order that is wrong in a way nothing
    downstream can notice, so the gate belongs here and not in a comment.
    """
    v.ERRORS[:] = []
    v.WARNINGS[:] = []
    # The validator prints the waves on its way out. The runner prints its own
    # plan a few lines later, so that copy is swallowed rather than doubled.
    with contextlib.redirect_stdout(io.StringIO()):
        v.validate(root)
    if v.ERRORS:
        for e in v.ERRORS:
            sys.stderr.write("ERROR   %s\n" % e)
        die("the tree does not validate, so there is nothing safe to walk. Run ./bpt validate")
    cfg = v.load_config(root)
    if cfg is None:
        die("bpt.config.yaml could not be read")
    return cfg


def adapter_command(root, cfg):
    name = cfg.get("adapter")
    if not name:
        die("no 'adapter' declared in bpt.config.yaml")
    manifest = os.path.join(root, "adapters", name, "adapter.yaml")
    if not os.path.exists(manifest):
        die("adapter '%s' declared but %s not found" % (name, os.path.relpath(manifest, root)))
    with open(manifest, encoding="utf-8") as fh:
        man = v.yaml.safe_load(fh) or {}
    cmd = man.get("command")
    if not cmd:
        die("adapter '%s' has no 'command' in adapter.yaml" % name)
    return name, cmd


def build_units(cfg, wave_ids, only):
    """Expand node ids into execution units, keyed (side, id) as the rulebook says."""
    nodes = {n["id"]: n for n in cfg.get("nodes", []) or [] if isinstance(n, dict) and n.get("id")}
    sides_cfg = cfg.get("sides", {}) or {}
    contracts_root = (cfg.get("contracts", {}) or {}).get("root", "packages/contracts")
    units = []
    for nid in wave_ids:
        if only and nid not in only:
            continue
        node = nodes[nid]
        path = v.node_path(nid)
        two_sided = len(node.get("sides") or []) >= 2 and node.get("contract") != "none"
        for side in node.get("sides") or []:
            side_root = (sides_cfg.get(side) or {}).get("root", os.path.join("apps", side, "behaviors"))
            kernel = (sides_cfg.get(side) or {}).get("kernel", os.path.join("apps", side, "kernel"))
            deps = node.get("deps", [])
            if isinstance(deps, dict):  # per-side deps
                deps = deps.get(side, []) or []
            units.append({
                "id": nid,
                "side": side,
                "key": "%s/%s" % (side, nid),
                "paths": [os.path.join(side_root, path)],
                "deps": list(deps),
                "consumes": list(node.get("consumes") or []),
                "contract_ref": os.path.join(contracts_root, path, "contract.yaml") if two_sided else None,
                "spec_ref": os.path.join(contracts_root, path, "spec.md"),
                "kernel_ref": kernel,
                "worktree": os.path.join(STATE_DIR, "worktrees", side, nid),
                "branch": "bpt/%s/%s" % (side, nid),
            })
    return units


def kernel_units(cfg):
    """The kernel pre-wave: one unit per side, run one at a time.

    KERNEL.md: the kernel is everyone's base, so it never changes in parallel
    with what depends on it. It changes first, alone, and announces the change.
    Opt-in, because the config declares no kernel node and nothing here can
    infer that the kernel needs touching.
    """
    units = []
    for side, scfg in (cfg.get("sides", {}) or {}).items():
        kernel = (scfg or {}).get("kernel", os.path.join("apps", side, "kernel"))
        units.append({
            "id": "kernel",
            "side": side,
            "key": "%s/kernel" % side,
            "paths": [kernel],
            "deps": [],
            "consumes": [],
            "contract_ref": None,
            "spec_ref": None,
            "kernel_ref": kernel,
            "worktree": os.path.join(STATE_DIR, "worktrees", side, "kernel"),
            "branch": "bpt/%s/kernel" % side,
        })
    return units


def ensure_worktree(root, unit, base_branch):
    """One worktree per unit, on its own branch, cut from the base branch."""
    path = os.path.join(root, unit["worktree"])
    if os.path.isdir(os.path.join(path, ".git")) or os.path.isfile(os.path.join(path, ".git")):
        return None
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out = git(root, "worktree", "add", "-B", unit["branch"], path, base_branch)
    if out.returncode != 0:
        return out.stderr.strip()[:300]
    return None


def envelope(unit, hook, attempt, mode, base_branch, prior, feedback):
    """Exactly the fields docs/ADAPTER.md declares the core assembles."""
    return {
        "hook": hook,
        "mode": mode,
        "attempt": attempt,
        "node": {
            "id": unit["id"],
            "side": unit["side"],
            "deps": unit["deps"],
            "paths": unit["paths"],
        },
        "spec": {"ref": unit["spec_ref"]},
        "contract": {"ref": unit["contract_ref"]},
        "consumes": unit["consumes"],
        "workspace": {
            "worktree": unit["worktree"],
            "branch": unit["branch"],
            "base_branch": base_branch,
        },
        "kernel": {"ref": unit["kernel_ref"]},
        "prior_artifacts": prior,
        "feedback": feedback,
    }


def call_hook(cwd, command, hook, request, timeout):
    """One JSON in, one JSON out, logs on stderr, exit code separates a business
    result from a broken adapter."""
    started = time.time()
    try:
        proc = subprocess.run(
            [os.path.join(cwd, command) if not os.path.isabs(command) else command, hook],
            input=json.dumps(request, ensure_ascii=False),
            capture_output=True, text=True, timeout=timeout, cwd=cwd,
        )
    except subprocess.TimeoutExpired:
        return {"status": "broken", "error": "adapter timed out after %ss" % timeout}, 0
    except OSError as exc:
        return {"status": "broken", "error": "could not run adapter: %s" % exc}, 0
    ms = int((time.time() - started) * 1000)
    if proc.stderr:
        for line in proc.stderr.rstrip().splitlines():
            sys.stderr.write("      | %s\n" % line)
    if proc.returncode != 0:
        return {"status": "broken", "error": "adapter exited %d" % proc.returncode}, ms
    try:
        payload = json.loads(proc.stdout)
    except ValueError:
        return {"status": "broken", "error": "adapter did not return one JSON document"}, ms
    if not isinstance(payload, dict) or "status" not in payload:
        return {"status": "broken", "error": "adapter result has no 'status'"}, ms
    return payload, ms


def run_unit(root, unit, command, mode, base_branch, timeout, max_attempts):
    """The build loop for one unit, up to max_attempts, findings feeding forward."""
    record = {
        "key": unit["key"], "id": unit["id"], "side": unit["side"],
        "branch": unit["branch"], "worktree": unit["worktree"],
        "attempts": 0, "status": "blocked", "first_attempt_ok": False,
        "hooks": [], "findings": [], "tokens": 0,
    }
    cwd = os.path.join(root, unit["worktree"])
    feedback = []

    for attempt in range(1, max_attempts + 1):
        record["attempts"] = attempt
        prior = {}
        failed_at = None
        for hook in BUILD_LOOP:
            req = envelope(unit, hook, attempt, mode, base_branch, prior, feedback)
            res, ms = call_hook(cwd, command, hook, req, timeout)
            status = res.get("status")
            findings = res.get("findings") or []
            record["hooks"].append({
                "hook": hook, "attempt": attempt, "status": status,
                "ms": ms, "findings": len(findings),
            })
            usage = res.get("usage") or {}
            if isinstance(usage, dict) and isinstance(usage.get("tokens"), int):
                record["tokens"] += usage["tokens"]
            prior = dict(prior)
            prior.update(res.get("artifacts") or {})

            # In yolo the review still runs and still records findings, it just
            # stops being a gate. That is the only thing the mode changes here.
            gating = not (hook == "review" and mode == "yolo")
            if status != "ok" and gating:
                failed_at = hook
                feedback = findings or [{"hook": hook, "status": status,
                                         "error": res.get("error", "")}]
                record["findings"] = feedback
                break

        if failed_at is None:
            record["status"] = "ok"
            record["first_attempt_ok"] = attempt == 1
            return record
        sys.stderr.write("    attempt %d failed at %s\n" % (attempt, failed_at))

    # Three failures: the unit stays blocked and its worktree is preserved, so
    # a person can open it and see the state that produced the failure.
    return record


def plan_waves(cfg, root, only, with_kernel):
    nodes = {n["id"]: n for n in cfg.get("nodes", []) or [] if isinstance(n, dict) and n.get("id")}
    edges = v.build_edges(nodes)
    order = v.waves(edges)
    if order is None:
        die("dependency cycle: the validator should have caught this")
    plan = []
    if with_kernel:
        for u in kernel_units(cfg):
            plan.append([u])  # serialized: one wave per kernel unit
    for layer in order:
        units = build_units(cfg, layer, only)
        if units:
            plan.append(units)
    return plan


def main(argv=None):
    ap = argparse.ArgumentParser(description="Walk the BPT waves and drive the adapter.")
    ap.add_argument("root", nargs="?", default=os.getcwd())
    ap.add_argument("--dry-run", action="store_true", help="print the plan and touch nothing")
    ap.add_argument("--only", action="append", default=[], help="restrict to a node id (repeatable)")
    ap.add_argument("--jobs", type=int, default=1, help="units of a wave to run at once")
    ap.add_argument("--mode", default="normal", help="normal or yolo")
    ap.add_argument("--kernel", action="store_true", help="run the serialized kernel pre-wave first")
    ap.add_argument("--base", default=None, help="base branch for the worktrees")
    ap.add_argument("--attempts", type=int, default=MAX_ATTEMPTS)
    ap.add_argument("--timeout", type=int, default=1800, help="seconds per hook call")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    cfg = load_tree(root)
    adapter_name, command = adapter_command(root, cfg)

    base = args.base
    if not base:
        head = git(root, "rev-parse", "--abbrev-ref", "HEAD")
        base = head.stdout.strip() or "HEAD"

    plan = plan_waves(cfg, root, set(args.only), args.kernel)
    total = sum(len(w) for w in plan)
    if total == 0:
        print("nothing to run (no node matched)")
        return 0

    print("bpt run: %s" % root)
    print("adapter: %s (%s) | mode: %s | base: %s | jobs: %d" % (
        adapter_name, command, args.mode, base, args.jobs))
    for i, wave in enumerate(plan, 1):
        print("  wave %d: %s" % (i, ", ".join(u["key"] for u in wave)))
    if args.dry_run:
        print("\ndry run: %d unit(s) would run, nothing was created" % total)
        return 0

    started = now_iso()
    records = []
    for i, wave in enumerate(plan, 1):
        print("\nwave %d" % i)
        # Worktrees are created serially: git takes a lock on the index and two
        # concurrent `worktree add` on the same repository race for it.
        for unit in wave:
            problem = ensure_worktree(root, unit, base)
            if problem:
                die("could not create the worktree for %s: %s" % (unit["key"], problem))

        def work(unit):
            print("  %s" % unit["key"])
            return run_unit(root, unit, command, args.mode, base, args.timeout, args.attempts)

        if args.jobs > 1 and len(wave) > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
                wave_records = list(pool.map(work, wave))
        else:
            wave_records = [work(u) for u in wave]
        records.extend(wave_records)

        # A wave whose units did not all pass stops the walk: everything after
        # it depends on it, so continuing would build on a broken base.
        if any(r["status"] != "ok" for r in wave_records):
            print("\nwave %d did not close, stopping before the next one" % i)
            break

    # A two-sided node is only done when both sides are. The bilateral contract
    # test that should also run here has no hook in the protocol, so the runner
    # enforces the ordering and reports the gap instead of pretending.
    by_node = {}
    for r in records:
        by_node.setdefault(r["id"], []).append(r["status"])
    pending_bilateral = sorted(
        nid for nid, st in by_node.items()
        if len(st) > 1 and all(s == "ok" for s in st)
    )

    ok = [r for r in records if r["status"] == "ok"]
    blocked = [r for r in records if r["status"] != "ok"]
    report = {
        "root": root, "adapter": adapter_name, "mode": args.mode,
        "base_branch": base, "started": started, "finished": now_iso(),
        "units": records,
        "bilateral_pending": pending_bilateral,
        "summary": {
            "units": len(records),
            "ok": len(ok),
            "blocked": len(blocked),
            "first_attempt_ok": len([r for r in records if r["first_attempt_ok"]]),
            "tokens": sum(r["tokens"] for r in records),
        },
    }
    out_dir = os.path.join(root, STATE_DIR)
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "last-run.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)

    s = report["summary"]
    print("\n%d unit(s): %d ok, %d blocked" % (s["units"], s["ok"], s["blocked"]))
    print("first-attempt success: %d/%d" % (s["first_attempt_ok"], s["units"]))
    if s["tokens"]:
        print("tokens reported by the adapter: %d" % s["tokens"])
    for r in blocked:
        print("  blocked: %s (worktree kept at %s)" % (r["key"], r["worktree"]))
    if pending_bilateral:
        print("  bilateral contract test pending for: %s" % ", ".join(pending_bilateral))
        print("  (both sides passed; the protocol has no hook to run the test itself)")
    print("report: %s" % os.path.join(STATE_DIR, "last-run.json"))
    return 1 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
