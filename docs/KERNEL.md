# KERNEL

The kernel is the cross-cutting infrastructure that lives **outside the behavior tree**. There is one kernel per side (`apps/backend/kernel`, `apps/frontend/kernel`), declared in `bpt.config.yaml`. A behavior is an isolated island; the kernel is the common ground beneath all the islands.

The goal of BPT is to minimize the context needed to make a change. The kernel serves that goal when it concentrates what is genuinely shared. It **betrays** that goal when it becomes a dumping ground of conveniences: every thing that rises to the kernel without deserving it increases everyone's context. That is why the kernel is small by design and the bar for entry is high.

## The direction rule (absolute)

There is a single permitted direction:

> **A behavior imports from the kernel. The kernel NEVER imports from a behavior.**

The kernel knows no behavior by name. If you need to cite `product.list` inside the kernel, that thing is not kernel: it is a behavior leaked into the wrong place. This rule is what keeps each behavior an island: touching `product.detail` can never react back through the kernel and affect `product.list`.

The kernel describes itself without citing a domain. `auth`, `db`, `config`, `app-shell`, `design-system`: none of them needs to know what a product is.

## What belongs in the kernel

Cross-cutting infrastructure, used by many behaviors, with no domain flavor:

- **auth**: who the user is, session, role check (the *mechanism*, not the policy of which role accesses what; the policy lives in the contract's `authorization`).
- **db**: connection, pool, transaction, database client, migration runner (the *plumbing*, not the business tables).
- **config**: environment reading, flags, secrets, bootstrap.
- **app-shell** (frontend): root router, frame layout, global providers, top-level error handling.
- **design-system** (frontend): tokens, primitive components (button, input, table), theme. No domain screen.

A sign that it belongs: it describes itself without naming a behavior, it is cross-cutting, and it is used by 2 or more behaviors today.

## What does NOT belong in the kernel

- **A rule for ONE behavior**: if only `product.list` uses it, it lives in `product.list`. It never rises "just in case".
- **Contract types**: the neutral type lives in `contract.yaml`; the materialization lives in the node's `__generated__/` (via `codegen`). There are no shared domain types in the kernel.
- **A single screen**: a specific screen is a behavior on the frontend, not design-system. The design-system delivers the button; the checkout screen uses the button.
- **A shared business rule**: it becomes **data** in the contract's `rules` block, never kernel code (its own section below).
- **helpers / utils / misc / shared**: umbrella folders are forbidden. See anti-bloat.

## Promotion to the kernel: the 3 questions

A thing only rises to the kernel if the answer is **yes** to all three:

1. **Is it already used by 2 or more behaviors today?** (real usage, not an imagined future)
2. **Is it cross-cutting?** (it does not belong to any domain in particular)
3. **Does it describe itself without citing the name of any behavior?**

Any "no" rejects it. "In case someone needs it later" does not count as a yes on question 1.

## The rule of three (graduation)

Promotion happens on the third occurrence, not before:

1. **1st time**: it is born inside the behavior that needs it. It stays there.
2. **2nd time**: another behavior needs the same thing. **Copy it.** Duplication is cheap; the wrong abstraction is expensive.
3. **3rd time**: a third one needs it. Now it rises to the kernel, and the two earlier ones start importing from there.

Copying on the 2nd occurrence is intentional: it is the time you buy to see whether the three copies are really the same thing or three similar things that will diverge. If they diverged, they were never kernel.

## Anti-bloat

The kernel dies of success: the more useful it is, the more people want to glue things onto it. Countermeasures:

- **Owner per submodule**: each kernel submodule (`auth`, `db`, ...) has an owner. Nothing enters without passing through the submodule owner. This prevents no-man's-land.
- **`helpers`, `utils`, `misc`, `shared` forbidden**: every kernel folder names a concrete cross-cutting capability. If you cannot name the capability, it is not kernel.
- **Measure fan-in**: for each kernel module, count how many behaviors import from it (fan-in). Fan-in is the health metric: high justifies its existence, low is suspicious.
- **Demotion**: when a module's fan-in returns to **1 consumer**, it goes back down inside that behavior. A kernel with a single consumer is not kernel.
- **Ceiling**: there is a size ceiling per submodule. Blowing the ceiling **triggers** a mandatory review (not an automatic block, but a human gate).
- **Serialized kernel wave**: a change in the kernel runs in **its own wave, before** all the behavior waves, and comes with a **CHANGELOG**. Since the kernel is everyone's base, it never changes in parallel with those who depend on it; it changes first, alone, and announces the change.

## A shared business rule does NOT become kernel code

A business rule that both sides must respect (ordering, price rounding, case-insensitive search) is the classic example of a thing that "looks like" kernel. It is not.

It goes as **data**, in the contract's `rules` block:

```yaml
rules:
  - ordering: items by name ascending
  - search-case-insensitive: ignores case
```

**Each side implements the rule in its own stack.** A **bilateral contract test** (consumer-driven) keeps both honest: if the backend orders and the frontend does not, the bilateral test fails.

Why data and not shared code:

- Shared domain code would create a dependency crossing both sides and pierce the mirror. The neutral contract is precisely the **only** joint between backend and frontend.
- The rule stays readable by any agent without loading code from another stack: the context stays minimal.
- The core is language- and runtime-agnostic; a rule as data survives that, code does not.

**When is the rule too complex to fit as data?** It stops being "a rule" and becomes **a behavior**: create a dedicated node (e.g.: `price.calculate`) with its own contract, and the other nodes consume it via `consumes`. The complexity gets its own island, its own scenario tests, and an identity in both trees. What you do **not** do is hide it in a kernel module: that would reintroduce the domain dependency that BPT exists to eliminate.

## Data and migrations

- **Each behavior owns its own tables.** The migration lives together with the behavior, inside the node's folder.
- The kernel delivers the database **plumbing** (connection, transaction, migration runner), never a business table.
- **A table touched by 2 or more behaviors = explicit global coupling.** This is not forbidden, but it is a reviewed event: it needs to be declared and go through review, because it breaks the isolation of the islands. The default is for each table to have a single owner.

## Enforcement in the adapter's `verify`

The adapter's `verify` hook checks the import direction and fails the build if the graph violates the rule. Edges:

**Permitted:**

| From | To |
| --- | --- |
| `behaviors/*` | `kernel` |
| `behaviors/*` | `contracts` |
| `kernel` | `kernel` |
| `kernel` | `contracts` |

**Forbidden:**

| From | To | Why |
| --- | --- | --- |
| `kernel` | `behaviors/*` | pierces the absolute direction |
| `behaviors/a` | `behaviors/b` | a behavior does not import a behavior; the joint is the contract |

A behavior talks to another behavior **only** through the contract (`consumes`), never by direct import of code.

The static validator reinforces this from another angle: the `kernel` domain is **reserved** (invariant 6 of `./bpt validate`), so no node `id` can be born under the kernel folder.

## DO vs DON'T

**1. Generic HTTP client**
DO: `kernel/http` with the base client, retry, timeout. DON'T: `kernel/product-api` that knows how to assemble the list product call (that belongs to the `product.list` behavior).

**2. Table component**
DO: `design-system/table` (generic columns, visual sorting). DON'T: `design-system/product-table` with columns `name, price, available` (that is the `product.list` screen).

**3. Ordering rule**
DO: `rules: [ordering: items by name ascending]` in the contract, each side implements it, the bilateral test guards it. DON'T: `kernel/sorter` with the logic for ordering products.

**4. Role check**
DO: `kernel/auth` that answers "which role this user has". DON'T: `kernel/auth` deciding that "a customer can list products" (that policy lives in the contract's `authorization.roles`).

**5. Data table**
DO: migration of `products` inside `apps/backend/behaviors/product/list/`, single owner. DON'T: migration of `products` in `kernel/db/migrations` as if it were infrastructure.

**6. A rule too complex for data**
DO: promote the calculation to its own node `price.calculate` with a contract, consumed via `consumes`. DON'T: `kernel/pricing` with the tree of discounts and taxes.
