# Placeholder Adapter

This adapter honors the entire BPT interface but knows no stack. It exists to prove the adapter contract and to keep the template runnable without choosing a language, framework, or runtime. Of the six hooks, only `scaffold` does real work; the other five respond with an empty ok status.

The BPT core declares (tree, mirror, contract, spec) and the adapter executes (worktrees, parallelism, loop). This placeholder fills the executor's place without actually executing.

## Protocol

The adapter is an executable declared in `bpt.config.yaml` (here, `adapter: placeholder`). The core always invokes it the same way:

```
bpt-adapter <hook>
```

- Reads **one** JSON object from `stdin`.
- Writes **one** JSON object to `stdout`.
- Sends logs to `stderr`.
- `exit 0` means the hook ran (the actual result goes in the payload's `status`).
- `exit != 0` means the adapter broke.

The unit of execution is the **node per side**, keyed on `(side, id)`. Each node-per-side runs in its own worktree. There can be one adapter per side, that is, `backend` and `frontend` can point to different executables, each speaking the same neutral protocol.

## The six hooks

| hook | role | in this placeholder |
| --- | --- | --- |
| `scaffold` | creates mirrored folders + contract and spec stubs, idempotent | does real work |
| `plan` | builds the technical plan, writes no product | empty ok status |
| `execute` | implements only in the node's folders | empty ok status |
| `verify` | runs surface scenarios + unit tests + checks import direction | empty ok status |
| `review` | semantic review | empty ok status |
| `codegen` | materializes the neutral contract into the stack's types/validators in `__generated__/` | empty ok status |

## Example: calling scaffold

You pipe a node's JSON, with `id` and `sides`, to the `scaffold` hook:

```
echo '{
  "id": "product.list",
  "sides": ["backend", "frontend"]
}' | bin/bpt-adapter scaffold
```

What it creates, following the canonical forms (`id` `product.list` becomes path `product/list`):

- `apps/backend/behaviors/product/list/` with `src/` and `__generated__/`.
- `apps/frontend/behaviors/product/list/` with `src/` and `__generated__/`.
- `packages/contracts/product/list/contract.yaml` (stub), if it does not exist yet.
- `packages/contracts/product/list/spec.md` (stub from the spec), if it does not exist yet.

Scaffold is **idempotent**: running it again on an already created node neither erases nor duplicates anything. The mirrored folders on both sides share a single spec, which lives next to the contract, never duplicated per side. `src/` is for human code; `__generated__/` stays empty here, because what fills it is the `codegen` of a real adapter.

There is no per-node metadata file: the folder in the convention plus the entry in `bpt.config.yaml` are already the declaration.

## From placeholder to real adapter

A real adapter does not change the protocol, it swaps the implementation. You replace the scripts in `hooks/` with your stack's logic:

- `hooks/plan` starts producing a real technical plan.
- `hooks/execute` starts writing code inside the node's folders.
- `hooks/verify` starts running the surface scenarios, the unit tests, and the import-direction check (fails `kernel -> behaviors/*` and `behaviors/a -> behaviors/b`).
- `hooks/review` starts doing semantic review.
- `hooks/codegen` starts materializing the neutral contract into the stack's types and validators, inside `__generated__/`.

Since there can be one adapter per side, a backend side can generate types in one language and the frontend side in another, each reading the same neutral contract.

## Where to continue

The complete reference for the interface, the payloads, and the orchestration that a real adapter must honor (worktree per node-per-side on branch `bpt/<side>/<id>`, kernel waves first, `codegen -> plan -> execute -> verify -> review` loop with up to 3 attempts, bilateral contract test) is in `docs/ADAPTER.md`.
