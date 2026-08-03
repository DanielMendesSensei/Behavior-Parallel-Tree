"""Tests for the runner.

Two halves, and the second is the one that matters: the loop closes when it
should, and it refuses to close when it should not. A runner only ever seen
succeeding proves nothing about the attempt it is supposed to catch.

stdlib unittest, so the repository keeps its single dependency.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, TOOLS)

import run as runner  # noqa: E402

STUB = os.path.join(HERE, "fixtures", "stub_adapter.py")

CONFIG = """schema: bpt/v1
project: fixture
adapter: stub
sides:
  backend:  { root: apps/backend/behaviors,  kernel: apps/backend/kernel }
  frontend: { root: apps/frontend/behaviors, kernel: apps/frontend/kernel }
contracts: { root: packages/contracts }
nodes:
  - id: product.list
    sides: [backend, frontend]
    deps: []

  - id: product.detail
    sides: [backend, frontend]
    deps: [product.list]
"""

CONTRACT = """id: %s
version: 1
kind: query
title: fixture
authorization: { required: false, roles: [] }
input: {}
output: {}
rules: []
errors: []
"""

SPEC = """---
id: %s
title: fixture
---

## Behavior
Fixture.
"""


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def make_repo(root):
    """A minimal tree that validates, plus an adapter pointing at the stub."""
    write(os.path.join(root, "bpt.config.yaml"), CONFIG)
    for nid in ("product.list", "product.detail"):
        p = nid.replace(".", "/")
        write(os.path.join(root, "packages/contracts", p, "contract.yaml"), CONTRACT % nid)
        write(os.path.join(root, "packages/contracts", p, "spec.md"), SPEC % nid)
        for side in ("backend", "frontend"):
            write(os.path.join(root, "apps", side, "behaviors", p, "src", ".gitkeep"), "")
    for side in ("backend", "frontend"):
        write(os.path.join(root, "apps", side, "kernel", ".gitkeep"), "")

    write(os.path.join(root, "adapters/stub/adapter.yaml"),
          "name: stub\nversion: 1\ncommand: adapters/stub/bin/bpt-adapter\n"
          "execution_unit: side-node\nhooks: [scaffold, plan, execute, verify, review, codegen]\n")
    binp = os.path.join(root, "adapters/stub/bin/bpt-adapter")
    os.makedirs(os.path.dirname(binp), exist_ok=True)
    shutil.copy(STUB, binp)
    os.chmod(binp, 0o755)

    subprocess.run(["git", "-C", root, "init", "-q", "-b", "main"], check=True)
    subprocess.run(["git", "-C", root, "config", "user.email", "t@example.com"], check=True)
    subprocess.run(["git", "-C", root, "config", "user.name", "t"], check=True)
    subprocess.run(["git", "-C", root, "add", "-A"], check=True)
    subprocess.run(["git", "-C", root, "commit", "-qm", "fixture"], check=True)


class RunnerCase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="bpt-run-test-")
        make_repo(self.root)
        self.log = os.path.join(self.root, "envelopes.jsonl")
        os.environ["BPT_STUB_LOG"] = self.log
        os.environ["BPT_STUB_PLAN"] = "{}"

    def tearDown(self):
        subprocess.run(["git", "-C", self.root, "worktree", "prune"], capture_output=True)
        shutil.rmtree(self.root, ignore_errors=True)
        os.environ.pop("BPT_STUB_LOG", None)
        os.environ.pop("BPT_STUB_PLAN", None)

    def run_bpt(self, *extra):
        return runner.main([self.root] + list(extra))

    def report(self):
        with open(os.path.join(self.root, ".bpt", "last-run.json"), encoding="utf-8") as fh:
            return json.load(fh)

    def envelopes(self):
        if not os.path.exists(self.log):
            return []
        with open(self.log, encoding="utf-8") as fh:
            return [json.loads(l) for l in fh if l.strip()]

    # --- the loop closes -------------------------------------------------

    def test_every_unit_closes_on_the_first_attempt(self):
        self.assertEqual(self.run_bpt(), 0)
        rep = self.report()
        self.assertEqual(rep["summary"]["units"], 4)  # 2 nodes, 2 sides each
        self.assertEqual(rep["summary"]["ok"], 4)
        self.assertEqual(rep["summary"]["first_attempt_ok"], 4)

    def test_waves_run_in_dependency_order(self):
        self.run_bpt()
        order = [e["node"]["id"] for e in self.envelopes()]
        self.assertIn("product.list", order)
        self.assertIn("product.detail", order)
        self.assertLess(
            max(i for i, n in enumerate(order) if n == "product.list"),
            min(i for i, n in enumerate(order) if n == "product.detail"),
            "product.detail must not start before product.list has finished",
        )

    def test_the_envelope_carries_what_only_a_runner_can_produce(self):
        self.run_bpt()
        env = self.envelopes()[0]
        self.assertEqual(env["attempt"], 1)
        self.assertEqual(env["feedback"], [])
        self.assertTrue(env["workspace"]["worktree"].startswith(".bpt/worktrees/"))
        self.assertTrue(env["workspace"]["branch"].startswith("bpt/"))
        self.assertEqual(env["workspace"]["base_branch"], "main")
        self.assertIn("prior_artifacts", env)

    def test_artifacts_of_one_hook_reach_the_next(self):
        self.run_bpt()
        after_plan = [e for e in self.envelopes()
                      if e["hook"] in ("execute", "verify", "review")]
        self.assertTrue(after_plan)
        self.assertTrue(all("plan" in e["prior_artifacts"] for e in after_plan),
                        "the plan artifact must travel to the hooks after it")

    def test_dry_run_creates_nothing(self):
        self.assertEqual(self.run_bpt("--dry-run"), 0)
        self.assertFalse(os.path.exists(os.path.join(self.root, ".bpt")))
        self.assertEqual(self.envelopes(), [])

    def test_only_restricts_the_walk(self):
        self.assertEqual(self.run_bpt("--only", "product.list"), 0)
        self.assertEqual(self.report()["summary"]["units"], 2)

    # --- the loop refuses to close ---------------------------------------

    def test_a_unit_that_keeps_failing_ends_blocked_after_three_attempts(self):
        os.environ["BPT_STUB_PLAN"] = json.dumps({"always_fail": ["verify"]})
        self.assertEqual(self.run_bpt("--only", "product.list"), 1)
        rep = self.report()
        self.assertEqual(rep["summary"]["ok"], 0)
        self.assertTrue(all(u["attempts"] == 3 for u in rep["units"]))
        self.assertTrue(all(u["status"] == "blocked" for u in rep["units"]))

    def test_a_blocked_unit_keeps_its_worktree_for_inspection(self):
        os.environ["BPT_STUB_PLAN"] = json.dumps({"always_fail": ["verify"]})
        self.run_bpt("--only", "product.list")
        for unit in self.report()["units"]:
            self.assertTrue(os.path.isdir(os.path.join(self.root, unit["worktree"])))

    def test_it_recovers_when_the_failure_stops(self):
        os.environ["BPT_STUB_PLAN"] = json.dumps({"fail": {"verify": 2}})
        self.assertEqual(self.run_bpt("--only", "product.list"), 0)
        rep = self.report()
        self.assertEqual(rep["summary"]["ok"], 2)
        self.assertEqual(rep["summary"]["first_attempt_ok"], 0)
        self.assertTrue(all(u["attempts"] == 3 for u in rep["units"]))

    def test_findings_of_one_attempt_arrive_as_feedback_on_the_next(self):
        os.environ["BPT_STUB_PLAN"] = json.dumps({"fail": {"verify": 1}})
        self.run_bpt("--only", "product.list")
        second = [e for e in self.envelopes() if e["attempt"] == 2]
        self.assertTrue(second)
        self.assertTrue(all(e["feedback"] for e in second),
                        "attempt 2 must carry the findings of attempt 1")
        self.assertEqual(second[0]["feedback"][0]["hook"], "verify")

    def test_a_failed_wave_stops_the_walk(self):
        os.environ["BPT_STUB_PLAN"] = json.dumps({"always_fail": ["verify"]})
        self.assertEqual(self.run_bpt(), 1)
        ids = {u["id"] for u in self.report()["units"]}
        self.assertNotIn("product.detail", ids,
                         "nothing downstream may build on a wave that did not close")

    def test_a_broken_adapter_is_not_a_business_result(self):
        os.environ["BPT_STUB_PLAN"] = json.dumps({"broken": ["execute"]})
        self.assertEqual(self.run_bpt("--only", "product.list"), 1)
        self.assertEqual(self.report()["summary"]["blocked"], 2)

    def test_it_refuses_a_tree_that_does_not_validate(self):
        with open(os.path.join(self.root, "bpt.config.yaml"), "a", encoding="utf-8") as fh:
            fh.write("\n  - id: Bad.Id\n    sides: [backend]\n    contract: none\n    deps: []\n")
        with self.assertRaises(SystemExit) as caught:
            self.run_bpt()
        self.assertEqual(caught.exception.code, 1)
        self.assertEqual(self.envelopes(), [], "no hook may run on a tree that does not validate")

    # --- modes ------------------------------------------------------------

    def test_yolo_lets_review_speak_without_letting_it_block(self):
        os.environ["BPT_STUB_PLAN"] = json.dumps({"always_fail": ["review"]})
        self.assertEqual(self.run_bpt("--only", "product.list", "--mode", "yolo"), 0)
        rep = self.report()
        self.assertEqual(rep["summary"]["ok"], 2)
        self.assertEqual(rep["summary"]["first_attempt_ok"], 2)
        reviews = [h for u in rep["units"] for h in u["hooks"] if h["hook"] == "review"]
        self.assertTrue(all(h["status"] == "needs_changes" for h in reviews),
                        "yolo must not silence the review, only stop it gating")

    def test_outside_yolo_the_review_is_a_gate(self):
        os.environ["BPT_STUB_PLAN"] = json.dumps({"always_fail": ["review"]})
        self.assertEqual(self.run_bpt("--only", "product.list"), 1)

    def test_the_kernel_pre_wave_runs_first_and_alone(self):
        self.run_bpt("--kernel", "--only", "product.list")
        order = [(e["node"]["side"], e["node"]["id"]) for e in self.envelopes()]
        kernels = [i for i, (_, nid) in enumerate(order) if nid == "kernel"]
        others = [i for i, (_, nid) in enumerate(order) if nid != "kernel"]
        self.assertTrue(kernels, "the kernel pre-wave must run when asked for")
        self.assertLess(max(kernels), min(others),
                        "the kernel changes first, alone, before anything that depends on it")

    def test_two_sided_nodes_are_reported_as_pending_the_bilateral_test(self):
        self.run_bpt("--only", "product.list")
        self.assertEqual(self.report()["bilateral_pending"], ["product.list"])


if __name__ == "__main__":
    unittest.main()
