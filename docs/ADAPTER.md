# Adapter

The BPT core declares the tree, the mirror, the contract and the spec, and it
**walks them**: `./bpt run` derives the waves, cuts a worktree per execution unit,
and drives the build loop. The adapter is what happens behind the six hooks, and it
is the only piece that knows about language, framework and runtime. Switching stacks
means switching adapters, without touching the core.

That line used to sit one step further out, with orchestration on the adapter's side.
It was in the wrong place, and the envelope below is the proof: the core assembles it,
and it carries `attempt`, the `feedback` of the previous attempt, the `prior_artifacts`
of earlier hooks, and the worktree and branch of the unit. None of those five can be
read off the tree, the contract or the spec. They only exist while a loop is running,
and the adapter cannot hold them because it is invoked once per hook and keeps nothing
between invocations. Creating a worktree, walking a wave, counting to three and
carrying findings forward do not know your language, so they belong here.

## Where the adapter is declared

The adapter is an executable pointed to in `bpt.config.yaml`:

```yaml
adapter: placeholder
```

The name resolves to an adapter directory at the root, `adapters/<name>/`, whose executable is declared in `adapters/<name>/adapter.yaml`. For the one shipped here that is `adapters/placeholder/bin/bpt-adapter`. The core invokes that executable once per hook, per execution unit.

## Execution unit

The execution unit is the **node per side**, keyed on `(side, id)`. The two-sided node `product.list` produces two units: `(backend, product.list)` and `(frontend, product.list)`. Each unit has its own worktree.

The adapter can be a single one for both sides or one per side. One adapter per side is a valid and common choice, since backend and frontend usually live in different stacks.

## Neutral protocol

The contract between core and adapter is a process protocol, language-neutral:

```
bpt-adapter <hook>
```

- **stdin**: exactly 1 JSON document, the request envelope.
- **stdout**: exactly 1 JSON document, the hook result.
- **stderr**: free-form logs (progress, diagnostics). The core passes stderr through without interpreting it.

### Exit code semantics

- **exit 0**: the adapter ran. What actually happened is in the `status` of the output JSON (`ok`, `blocked`, `skipped`). A node still blocked after 3 attempts still exits with exit 0 and `status: blocked`.
- **exit != 0**: the adapter broke. There is no reliable result; the core treats it as an infrastructure failure, not a business result.

Practical rule: a product error (the behavior did not get done) is `exit 0` with the status in the payload; a tooling error (the adapter itself failed) is `exit != 0`.

## Request envelope (stdin)

The core assembles the envelope from the tree, the contract, and the spec. Fields:

| Field | Meaning |
|-------|-------------|
| `hook` | which of the 6 hooks to run (`scaffold`, `plan`, `execute`, `verify`, `review`, `codegen`) |
| `mode` | orchestration mode (for example `normal` or `yolo`) |
| `attempt` | attempt number in the loop (1 to 3) |
| `node.id` | canonical node id, form `domain.action` |
| `node.side` | side of this unit (`backend`, `frontend`, or another declared side) |
| `node.deps` | ids of the nodes this one depends on (already resolved per side when the graph diverges) |
| `node.paths` | folders of the node on this side, root `apps/<side>/behaviors/<path>/` |
| `spec.ref` | path of the single spec, `packages/contracts/<path>/spec.md` |
| `contract.ref` | path of the contract, `packages/contracts/<path>/contract.yaml` (or null on a one-sided node with `contract: none`) |
| `consumes` | contracts consumed by this node (composed screens consume N contracts) |
| `workspace.worktree` | path of this unit's worktree |
| `workspace.branch` | the unit's branch, `bpt/<side>/<id>` |
| `workspace.base_branch` | base branch the worktree was created on |
| `kernel.ref` | root of the side's kernel, `apps/<side>/kernel` (read-only) |
| `prior_artifacts` | artifacts produced by earlier hooks of this unit (for example the plan from `plan`) |
| `feedback` | findings from the previous attempt, when `attempt > 1` |

## Result (stdout)

The output JSON always carries a `status`. Beyond that it may carry artifacts that the core passes on as `prior_artifacts` to the next hook, and `findings` that become `feedback` on the next attempt.

```json
{ "status": "ok", "artifacts": {}, "findings": [] }
```

## The 6 hooks

| Hook | What it does | What it writes |
|------|-----------|---------------|
| `scaffold` | creates the node's mirrored folders from the spec, plus a contract and spec stub. Idempotent: running it again neither duplicates nor overwrites human work | `apps/<side>/behaviors/<path>/src/`, stub in `packages/contracts/<path>/` |
| `plan` | produces a technical plan to implement the node. Does not write product code | plan artifact in `prior_artifacts` |
| `execute` | implements the behavior, writing only inside the node's folders | `apps/<side>/behaviors/<path>/src/` |
| `verify` | runs the surface scenarios plus the unit tests and checks import direction | verification report, `status`, and `findings` |
| `review` | semantic review of what was built; a gate after green | `status` and `findings` |
| `codegen` | materializes the neutral contract into the stack's types and validators | `apps/<side>/behaviors/<path>/__generated__/` |

Boundary rules every hook respects:

- Human code lives in `src/` inside the node; generated code lives in `__generated__/` inside the node. Only `codegen` writes to `__generated__/`.
- `execute` writes only in the node's folders. Consumed contracts and the kernel enter as read-only.
- `verify` rejects imports from `kernel -> behaviors/*` and from `behaviors/a -> behaviors/b`. It permits `behaviors/* -> kernel`, `behaviors/* -> contracts`, `kernel -> kernel`, and `kernel -> contracts`.

## Orchestration: what `./bpt run` does

The core derives the waves by topological order of the DAG and then walks them.
None of the steps below knows a language, which is why they are here and not in
your adapter.

- **Worktree per node-per-side**: one worktree per `(side, id)` unit, at
  `.bpt/worktrees/<side>/<id>`, on the `bpt/<side>/<id>` branch, cut from the
  `base_branch`. Worktrees within a wave are created serially, because git locks
  the index and two concurrent `worktree add` race for it.
- **Context slicing**: each worktree sees the node's folders, the consumed
  contracts, and the side's kernel read-only. That slice is the goal of BPT: to
  minimize the context of each change.
- **Waves**: `--jobs N` runs the units of a wave concurrently. A wave whose units
  did not all pass stops the walk, because everything after it would build on a
  base that is not there.
- **Kernel pre-wave**: `--kernel` runs one unit per side first, one at a time,
  before any behavior wave. It is opt-in because the config declares no kernel
  node, so nothing can infer that the kernel needs touching.
- **Build loop**: `codegen -> plan -> execute -> verify -> review`, up to 3
  attempts. The whole chain repeats on failure. The `findings` of one attempt come
  back as `feedback` on the next, and the `artifacts` of one hook reach the next as
  `prior_artifacts`. On the third failure the unit stays `blocked` and its worktree
  is preserved, so a person can open the state that produced the failure.
- **yolo mode**: `--mode yolo` keeps the review running and keeps recording its
  findings; it only stops the review from being a gate. Nothing else changes.
- **Report**: `.bpt/last-run.json` carries, per unit, the attempts, the status of
  every hook call, the duration, the findings and whatever token count the adapter
  reported. First-attempt success rate and tokens per change are counted from it.

### The one expectation the protocol cannot meet yet

A two-sided node should not be done until the consumer-driven **bilateral contract
test** has run against both sides. None of the six hooks is that test: `verify` is
scoped to one unit, and the test is by definition about two. So the runner enforces
the ordering (a two-sided node is only reported done when every side passed) and
then lists the node under `bilateral_pending`, rather than pretending the check ran.

Closing this needs a protocol change, not an adapter: either a seventh hook keyed on
the node instead of the unit, or a second invocation of `verify` carrying both sides.
It is named here so that whoever writes an adapter knows the gap is in the interface
and not in their code.

## What the placeholder does

The template's placeholder adapter does **real scaffolding** and nothing more. The `plan`, `execute`, `verify`, `review`, and `codegen` hooks respond with `status: ok` and an empty payload.

That is what makes it useful before you have written anything: `./bpt run` walks the real waves, cuts the real worktrees and drives the real loop against those empty hooks, so you can watch the whole thing end to end and read the report before a single line of your stack exists. Start with `./bpt run --dry-run` to see the plan without creating a worktree.

### Example scaffold call

Input (stdin of `bpt-adapter scaffold`):

```json
{
  "hook": "scaffold",
  "mode": "normal",
  "attempt": 1,
  "node": {
    "id": "product.list",
    "side": "backend",
    "deps": [],
    "paths": ["apps/backend/behaviors/product/list"]
  },
  "spec": { "ref": "packages/contracts/product/list/spec.md" },
  "contract": { "ref": "packages/contracts/product/list/contract.yaml" },
  "consumes": [],
  "workspace": {
    "worktree": ".bpt/worktrees/backend/product.list",
    "branch": "bpt/backend/product.list",
    "base_branch": "main"
  },
  "kernel": { "ref": "apps/backend/kernel" },
  "prior_artifacts": {},
  "feedback": []
}
```

Output (stdout):

```json
{
  "status": "ok",
  "artifacts": {
    "created": [
      "apps/backend/behaviors/product/list/src/",
      "packages/contracts/product/list/contract.yaml",
      "packages/contracts/product/list/spec.md"
    ]
  },
  "findings": []
}
```

Running the same scaffold again returns `status: ok` with an empty `created`: the hook is idempotent and does not touch what already exists.

## How to write a real adapter

1. Copy the placeholder folder into a new adapter folder (for example per stack) and point `adapter:` in `bpt.config.yaml` at the new executable.
2. Replace the hooks one by one inside `hooks/`. Start with `codegen` (to get types for your stack) and `execute`, then `verify`, `review`, and `plan`. The placeholder's `scaffold` already serves as a base.
3. Keep the protocol: read 1 JSON from stdin, write 1 JSON to stdout, send logs to stderr, use exit 0 for a business result and exit != 0 only when the adapter itself breaks.
4. Respect the import boundaries and the write-per-folder rule. `verify` is where you enforce import direction in your language.
5. One adapter per side is a valid choice: declare each side's executable if backend and frontend use different stacks. The `(side, id)` key already separates the units, so each adapter only needs to take care of its own side.

Orchestration is no longer future work: waves, worktrees, `--jobs`, the three attempts, feedback forward and yolo all ship in `./bpt run`, and `tools/bpt/tests/test_run.py` proves the loop both closes and refuses to.

What is still out of scope for v1: the bilateral contract test (the gap named above, which needs a protocol change), PR per PRD and deploy tracking, rich codegen with JSON Schema and `$ref`, a multi-agent review committee, and any derivation of the dependency graph, which today is written by hand in `bpt.config.yaml` and only read by the core.
