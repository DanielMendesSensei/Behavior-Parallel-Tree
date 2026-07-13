---
id: product.detail
title: Detail product
surfaces:
  frontend: { type: screen, route: /products/:productId }
  backend:  { type: endpoint }
contract: product/detail
consumes: [product.list]
status: { backend: draft, frontend: draft }
ui_bindings:
  product-detail: product-detail
  unavailable-notice: unavailable-notice
---

## Behavior
Action: the user clicks a product in the list. Result: they see the product detail page.

## Rules
- Shows name, description, price, and availability.
- An unavailable product appears with a notice and no purchase button.

## Scenarios (given / when / then, by surface)
- existing product: given a valid productId, when opening the screen,
  then [contract] output.id equals the requested one and [screen] shows name and price.
- missing product: given a productId that does not exist, when opening the screen,
  then [contract] error PRODUCT_NOT_FOUND and [screen] shows "product not found".
- unavailable product: given a product out of stock, when opening the screen,
  then [screen] shows an unavailable notice and does not show the purchase action.

## Out of scope
- List products (product.list).
- Add to cart (another behavior).
