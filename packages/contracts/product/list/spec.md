---
id: product.list
title: List products
surfaces:
  frontend: { type: screen, route: /products }
  backend:  { type: endpoint }
contract: product/list
consumes: []
status: { backend: draft, frontend: draft }   # draft -> ready -> built -> verified, per side
# UI binding: neutral surface -> stable handle map (the frontend verify uses it)
ui_bindings:
  product-list: product-list
  empty-state: empty-state
---

## Behavior
Action: the user opens /products. Result: they see the paginated list of available products.

## Rules
- Available products only, ordered by name ascending.
- Search by name, case insensitive.
- Default page size 20, cap 100.

## Scenarios (given / when / then, by surface)
- catalog with items: given available products, when opening /products,
  then [contract] output.total > 0 and [screen] shows the first page.
- empty catalog: given no products, when opening /products,
  then [screen] shows the empty state and does not show pagination.
- invalid parameter: given size 500, when loading,
  then [contract] error INVALID_PARAMETER and [screen] shows "could not load".

## Out of scope
- Create, edit, delete a product (other behaviors).
- Detail a product (product.detail).
