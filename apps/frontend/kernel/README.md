# Frontend Kernel

Cross-cutting infrastructure for the frontend side, OUTSIDE the behavior tree. Only what serves several behaviors at once and belongs to none of them lives here: `app-shell/` (layout, routing, global providers), `design-system/` (tokens, base components, themes), `auth/` (session, route guards), and `config/` (environment, feature flags).

The subfolders are born empty on purpose. The kernel starts lean; code only rises here when it passes the promotion rules (see `docs/KERNEL.md`).

## Direction rule

Dependency points in only one direction:

- a behavior CAN import from the kernel.
- the kernel NEVER imports from a behavior.
- the kernel CAN import from another kernel and from `packages/contracts`.

The adapter's `verify` fails `kernel -> behaviors/*` and `behaviors/a -> behaviors/b`. The `kernel` domain is reserved: no behavior id can live under a kernel folder.

## What does NOT go here

Shared business rules do not become kernel code. They are DATA, in the contract's `rules` block, and each side implements them, with a bilateral test keeping both sides honest.

## More details

Promotion, the rule of three, anti-bloat, demotion, and the kernel wave serialized before the behavior waves: all in `docs/KERNEL.md`.
