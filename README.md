# BPT: Behavior Parallel Tree

BPT is two mirrored trees of behaviors, where each behavior is an isolated island that an agent builds in parallel, because the tree declares nodes, dependencies, and the neutral contract that links backend and frontend, with a single goal: to minimize the context needed to make a change.

This repository is a template. The idea is to clone it for each new project, delete the two example nodes, and start declaring your own behaviors. The core is stack-agnostic: it knows nothing about language, framework, or runtime. The one that does the real work is an adapter, chosen per project.

## Clone and go

Prerequisites: just Python 3 with PyYAML, and only for the tooling validator. This is not your app's stack: it is the tool that checks whether the tree is coherent.

```bash
pip install pyyaml
./bpt validate
```

Expected output: the validator derives the parallelism waves (the topological order the adapter will walk through) and confirms the 7 invariants.

```
bpt validate: /path/to/project
parallelism waves (the adapter walks in this order):
  wave 1: product.list
  wave 2: product.detail

ok: bpt.config.yaml and the tree passed the 7 invariants (0 warning(s))
```

## Folder tree

```
bpt.config.yaml              single declaration: sides, contracts, and nodes
bpt                          shortcut for ./bpt validate
apps/
  backend/
    behaviors/               the backend-side nodes (root declared in sides)
    kernel/                  cross-cutting backend infra (auth, db, config, app-shell)
  frontend/
    behaviors/               the frontend-side nodes
    kernel/                  cross-cutting frontend infra (+ design-system)
packages/
  contracts/                 one contract + one spec per behavior
adapters/
  placeholder/               example adapter (only does real scaffolding)
tools/
  bpt/validate.py            the validator (swappable tooling, not the app's stack)
docs/                        the rulebook and the contributing guide
```

Inside each node there is `src/` (human code) and `__generated__/` (code materialized by the adapter from the contract). There is no per-node metadata file: the conventional folder plus the entry in `bpt.config.yaml` are already the declaration.

## The example

The template ships with 2 real nodes, both mirrored in backend and frontend:

- `product.list`: no dependencies. Contract in `packages/contracts/product/list/contract.yaml`, spec in `packages/contracts/product/list/spec.md`.
- `product.detail`: depends on `product.list` (which is why it falls into wave 2). Contract and spec in `packages/contracts/product/detail/`.

Each node's code lives in `apps/backend/behaviors/product/<action>/` and `apps/frontend/behaviors/product/<action>/`. The spec sits next to the contract, a single one, never duplicated per side.

## Docs

- `docs/RULEBOOK.md`: the stack-agnostic rulebook. Mirrored topology, canonical forms for id and path, neutral contract, kernel, tests, and advanced examples.
- `docs/CONTRIBUTING.md`: how to add a behavior step by step.

## How to add a behavior

In short: choose the id in the `domain.action` format, create the contract folder plus the spec, declare the node in `bpt.config.yaml` (with `sides` and `deps`), run `./bpt validate`, and let the adapter build. The complete step by step is in `docs/CONTRIBUTING.md`.

## About the adapter

The core declares (tree, mirror, contract, spec); the adapter executes (worktrees, parallelism, loop). The adapter included here is a placeholder: it only does real scaffolding (creates the mirrored folders and the stubs from the spec). The remaining hooks return an empty ok status.

A real adapter, written for your stack, is what will run `plan`, `execute`, `verify`, `review`, and `codegen`: plan, implement only in the node's folders, run the surface scenarios and check the import direction, review, and materialize the neutral contract into the stack's types and validators.
