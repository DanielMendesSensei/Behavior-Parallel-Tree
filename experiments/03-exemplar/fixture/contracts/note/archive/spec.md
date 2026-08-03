---
id: note.archive
title: Archive a note
surfaces:
  backend: { type: endpoint }
contract: note/archive
consumes: []
---

## Behavior

A signed in member archives one note. The note stops being live and comes back
with its archived flag set.

## Rules

- Archiving a note that is already archived is an error, not a no-op.
- The change is written through the store, so a later read sees it.
- The output carries the contract's fields and nothing else.

## Scenarios

- archives a live note: given a live note, then it comes back with `archived`
  true.
- the change persists: given a live note, when it is archived, then reading the
  store again shows it archived.
- already archived: given a note that is archived, then the call fails with
  ALREADY_ARCHIVED and the store is untouched.
- unknown id: given an id no note has, then the call fails with NOT_FOUND.
- empty id: given an empty note_id, then the call fails with INVALID_PARAMETER.
- no session: given no session, then the call fails with UNAUTHORIZED, and it
  fails before the id is looked at.
