---
id: product.list
title: List products
surfaces:
  backend: { type: endpoint }
contract: product/list
consumes: []
---

## Behavior

A signed in customer asks for the product catalogue and gets one page of it.

## Rules

- Only available products are returned. An unavailable product is not in the page and is not
  counted.
- Results are ordered by name, ascending.
- Search matches the product name and ignores case. A search that matches nothing returns an
  empty page, not an error.
- `page` defaults to 1 and `size` defaults to 20 when the caller does not supply them.
- `total` is how many products the filters match in the whole catalogue, not how many are on
  the returned page.
- `page` in the output is the page that was served.
- The price of a product is an exact monetary amount. Whatever the implementation returns for
  it must carry the same value it came in with, to the cent.

## Scenarios

- default page: given the catalogue, when listing with no arguments, then the first twenty
  products by name come back, `page` is 1, and `total` counts every available product.
- empty catalogue: given no products, then the page is empty and `total` is 0.
- second page: given the catalogue, when asking for page 2 at the default size, then the
  remaining products come back in order.
- case insensitive search: given a product named "Zebra Lamp", when searching for "zebra",
  then that product comes back and `total` is 1.
- unavailable excluded: given three unavailable products, then none of them appears and none
  of them is counted.
- size out of range: given `size` of 500, then the call fails with INVALID_PARAMETER.
- page out of range: given `page` of 0, then the call fails with INVALID_PARAMETER.
- no session: given no session, then the call fails with UNAUTHORIZED, and it fails before any
  parameter is looked at.
- exact price: given a product priced 1099.95, then the returned price still reads 1099.95.
- no extra fields: the output carries the contract's fields and nothing else.

## Out of scope

- Creating, editing or deleting a product.
- The detail view of a single product.
