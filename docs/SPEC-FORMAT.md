# How to write a spec.md

The `spec.md` is a behavior's human document. It describes WHAT the behavior
does, for people and for the agent, in language that survives refactoring. The
`contract.yaml` (next to it) speaks to the machine; the `spec.md` speaks to the
intent. The two live together and hold for both sides of the mirror.

Golden rule, valid on every line of this document: the spec says WHAT, never
HOW. It does not name a function, a table, a component, a library, or an internal
route. If a passage only makes sense after choosing the stack, it does not
belong in the spec.

## Where the spec lives

There is ONE spec per behavior, next to the contract, never duplicated per
side:

```
packages/contracts/<path>/spec.md
packages/contracts/<path>/contract.yaml
```

The `<path>` comes from the behavior's id, replacing dots with slashes. The
behavior `product.list` has a two-segment id (`domain.action`) and becomes the
path `product/list`. So:

```
packages/contracts/product/list/spec.md
packages/contracts/product/list/contract.yaml
```

The behavior exists in both trees (`apps/backend/behaviors/product/list/`
and `apps/frontend/behaviors/product/list/`), but the spec and the contract live
only in `packages/contracts`. Backend and frontend read the same source of truth.
That is what keeps the mirror honest: one description, two implementations.

## Anatomy of the spec

The spec has two parts: the front-matter (structural metadata in YAML) and the
body (Markdown sections). The language convention follows BPT's rule: structure
keys are fixed BPT vocabulary (`id`, `title`, `surfaces`, `contract`, `consumes`,
`status`, `ui_bindings`); the domain vocabulary and the ids describe the product
(`product.list`, `search`, `/products`). Everything is written in English.

## The front-matter

The front-matter is a YAML block at the top of the file, delimited by `---`. It
declares the behavior's identity and how it appears on each surface.

Fields:

- `id`: the behavior's canonical id, in the form `domain.action`. Equal to the
  key in `bpt.config.yaml` and to the contract's `id`.
- `title`: a short, readable title.
- `surfaces`: a map from side to surface. Each side declares the surface `type`
  and its specific data. A screen declares a `route`; an endpoint does not need a
  public route. Surface types are an open vocabulary: `screen`, `cli-command`,
  `endpoint`, `job`, `event`.
- `contract`: the path of the contract this behavior fulfills (`product/list`).
  A one-sided behavior without a contract uses `contract: none`.
- `consumes`: the list of contracts this behavior reads from other behaviors.
  Empty (`[]`) when it does not depend on any external contract.
- `status`: a map from side to state. The states advance in this order:
  `draft` (only the spec exists), `ready` (spec finalized, ready to build),
  `built` (implemented), and `verified` (scenarios passed in verify). Each side
  walks at its own pace.
- `ui_bindings`: a neutral map from surface to a stable handle. It is the anchor
  point through which the screen test finds an element without depending on the
  component's internal name. It is still the WHAT (a target exists by that name),
  not the HOW.

## The body sections

After the front-matter comes the body, always in this order:

### Behavior

Two things in short prose: the action the behavior offers and the result the
user obtains. No internal steps, no mention of how the data is fetched.

### Rules

The observable business rules, as a list. Each rule has a short id and a
description. The same rules appear in the contract's `rules` block: there they
become data that each side implements, here they become text for the reader. A
rule never becomes shared code; the bilateral test is what keeps both sides
honest.

### Scenarios

The scenarios describe observable behavior in the given / when / then format.
The `then` is projected per surface: the same `given`/`when` can have a `then`
marked `[contract]` (what the backend guarantees) and another marked `[screen]`
(what the user sees). The backend verify runs the contract `then` clauses; the
frontend verify runs the screen ones.

A scenario tests behavior, not implementation: it never names a function or a
table, and it survives a complete internal refactor.

### Out of scope

What this behavior deliberately does not do. It serves to cut off assumptions
and keep the behavior from growing without an explicit decision.

## Guided example: product.list

Below is the real spec for `product.list`, field by field.

```markdown
---
id: product.list
title: List products
surfaces:
  frontend:
    type: screen
    route: /products
  backend:
    type: endpoint
contract: product/list
consumes: []
status:
  backend: draft
  frontend: draft
ui_bindings:
  frontend:
    search-field: product-search
    results-list: product-list
    total-label: product-total
---

# Behavior

The customer lists the available products and can filter by a search text.
The result comes paginated, with the total number of items found.

# Rules

- ordering: the items come sorted by name in ascending order.
- search-case-insensitive: the search ignores the difference between uppercase
  and lowercase.

# Scenarios

## Listing without search

- Given that available products exist
- When the customer opens the listing without providing a search
- Then [contract] returns the first page with up to 20 items, sorted by name
  ascending, and the total number of items
- Then [screen] the results list shows the products in name order and displays
  the total found

## Text search

- Given that products exist whose name contains "coffee" in any case
- When the customer types "COFFEE" in the search field
- Then [contract] returns only the items whose name matches the text, ignoring
  case
- Then [screen] the results list shows only the products that match the search

## Invalid parameter

- Given that the customer requests a page smaller than 1
- When the request arrives
- Then [contract] responds with the INVALID_PARAMETER error

# Out of scope

- Sorting by fields other than name.
- Detail of an individual product (that is product.detail).
- Real-time stock.
```

### Reading the example front-matter

- `id: product.list` and `title: List products`: the identity, identical to the
  key in the config and to the contract's id.
- `surfaces`: the behavior appears as a `screen` on the frontend, at the route
  `/products`, and as an `endpoint` on the backend. The same behavior, two
  surfaces.
- `contract: product/list`: points to
  `packages/contracts/product/list/contract.yaml`, which sits in the same directory.
- `consumes: []`: `product.list` does not read any contract from another behavior.
  (`product.detail`, by contrast, would have `product/list` here if it depended on
  its contract.)
- `status`: both sides start in `draft`. As the work moves along, each side climbs
  the ladder from `draft` to `ready` to `built` to `verified` at its own pace.
- `ui_bindings`: for the screen surface, the stable handles
  (`product-search`, `product-list`, `product-total`) let the screen test find the
  elements without knowing the name of the component that renders them.

### Reading the example body

- Behavior: two sentences. It states the action (list and filter) and the result
  (a page with a total). It does not say how the search happens.
- Rules: `ordering` and `search-case-insensitive` are the same two rules from the
  contract's `rules` block. The spec describes; the contract carries the data;
  each side implements; the bilateral test holds both accountable.
- Scenarios: each one separates `[contract]` from `[screen]`. Note that the
  invalid-parameter scenario has only `[contract]`, because the `INVALID_PARAMETER`
  error is a backend guarantee. No scenario mentions a function, a table, or a
  component.
- Out of scope: it cuts alternative sorting, product detail, and stock, so that
  nobody assumes those behaviors on their own.

## Checklist before marking ready

- The `id` in the front-matter matches `bpt.config.yaml` and the contract.
- Every side listed in `surfaces` has an entry in `status`.
- There is at least one scenario per active surface, with `[contract]` and `[screen]`
  where it makes sense.
- No line of the spec names a function, a table, a component, a library, or an
  internal route: only the WHAT.
- The spec's rules correspond to the contract's `rules` block.
- Out of scope is filled in with what was deliberately left out.
