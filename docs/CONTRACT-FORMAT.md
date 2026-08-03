# Neutral Contract Format

The contract is BPT's joint. It is the single point where backend and frontend meet, and it does so without either side needing to know the other's code. A two-sided behavior exists on both sides with the same identity and the same spec; what binds the two is this neutral YAML file.

The golden rule: the contract describes **what** the behavior accepts and returns, never **how** a side implements it. No language type, no route, no HTTP verb.

## Where it lives

One contract per behavior, at the canonical path derived from the id (dot becomes slash):

```
packages/contracts/<path>/contract.yaml
packages/contracts/<path>/spec.md
```

Example for `product.list`:

```
packages/contracts/product/list/contract.yaml
packages/contracts/product/list/spec.md
```

The contract lives **outside** `apps/backend` and `apps/frontend`, in `packages/contracts`. The spec sits next to the contract, a single one, never duplicated per side. The contracts root is declared in `bpt.config.yaml`:

```yaml
contracts:
  root: packages/contracts
```

## Ownership

Nobody owns the contract in the sense that one side could change it for convenience. The ownership rules:

- **Nobody owns it unilaterally.** The contract lives outside the apps precisely so it belongs to none of them.
- **The apps read, never write outside a contract PR.** Backend and frontend consume the contract as the source of truth. Changing the contract is a deliberate change, reviewed in its own contract PR, not a side effect of touching one side's code.
- **One side never imports from the other.** Backend does not import from frontend and vice versa. All communication between sides goes through the contract.
- **On conflict, the contract decides.** If a side's implementation diverges from the contract, the implementation is what is wrong. The contract is the arbiter; the code adjusts to it, never the other way around within the same PR.

## Neutral types

The `input` and `output` fields use only neutral types, with no tie to a stack:

| Type | Meaning |
|------|---------|
| `string` | Free text. |
| `integer` | Whole number. |
| `number` | Number with decimal places (not monetary). |
| `boolean` | True or false. |
| `array` | Ordered collection (`array of <type>`). |
| `object` | Structure with named fields. |
| `money` | Monetary value: an exact amount that must not be held in binary floating point. |

Six of those seven are the words every schema language already uses. That is on
purpose, and it is measured rather than assumed: in `experiments/`, ten clean
runs asked a model to design this exact file with no BPT in sight, and it reached
for `string`, `integer`, `number`, `boolean`, `object` and `array` every time.
BPT used to say `text`, `decimal` and `list` instead. Those three appeared zero
times in ten runs, so they were three words of friction buying nothing, and they
are gone.

`money` stays, and it is the one exception worth defending. It has no equivalent
in the standard vocabulary: `string` and `number` both describe a shape, and what
matters about an amount is a rule about precision. The same experiment measured
the difference. Given a contract saying `type: money`, five implementations out
of five reached for an exact decimal type. Given `type: string` plus a written
rule saying the value must never touch binary floating point, zero out of five
did, and all five returned a plain string. The rule was there, in the same words,
in both arms. The type carried the meaning into the code and the prose did not.

### Why no language type, route, or HTTP verb

- **A language type** (`String`, `BigDecimal`, `Int32`, `Optional<T>`) would tie the contract to a stack. The contract must be read equally by any adapter, in any runtime.
- **A route** (`/products`, `/api/v2/...`) is a surface detail. A route lives in the spec, in the `surfaces` block, because it is **how** the frontend or the backend exposes the behavior, not **what** it does.
- **An HTTP verb** (`GET`, `POST`) assumes HTTP transport. The same behavior could be exposed as an endpoint, a CLI command, a job, or an event. The contract uses `kind` (`query` or `command`) to capture the intent neutrally, leaving the transport to the adapter.

## Contract fields

| Field | Required | Description |
|-------|----------|-------------|
| `id` | yes | Canonical identity `domain.action`. Same on both sides. |
| `version` | yes | Integer (see Versioning). |
| `kind` | yes | `query` (reads, does not change state) or `command` (changes state). |
| `title` | yes | Short human title. |
| `authorization` | yes | `required` (boolean) and `roles` (list of domain roles). |
| `input` | yes | Input fields, each with a neutral type and constraints (`min`, `max`, `default`, `required`). A field is required unless it says `required: false`. |
| `output` | yes | Shape of the result, with nested neutral types. |
| `rules` | yes | Business rules as data (see below). |
| `errors` | yes | List of possible errors. |

### Errors

Each error has four attributes:

- `code`: an uppercase identifier (`INVALID_PARAMETER`, `UNAUTHORIZED`).
- `category`: the error class (`user`, `validation`, `system`).
- `retryable`: boolean, whether it is worth trying again.
- `when`: the condition that triggers the error (described in the spec when it needs detail).

## Shared business rules as DATA

There is no shared domain package in code. A rule that holds for both sides lives in the contract's `rules` block, as **data**, with an id and a neutral description:

```yaml
rules:
  - id: ordering
    describe: items ordered by name ascending
  - id: search-case-insensitive
    describe: search by name ignores case
```

Each side implements the rule in its own code. The honesty of both is guaranteed by the bilateral, consumer-driven contract test: the scenario lives in the spec and runs on each surface during `verify`. The rule is single (the data in the contract), but it has two implementations that must agree.

A shared rule **never** becomes kernel code. The kernel is cross-cutting infra; a business rule is data in the contract.

## Lean versioning in v1

- `version` is an **integer**, not semver.
- An **additive** change (a new optional input field, a new output field, a new error) does **not** bump the version. Old consumers stay valid.
- A **breaking** change (removing or renaming a field, making required what was optional, changing a type, changing meaning) **bumps** the version.

Full semver, N and N-1 coexistence, and expand/contract are for the future. In v1 the distinction is binary: additive holds, breaking bumps.

## Drift detection in v1

In v1, drift detection is simple and checked by the validator: the **file trio exists**.

- `contract.yaml` present.
- `spec.md` present next to it.
- The behavior folder exists on each side declared in `sides`.

A two-sided node needs a contract; a one-sided node declares `contract: none`. A canonical hash, a central registry, and N/N-1 negotiation are future work, not v1.

## Language convention

- **Structural schema keys are fixed BPT vocabulary**: `id`, `version`, `kind`, `title`, `authorization`, `input`, `output`, `rules`, `errors`, `code`, `category`, `retryable`.
- **Domain vocabulary and ids describe the product**: `product.list`, `search`, `price`, `available`, `INVALID_PARAMETER`, `UNAUTHORIZED`, roles like `customer`.

Everything is written in English. The structure is universal; the domain belongs to the project.

## Real example: product.list

`packages/contracts/product/list/contract.yaml`:

```yaml
# Neutral contract for product.list (the joint between backend and frontend).
# Pure data, neutral types. No language type, route, or HTTP verb.
# Structural keys and domain vocabulary are both English.
id: product.list
version: 1                 # simple integer in v1 (semver/hash: future)
kind: query                # query | command  (event/stream: future)
title: List products

authorization:
  required: true
  roles: [customer]

input:
  search: { type: string, required: false }
  page:   { type: integer, min: 1, default: 1 }
  size:   { type: integer, min: 1, max: 100, default: 20 }

output:
  items:
    type: array
    of:
      object:
        id:        { type: string }
        name:      { type: string }
        price:     { type: money }
        available: { type: boolean }
  total: { type: integer }
  page:  { type: integer }

# Shared business rules live here as DATA. Each side implements them
# from here; the bilateral contract test keeps both sides honest.
rules:
  - id: ordering
    describe: items ordered by name ascending
  - id: search-case-insensitive
    describe: search by name ignores case

errors:
  - code: INVALID_PARAMETER
    category: validation   # user | validation | system
    retryable: false
    when: page or size out of range
  - code: UNAUTHORIZED
    category: user
    retryable: false
    when: session missing or expired
```

Notice what is **not** here: no language type, no `/products` route, no HTTP verb. The route and the surface type live in the spec, in the `surfaces` block. The contract only says what `product.list` accepts, what it returns, which rules hold for both sides, and how it can fail.
