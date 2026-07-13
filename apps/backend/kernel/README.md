# Backend Kernel

This is the backend-side kernel: cross-cutting infrastructure that sits OUTSIDE the behavior tree. Only things like auth, database access (db), config, and app-shell live here, that is, the plumbing that several behaviors share.

The kernel is NOT a behavior. It has no contract, no spec, and does not appear as a node in `bpt.config.yaml`. The `kernel` domain is reserved: no behavior id can live under this folder.

## Direction rule (absolute)

- Behavior imports from the kernel: allowed.
- Kernel imports from a behavior: FORBIDDEN.

The kernel never knows a behavior by name. If something here needs to know which behavior calls it, that something is in the wrong place. The adapter's `verify` fails any import in the `kernel -> behaviors/*` direction.

## Shared business rules do not live here

A business rule that two sides or two behaviors must respect does NOT become kernel code. It becomes DATA, declared in the contract's `rules` block, and each side implements it. A bilateral test keeps both sides honest. The kernel holds infrastructure, not domain policy.

## Subfolders empty on purpose

This kernel is born empty because it is stack-agnostic: the BPT core knows no language, framework, or runtime. The subfolders (auth, db, config, app-shell, design-system, and the like) are filled by the adapter and the project's chosen stack, not by the core.

## Learn more

Kernel promotion criteria, the rule of three, anti-bloat, demotion, serialized waves, and full enforcement are in `docs/KERNEL.md`.
