# BPT: Behavior Parallel Tree

**An architecture for codebases that coding agents work on in parallel.**

Ask an agent to change one behavior of your app and it loads half the repo to find out what it may touch. Ask three agents to work at once and they collide, because nothing in a folder-per-feature layout says which pieces are independent. BPT fixes both by making the boundaries declared, checkable and machine-readable:

- **Every behavior is an island.** A behavior may import from its side's kernel and read the contracts it declares. Behavior to behavior imports are forbidden, and the rule is enforced, not just documented.
- **One neutral contract joins the sides.** The same behavior exists on backend and on frontend (or on any sides you declare), with one contract and one spec for all of them, never a copy per side.
- **The dependency graph is data.** One command reads the tree and derives the parallelism waves: which behaviors can be built at the same time, and which have to wait.
- **The context per change is bounded on purpose.** An agent building a behavior loads the node's folder, its own contract, the contracts it consumes, and the kernel read-only. Nothing else.

```bash
pip install pyyaml
./bpt validate
```

```
bpt validate: /path/to/project
parallelism waves (the adapter walks in this order):
  wave 1: product.list
  wave 2: product.detail

ok: bpt.config.yaml and the tree passed the 7 invariants (0 warning(s))
```

That output is the whole idea in one screen: two behaviors, mirrored across two sides, and the order they can be built in, derived rather than maintained by hand.

## Who this is for

Teams and solo builders who are handing implementation work to coding agents and want the boundaries to be a property of the repository instead of a paragraph in a prompt. It is equally useful without agents, as a way to keep features from growing into each other, but the parallelism and the context budget are the reasons it exists.

## Why not just organize by feature

Folder-per-feature gets you naming. It does not get you:

| | folder per feature | BPT |
|---|---|---|
| Cross-feature imports | nothing stops them | forbidden by rule, checkable by the adapter's `verify` |
| Machine-readable dependency graph | none, so no parallelism can be derived | `deps` and `consumes` per node, waves derived by one command |
| Spec per side | duplicated, and the copies drift | one neutral contract plus one spec for N sides |
| Rule for what goes in shared code | taste | the rule of three, plus a promotion gate for the kernel |

## Clone and go

Prerequisites: Python 3 with PyYAML, and only for the validator. That is tooling, not your app's stack: BPT knows nothing about your language, framework or runtime.

```bash
pip install pyyaml
./bpt validate      # checks the 7 invariants and prints the waves
./bpt help
```

## Folder tree

```
bpt.config.yaml              single declaration: sides, contracts, and nodes
bpt                          the CLI (validate, help)
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
  placeholder/               reference adapter (only scaffold does real work)
tools/
  bpt/validate.py            the validator (swappable tooling, not the app's stack)
docs/                        the rulebook and the formats
```

Inside each node there is `src/` (human code) and `__generated__/` (code materialized by the adapter from the contract). There is no per-node metadata file: the conventional folder plus the entry in `bpt.config.yaml` are already the declaration.

## The example that ships

Two real nodes, both mirrored in backend and frontend:

- `product.list`: no dependencies, so it lands in wave 1. Contract and spec in `packages/contracts/product/list/`.
- `product.detail`: depends on `product.list`, so it lands in wave 2. Contract and spec in `packages/contracts/product/detail/`.

Their code lives in `apps/backend/behaviors/product/<action>/` and `apps/frontend/behaviors/product/<action>/`. Delete both when you start declaring your own, and read `docs/ADDING-A-BEHAVIOR.md` for the step by step.

## Docs

- `docs/RULEBOOK.md`: the rulebook. Mirrored topology, canonical id and path, the neutral contract, the kernel, tests, and the advanced forms (one-sided nodes, per-side deps, grouping by prd).
- `docs/ADDING-A-BEHAVIOR.md`: how to add the 2nd, the 3rd, the Nth behavior.
- `docs/NAMING.md`: how to choose an id, and the granularity tests that decide whether something is one behavior or two.
- `docs/CONTRACT-FORMAT.md` and `docs/SPEC-FORMAT.md`: the two files every behavior owns.
- `docs/KERNEL.md`: what may live in the kernel, and the promotion rules that keep it small.
- `docs/ADAPTER.md`: the hook protocol an adapter implements.
- `docs/TESTING.md`: the three test layers and the bilateral contract test.
- `docs/MIGRATION.md`: renaming an id, and adopting BPT in an existing codebase.
- `CONTRIBUTING.md`: how to contribute to BPT itself.

## About the adapter

The core declares (tree, mirror, contract, spec) and checks the invariants. The adapter executes, and it is the only component allowed to know your language, framework and runtime. The two talk over a neutral process protocol: one JSON on stdin, one JSON on stdout, per hook, per execution unit.

The adapter shipped here is a placeholder: `scaffold` does real work (creates the mirrored folders and the stubs from the spec), and the other hooks answer with an empty ok. Writing the real one, for your stack, is the work BPT expects of you: `plan`, `execute` (only inside the node's folders), `verify` (run the spec scenarios and check the import direction), `review`, and `codegen` (materialize the neutral contract into your stack's types and validators). The protocol and the envelope are in `docs/ADAPTER.md`.

## Scope

BPT v1 is deliberately small: a convention, a neutral contract format, a spec format, and a validator that proves the tree is coherent. What it does not include yet, and why, is listed honestly at the end of `docs/RULEBOOK.md`. The `bpt/v1` schema is the contract this template owes you: see `CHANGELOG.md` for how it will change.

## License

MIT. Clone it, fork it, use it in closed source, no obligations beyond keeping the notice.
