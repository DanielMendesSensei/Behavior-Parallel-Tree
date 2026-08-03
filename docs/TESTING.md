# Tests and Verification in BPT

BPT has a single goal: to minimize the context needed to make a change. The test model serves that goal. Each type of test has a fixed place, a narrow responsibility, and a clear rule about whether or not it survives a refactor. When that is respected, an agent can work a behavior as an isolated island without carrying the rest of the system in their head.

This document describes the three test layers, how the scenario is projected per surface, how the adapter's `verify` consumes the spec scenarios, the bilateral contract test, the optional audits (property and mutation), and semantic review as the final gate.

## The three layers

There are three layers with distinct roles. The rule that separates one from another is simple: the scenario tests the **what** (observable behavior), the unit tests the **how** (internals), the flow tests the **journey** (several behaviors together).

| Layer | What it tests | Where it lives | Survives a refactor? |
| --- | --- | --- | --- |
| Scenario | Observable behavior: the contract and the surface. Never cites a function, class, or table name. | `packages/contracts/<path>/spec.md`, in the Scenarios section | Yes. It only changes when the observable behavior changes. |
| Unit | Internals: the how. Internal logic, branches, edge cases of a code unit. | Next to the code, inside the node's `src/` | No. It is disposable: it changes along with the code it covers. |
| Flow / e2e | A journey that crosses N behaviors, anchored to a PRD. | `packages/contracts/_flows/<prd>/` | Partial. It survives an internal refactor; it changes when the business journey changes. |

The intuition behind the "survives a refactor" column: the scenario and the unit exist at different levels of stability on purpose. The scenario is a contract with the world and must last; the unit is scaffolding you throw away when you rewrite the unit. If an internal refactor breaks a scenario, the scenario was looking at the wrong place (at the how, not the what).

## Scenario: only contract and surface

The scenario is the central layer of BPT because it is the only one that lives on the behavior's boundary, not inside it. It speaks of two things, and only those two:

- The **contract** (`contract.yaml`): input, output, `rules`, `errors`, authorization.
- The **surface** (declared in the spec: screen, endpoint, cli-command, job, event).

A scenario never mentions the name of a function, a method, a table, or a component. If it needs those names to be written, it has become a disguised unit test. The text of a scenario must remain valid even if the node's entire internal implementation is rewritten from scratch in another stack.

The scenarios live in the **Scenarios** section of the `spec.md`, written in given / when / then. Each scenario marks which one it belongs to:

- `[contract]`: verifiable at the data boundary, independent of visual surface. This is what the backend runs.
- `[screen]` (or the equivalent surface): verifiable on the concrete surface. This is what the frontend runs.

### The "then" is projected per surface

A single scenario has one "given" and one "when", but the "then" is **projected per surface**. The observable behavior is one; the way to observe it depends on where you look.

Example, for `product.list` with the rule `ordering: items by name ascending`:

- `[contract]` projection (backend verify): the `then` asserts about the contract's `output`. "Then the `items` list comes ordered by `name` ascending and `total` reflects the count." Runs against the data response, no screen.
- `[screen]` projection (frontend verify): the `then` asserts about the surface. "Then the products screen shows the items in name-ascending order." Runs against the rendered surface.

The backend `verify` runs the `[contract]` projections; the frontend `verify` runs the `[screen]` projections. Each side proves the same truth in its own language. This is what allows mirroring the behavior on both sides without duplicating the spec: the spec is single, and only the projections split apart.

### UI binding: deterministic frontend verify

A `[screen]` scenario cannot depend on visible text or on layout structure, otherwise it breaks with every copy or CSS adjustment, and it goes back to not surviving a refactor. To keep the frontend `verify` deterministic, the spec declares `ui_bindings`: a neutral map of **surface to stable handle**.

The handle is a stable identifier (for example a test id) that the scenario references by logical name. The adapter, in `codegen` or `execute`, materializes that handle on the stack's concrete surface. The scenario says "the handle `product-list` contains the ordered items"; it does not say "the `<ul class=...>` contains". This way the scenario text stays stable and the frontend `verify` has a deterministic target to inspect.

## Unit: disposable, glued to the code

The unit tests the internals: conditional branches, edge cases of a function, invariants of an internal data structure. It lives inside the node's `src/`, next to the code it covers, and belongs to the same context scope as the code.

The property that defines the unit is being **disposable**. When you rewrite the unit, you rewrite (or delete) its unit tests without ceremony. They are not a contract with anyone outside the node; they are a tool of the unit's author. That is why they can and should cite function names and internal structure: that is exactly what they are testing.

A unit never leaks outside the node. If a test needs to know the internals of two behaviors at the same time, it is not a unit: it either became a scenario (on the boundary) or a flow (crossing behaviors).

Two consequences of that scope, worth saying out loud because the unit layer is the one place BPT deliberately tests the how, and testing the how is normally the mistake:

- **A unit test can never block another node.** It runs inside one unit's worktree, against one node's code, as step 4 of that unit's `verify`. A stale unit test stops the agent that wrote it and nobody else. The reason the usual advice says never test implementation is that the test outlives the code and becomes a second source of truth for it; here the test is scoped and disposable, so the failure mode does not reach.
- **Its source of truth is the plan, not the code.** If the same agent writes the implementation and then writes tests by reading what it just wrote, the tests only restate the code and pass by construction. That is why `plan` may emit a spec per module, in the "these inputs go in, this comes out" form, before `execute` runs: the unit test is written against that, not against the implementation.

## Flow / e2e: the journey across N behaviors

The flow test covers a business journey that crosses several behaviors, anchored to a PRD. It lives in `packages/contracts/_flows/<prd>/`, outside any node, because no node owns it: the owner is the PRD level.

Example: a purchase journey that passes through `product.list`, `product.detail`, `cart.review`, and `checkout.pay` lives in `packages/contracts/_flows/checkout-v1/`. It does not belong to any of those nodes individually; it verifies that the seam between them delivers the journey promised in the PRD.

The flow is the only test authorized to know several behaviors at once. Precisely for that reason it is expensive in context and should be rare: one per PRD journey, not one per possible combination of nodes.

## Bilateral, consumer-driven contract test

A two-sided node exists on both sides with the same identity and the same spec, linked by the neutral contract. The shape of the contract (the structure of `input` and `output`) can even be checked by structural comparison, but **shape is not enough**: two sides can agree on shape and disagree on meaning. The backend can order by name descending while the frontend expects ascending; both respect the `output` shape and yet the behavior is broken.

That is why every two-sided node goes through a **bilateral, consumer-driven contract test** before being considered done:

- **Consumer-driven**: the consumer (typically the frontend, or the node that appears in `consumes`) declares what it expects from the contract, including the `rules` that depend on that meaning. That expectation is the source of truth for the test.
- **Bilateral**: the provider (typically the backend) is verified against that expectation. Both sides are kept honest by the same set of contract scenarios, each proving its own projection (`[contract]` on one side, `[screen]` on the other).

This is where the decision to treat a shared business rule as **data** closes the loop: the contract's `rules` describe the meaning, each side implements it, and the bilateral contract test is what guarantees that the two implementations agree on that meaning. There is no domain package in shared code; there is the data in the `rules` block plus the bilateral test that keeps it true on both sides.

The adapter honors this in the orchestration: a two-sided node is only considered done after the bilateral contract test passes. As long as it does not pass, the two sides are not actually mirrored.

## Property and mutation: optional audit

Property tests (generating many inputs and checking invariants) and mutation tests (introducing defects and checking whether the suite catches them) are **audits of the suite**, not part of the node's fast build loop.

- They stay **outside the fast loop** `codegen -> plan -> execute -> verify -> review`. They do not decide whether a node is done day to day.
- They serve to audit the quality of the existing tests: property tests explore the input space beyond the written scenarios; mutation tests measure whether the scenarios and units would actually catch a regression.
- They are optional in v1 and do not enter `bpt.config.yaml`. Run them as a separate, periodic step, when you want extra confidence in the suite.

## Semantic review: the gate after green

Green is not done. After the scenarios, the units, and (for two-sided) the bilateral contract pass, the node still goes through the **semantic review** (`review`), which is a gate **after green**.

The semantic review asks what the tests cannot ask: does the implementation do what the spec meant, and not just what it literally checked? Is the import direction respected? Does the behavior honor the spirit of the `rules`? It runs as the last stage of the loop and can return findings, which come back as feedback for a new attempt (up to 3; the 3rd failure marks the node as `blocked` with the worktree preserved).

### It writes a report, not only a verdict

A diff of added and removed lines is unreadable past a certain size, and reading it is exactly the job being handed to a person. So `review` produces a document, and the verdict is a field on it:

- **One section per module the attempt changed**, not one section per file. Each says what that module now does and what changed about it in words, with the added and removed lines shown inside the context of that module rather than as one flat diff.
- **What it was asked for**, from the spec, next to what it got.
- **The verdict**, `status`, and any `findings`, which are what feed back into the next attempt.

The report goes in `artifacts` on the hook result, the same slot `verify` uses for its verification report. In `--mode yolo` the review still runs and still writes the report; it just stops gating, so the report is there to read afterwards instead of before.

This is one place where the loop and the reader want different things. The loop needs `status` and `findings` and nothing else. The person needs the prose. Producing only the first is how a review hook quietly becomes a checker that no one can learn anything from.

## How the verify hook consumes the scenarios

`verify` is the adapter hook that turns the spec into a verdict. It does not invent what to test: it **reads the scenarios from the `spec.md`** and runs the projection corresponding to the side it is running on.

The `verify` flow, per node and per side, keyed on (side, id):

1. Reads the `spec.md` of the contract linked to the node and extracts the scenarios from the Scenarios section.
2. Selects the side's projection: on the backend, those marked `[contract]`; on the frontend, those marked `[screen]`.
3. Runs the projection against that side's implementation. On the frontend, it resolves the targets via `ui_bindings` (surface to stable handle), which makes the verification deterministic.
4. Runs the node's unit tests for that side.
5. Checks the **import direction** (kernel enforcement): rejects `kernel -> behaviors/*` and `behaviors/a -> behaviors/b`; permits `behaviors/* -> kernel`, `behaviors/* -> contracts`, `kernel -> kernel`, and `kernel -> contracts`.
6. For a two-sided node, done only comes after the bilateral contract test also passes.

`verify` reports status through the adapter's neutral protocol: exit 0 means it ran (the verdict comes in the stdout JSON payload), exit other than 0 means the adapter itself broke. In the placeholder adapter, `verify` returns an empty ok status; a real stack adapter is what actually runs the projections, the units, and the import check.
