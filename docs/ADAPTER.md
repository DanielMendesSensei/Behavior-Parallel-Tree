# Adapter

The BPT core only declares: tree, mirror, contract, and spec. Whatever executes (worktrees, parallelism, build loop, code generation) is the adapter. The adapter is the only piece that knows about language, framework, and runtime. Switching stacks means switching adapters, without touching the core.

In v1 the adapter interface is deferred: the protocol, the envelope, and the hook table all exist, but the template only ships a placeholder adapter that does real scaffolding. The placeholder's other hooks respond with an empty ok status.

## Where the adapter is declared

The adapter is an executable pointed to in `bpt.config.yaml`:

```yaml
adapter: placeholder
```

The name resolves to an executable in the template (for example `tools/bpt/adapters/placeholder`). The core invokes that executable once per hook, per execution unit.

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

## Orchestration expectations

The core derives the parallelism waves by topological order of the DAG. The adapter honors the orchestration like this:

- **Worktree per node-per-side**: one worktree per `(side, id)` unit, on the `bpt/<side>/<id>` branch, created on top of the `base_branch`.
- **Context slicing**: each worktree sees the node's folders, the consumed contracts, and the side's kernel read-only. That slice is the goal of BPT: to minimize the context of each change.
- **Waves**: parallelism respects the DAG. The kernel waves run first and serialized (with the kernel CHANGELOG), then the behavior waves.
- **Build loop**: `codegen -> plan -> execute -> verify -> review`, with up to 3 attempts. The `findings` from one attempt come back as `feedback` on the next. On the 3rd failure the node stays `blocked` with the worktree preserved for inspection.
- **Bilateral contract test**: before considering a two-sided node done, it runs the consumer-driven contract test that keeps backend and frontend honest against the same spec.
- **yolo mode**: an accelerated orchestration mode, signaled in `mode`, for those who want to skip intermediate gates.

None of this lives in the core beyond the declaration: the core says what the unit is, what the branch is, what the slice is, and what the wave order is; the adapter executes.

## What the placeholder does

The template's placeholder adapter does **real scaffolding** and nothing more. The `plan`, `execute`, `verify`, `review`, and `codegen` hooks respond with `status: ok` and an empty payload, so you can watch the loop run end to end before plugging in a real stack.

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

What is out of scope for v1 and becomes future work: real orchestration (parallelism, automatic retries, real yolo, PR per PRD, deploy tracking), rich codegen with JSON Schema and `$ref`, and a multi-agent review committee. The interface above is already designed to receive that without changing shape.
