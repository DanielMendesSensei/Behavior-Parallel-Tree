# BPT Validator

`tools/bpt/validate.py` is the reference validator for the template. It is **tooling**, not the app stack: it exists to check the tree and derive the parallelism waves, and it can be swapped for any equivalent implementation without affecting production code.

## Usage

```
./bpt validate
```

The command reads the root `bpt.config.yaml` plus the contracts and specs, runs the 7 invariants, and finally prints the parallelism waves.

## Dependency

Single dependency: **PyYAML**.

```
pip install pyyaml
```

Python 3 + PyYAML is intentional: it is lightweight, swappable tooling, deliberately decoupled from the app's language, framework, and runtime.

## The 7 invariants

1. Schema present and supported (`bpt/v1`).
2. Each `id` is unique and follows the `domain.action` format.
3. `sides` is not empty and every declared side exists.
4. `deps`/`consumes` refs exist, with no self-dependency, and the graph is acyclic (Kahn points to the cycle).
5. Every two-sided node has a contract; every one-sided node declares `contract: none`.
6. No `id` lives under a kernel folder (the `kernel` domain is reserved).
7. The file trio exists: `contract.yaml` + `spec.md` + the node's folder per side.

## Parallelism waves

Beyond validating, the core derives the **waves** by topological order of the dependency graph and prints them. Each wave is the set of nodes that can be built in parallel at that step, with the kernel waves first. It is the map the adapter uses to parallelize the work while respecting the DAG.
