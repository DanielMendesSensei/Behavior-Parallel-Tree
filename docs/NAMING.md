# Identity and Naming in BPT

This document defines how a behavior gets its name in the Behavior Parallel Tree. The `id` is the most important thing in the whole template: it is the identity that crosses both sides (backend and frontend), binds the contract, names the folder, and keys execution. Getting the `id` right means getting the behavior's boundary right, and drawing that boundary well is what keeps each behavior an isolated island of minimal context.

## Grammar of the id

An `id` has the form:

```
domain.action
```

Rules:

- All lowercase.
- The dot (`.`) separates segments.
- A single hyphen (`-`) appears only inside a compound segment (example: `invoice`).
- 2 to 3 segments. Prefer 2. Use 3 only when a real subdomain exists in the mental model (example: `payment.card.authorize`).
- The last segment is always the action (verb). The preceding segments form the domain.

Conceptual regex (the intent, not a strict parser):

```
^[a-z][a-z0-9-]*(\.[a-z][a-z0-9-]*){1,2}$
```

In other words: each segment starts with a letter, accepts letters, digits, and internal hyphens, and there are 2 to 3 segments joined by dots.

Valid examples:

```
product.list
product.detail
cart.review
payment.card.authorize
invoice.issue
```

Invalid examples:

```
list                   (missing the domain)
product                (missing the action)
Product.List           (uppercase)
product_list           (underscore instead of the dot)
product.list.items.paginated   (4 segments, wrong granularity)
```

### domain = noun from the user's mental model

The domain is the name of the thing as the user thinks of it, not as the database or the framework models it. Choose the noun that would come up in a conversation with someone who uses the product: `product`, `cart`, `order`, `payment`. Avoid technical implementation names (`table`, `service`, `repository`, `dto`) and avoid layer names (`api`, `controller`, `component`).

### action = verb

The action is always a verb, describing what the behavior does from the point of view of someone observing the result. One verb, one action.

Suggested list of verbs, as a guide and not a gate:

- `list`: returns a collection, usually paginated and filterable.
- `detail`: returns a complete item by identity.
- `create`: a new entity is born.
- `edit`: changes an existing entity.
- `cancel`: closes or invalidates something without deleting history.
- `pay`: closes a financial transaction from the payer's side.
- `authorize`: approves or denies an operation against a rule or provider.

This list exists to give consistency, not to limit. If the domain calls for a verb that is not here (`issue`, `archive`, `duplicate`, `review`), use the verb that describes the action honestly. The real gate is not the vocabulary: it is the four granularity tests below.

## Immutable id

Once an `id` exists (folder created, contract written, node in `bpt.config.yaml`), it is immutable. The `id` is the identity key that links backend, frontend, contract, spec, and execution: changing the string breaks all those bindings at once.

Renaming a behavior is not an edit, it is a migration. The rename procedure (moving folders on both sides, moving the contract and spec, updating `deps` and `consumes` of every node that points to it, updating the entry in `bpt.config.yaml`) is described in `MIGRATION.md`. Do not rename by hand, folder by folder.

## The 4 granularity tests

Before creating an `id`, run the behavior through the four tests. They decide whether you have one behavior or two disguised as one.

### 1. The "and" rule

If you need the word "and" to describe what the behavior does, it is probably two behaviors. "List products AND apply a coupon" is `product.list` plus something else. Break at the "and".

### 2. One verb, one id

The action has exactly one verb. If the natural description uses two verbs ("create and notify", "save and publish"), there are two `ids`. One of them may depend on the other via `deps`, but each verb has its own island.

### 3. One action, one main surface, one result

A behavior produces one observable result per surface. If the same action produces conceptually different results depending on a mode or flag, it is a sign that there is more than one behavior. A composite screen that reads several contracts does not violate this: it consumes N behaviors via `consumes`, it is not one giant behavior.

### 4. Context budget

The final test is BPT's very goal: an agent should be able to build this behavior, on both sides, loading only the node's folder, the contracts it consumes, and the kernel in read-only. If implementing the behavior requires holding half the system in your head, the boundary is too large. Shrink it until it fits within the context budget of an island.

## Language convention

BPT uses one language throughout, and the distinction below is about role, not idiom:

- **Structural schema keys are fixed BPT vocabulary.** They are BPT's own words, identical across every project: `kind`, `input`, `output`, `errors`, `sides`, `deps`, `consumes`, `rules`, `version`, `title`, `authorization`, `roles`, `surfaces`, `status`. They do not change with the domain.

- **Domain vocabulary and ids describe the product.** They are the product's words: `product.list`, `search`, `page`, `size`, `price`, `available`, `customer`. Error codes too: `INVALID_PARAMETER`, `UNAUTHORIZED`.

Both are written in English. The practical rule is only about which words come from BPT and which come from your product, not about mixing languages. An `id` always describes the business. A contract key always describes the BPT mechanism.

Example contract showing the boundary:

```
id product.list           # id: your product's word
kind query                # key: BPT's word
input:                    # key: BPT's word
  search text optional    # domain field: your product's word
  page integer default 1  # domain field: your product's word
errors:                   # key: BPT's word
  INVALID_PARAMETER ...    # domain code: your product's word
```

## Generic surfaces and sides as an open list

The `id` does not carry the surface. `product.list` is the same behavior whether it appears as a screen, an endpoint, or a command-line command. The surface is declared in the spec (`surfaces`), not in the name.

Surfaces are generic:

```
screen | cli-command | endpoint | job | event
```

And `sides` is an open list. The two sides the template ships knowing about are `backend` and `frontend`, but nothing in the core locks that pair. A command-line project could declare a node with `sides: [cli]`. A project with a worker could have a dedicated side. The mirror is N:M through the contract, not a rigid 1:1 between backend and frontend: what binds the sides is the shared identity (the `id`) and the neutral contract, not the number of sides.

The `id` remains the single identity, regardless of how many sides exist or which surface each side exposes.
