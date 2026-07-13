# Migration

This document covers two migration operations in BPT:

1. Renaming a behavior's id.
2. Adopting BPT in code that already exists (an overview of the incremental, strangler-style path).

Neither depends on automatic tooling. In v1, BPT declares and validates; moving folders and rewriting references is manual work (or your adapter's work, if you write one). The only automatic piece here is `./bpt validate`, which fails if anything ended up inconsistent.

---

## Renaming an id

The id is the behavior's identity. It appears in the folder convention (`apps/<side>/behaviors/<path>/`), in the contract path (`packages/contracts/<path>/`), in `bpt.config.yaml`, and in every `deps`/`consumes` that points to it. For that reason, in practice, the id is immutable: there is no "rename" operation. What exists is moving everything that carries that id to the new id, all at once, and validating.

Example: renaming `product.list` to `catalog.list`.

Recall the canonical forms before you start:

- id: `domain.action`, lowercase, dots separate segments, hyphens only in compounds, 2 to 3 segments.
- path: the dot becomes a slash, so `catalog.list` lives in `catalog/list`.

### Step by step

1. **Move the behavior folders on both sides.**
   The same behavior exists on each side with the same identity, so the two move together:
   - `apps/backend/behaviors/product/list/` becomes `apps/backend/behaviors/catalog/list/`
   - `apps/frontend/behaviors/product/list/` becomes `apps/frontend/behaviors/catalog/list/`

   Carry the entire node content (the `src/` folder with the human code and, if it exists, `__generated__/`). The `__generated__/` folder can be regenerated later by the adapter's `codegen` hook, so it is fine if it is left behind.

2. **Move the folder in `packages/contracts`.**
   `packages/contracts/product/list/` becomes `packages/contracts/catalog/list/`. That carries the `contract.yaml` and the `spec.md` with it (the spec is single, next to the contract, never duplicated per side).

3. **Update the `id` field inside the contract.**
   In `packages/contracts/catalog/list/contract.yaml`, the `id` stops being `product.list` and becomes `catalog.list`. Also adjust the `id` in the `spec.md` front-matter and the spec's `contract` field (which points at the path, now `catalog/list`).

4. **Update `bpt.config.yaml`.**
   Swap the node entry in `nodes`: the id `product.list` becomes `catalog.list`. The node's `sides` block stays the same (the mirrored topology did not change).

5. **Update every `deps` and `consumes` that points at the old id.**
   This is the step that most often slips. Search for `product.list` in:
   - `deps` of other nodes in `bpt.config.yaml` (for example, `product.detail` depends on `product.list` and needs to depend on `catalog.list` instead).
   - `consumes` in the front-matter of other `spec.md` files (a composite screen that consumes this contract).
   - per-side `deps`, when the graph diverges (the form `deps {backend [...], frontend [...]}`): check both sides.

   Remember that `deps` and `consumes` reference by id, not by file path. Everywhere that wrote `product.list` now writes `catalog.list`.

6. **Run the validator.**
   ```
   ./bpt validate
   ```
   It fails if anything was left half done. The invariants that most often catch a rename:
   - **unique id in `domain.action` format**: catches the case where you renamed the config but not the folder, or vice versa.
   - **`deps`/`consumes` refs exist**: catches the orphaned `deps` still pointing at `product.list`.
   - **acyclic graph**: catches the rare case where the rename created a cycle (Kahn shows where).
   - **file trio exists** (contract + spec + folder per side): catches the folder you forgot to move on one of the sides.

   Only consider the rename done when `./bpt validate` passes clean.

### What NOT to do

- Do not let the old id and the new one coexist. There is no id alias or redirect in v1. It is a clean cut.
- Do not rename just one side. The behavior has the same identity on both sides; one side without the other breaks the file-trio invariant and the mirror.
- Do not edit `__generated__/` by hand to "fix" the id. That is `codegen` territory; regenerate it.

---

## Adopting BPT in existing code

The path is incremental, strangler style: you do not rewrite the system. You draw the BPT boundary around what already exists and pull it in piece by piece, while the legacy keeps running behind the kernel.

> The full brownfield guide (large-scale adoption, systematic strangling, version coexistence) is future work, outside v1. What is here is the overview of the path, enough to get started without painting yourself into a corner.

### The idea in one sentence

Treat the legacy system as cross-cutting infrastructure (kernel) and extract visible behaviors into the tree, one at a time, each with its own contract.

### Adoption steps

1. **Identify the visible behaviors.**
   A behavior is a domain action with an observable result, from the point of view of whoever uses the system: "list products", "detail product", "filter catalog". Do not look at the legacy's internal structure (classes, tables, services); look at the surfaces (screens, endpoints, commands, jobs) and ask what action each one delivers. Each candidate action becomes an id in the form `domain.action`.

2. **Create contracts for the boundaries that already exist.**
   For each identified behavior, write a `contract.yaml` that describes the boundary as it is today: `input`, `output`, `errors`, `rules`, with the neutral types (`text`, `integer`, `decimal`, `boolean`, `money`, `list`, `object`). You are documenting the real contract of what the legacy already does, not inventing a new one. Write the `spec.md` next to it, with the scenarios per surface. Start with the most stable and most consumed boundaries: they give the biggest return in clarity.

3. **Move one screen (one behavior) at a time.**
   Pick a behavior and bring the code into the node folders (`apps/<side>/behaviors/<path>/src/`), respecting the mirrored topology: the backend and the frontend of the same behavior get the same identity and the same spec, linked by the contract. Register the node in `bpt.config.yaml` with its `sides` and `deps`. Run `./bpt validate`. Only then move to the next behavior. One behavior at a time keeps the change radius small, which is BPT's goal.

4. **Leave the legacy behind the kernel.**
   Everything not yet extracted keeps existing, but the new behavior does not talk directly to the scattered legacy: it talks to its side's kernel (cross-cutting infra: auth, db, config, app-shell, design-system). The legacy becomes a cross-cutting dependency accessed through the kernel. This respects the import-direction rule (a behavior imports from the kernel, the kernel never imports from a behavior) and keeps the legacy isolated behind a single boundary, instead of leaking into every new node.

   As more behaviors move out into the tree, the legacy behind the kernel shrinks. When a piece of legacy stops being used by any behavior, it can be removed. That is the strangling: the new grows, the old withers.

### Suggested order in practice

- Start with a read behavior, simple and dependency-free (a leaf `query`, like `product.list`). Less risk, an easier contract to get right.
- Then pull the behaviors that depend on it, in topological order (the waves the core derives). That way the `deps` already point at nodes that exist.
- Leave the write behaviors and the flows that cross several behaviors for when you already have confidence in the shape of the contracts.

### What to expect from v1

- **No automatic migration.** There is no tool that reads your legacy code and generates contracts or moves folders. `./bpt validate` checks consistency after you have done the work; it does not do the work.
- **Shared business rules become data, not code.** If a legacy rule must hold on both sides, it goes into the contract's `rules` block and each side implements it, with a bilateral test. Do not create a shared domain package during adoption; that reintroduces the global coupling that BPT exists to avoid.
- **The full brownfield guide is future work.** Version coexistence (N/N-1, expand/contract), a central contract registry, and real extraction orchestration are outside v1. For now, adoption is manual, incremental, and validated at each step.
