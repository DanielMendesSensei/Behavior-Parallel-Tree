---
id: tag.list
title: List tags with their note count
surfaces:
  backend: { type: endpoint }
contract: tag/list
consumes: []
---

## Behavior

A signed in member asks for the tags and gets each one with how many live notes
carry it.

## Rules

- Tags come ordered by name ascending.
- The count of a tag counts only notes that are not archived.
- A tag is kept when its count is greater than or equal to `min_count`. With the
  default of 0, every tag comes back, including the ones no note carries.
- `total` is how many tags the filter kept.
- The output carries the contract's fields and nothing else.

## Scenarios

- every tag by default: given the tags, when listing with no arguments, then all
  of them come back ordered by name, each with its count.
- archived notes do not count: given a tag carried only by archived notes, then
  its count is 0.
- min_count filters: given min_count of 2, then only tags with two or more live
  notes come back, and `total` matches.
- a tag nobody uses: given a tag on no note, then it still comes back with count
  0 when min_count is 0.
- negative min_count: given min_count of -1, then the call fails with
  INVALID_PARAMETER.
- no session: given no session, then the call fails with UNAUTHORIZED, and it
  fails before min_count is looked at.
