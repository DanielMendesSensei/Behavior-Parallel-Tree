# packages/contracts

The neutral joint between the two behavior trees. This is where the agreement that links backend and frontend lives, without either side knowing the other's code.

## What lives here

A pair of files per behavior, at the path derived from the id (the dot becomes a slash, that is, `product.list` becomes `product/list`):

- `contract.yaml`: the neutral contract (kind, input, output, rules, errors, authorization). The source of truth for the interface.
- `spec.md`: the single specification of the behavior (only one, next to the contract, never duplicated per side).

Example:

```
packages/contracts/
  product/list/contract.yaml
  product/list/spec.md
  product/detail/contract.yaml
  product/detail/spec.md
```

## Joint rules

- **Nobody owns it.** The contract belongs to the boundary, not to one side. Backend and frontend implement against it.
- **The apps read, never write outside a contract PR.** Changing the interface is a deliberate, reviewed act, not a side effect of implementing one side.
- **One side never imports from the other.** The only bridge allowed is the contract. `apps/backend` and `apps/frontend` see each other only through here.
- **Shared business rules are data**, in the contract's `rules` block. Each side implements them; the bilateral test keeps both honest.

## Formats

- Contract format: see `docs/CONTRACT-FORMAT.md`.
- Spec format: see `docs/SPEC-FORMAT.md`.

## Future: `_flows/`

Flow tests (journeys that cross several behaviors) will live in `packages/contracts/_flows/<prd>/`, owned at the PRD level. Not part of v1 yet.
