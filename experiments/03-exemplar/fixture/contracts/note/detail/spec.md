---
id: note.detail
title: Read one note
surfaces:
  backend: { type: endpoint }
contract: note/detail
consumes: []
---

## Behavior

A signed in member asks for one note by its id and gets the note with the names
of the tags on it.

## Rules

- The tag names come back ordered by name ascending. A note with no tags gets an
  empty list, not an error.
- An archived note is still readable. It comes back with `archived` true.
- The output carries the contract's fields and nothing else.

## Scenarios

- reads a note: given a note that exists, then its id, title, body and archived
  flag come back, with the names of its tags.
- tags come ordered: given a note whose tags were attached out of order, then the
  names come back sorted ascending.
- no tags: given a note with no tags, then `tags` is an empty list.
- archived is readable: given an archived note, then it still comes back, with
  `archived` true.
- unknown id: given an id no note has, then the call fails with NOT_FOUND.
- empty id: given an empty note_id, then the call fails with INVALID_PARAMETER.
- no session: given no session, then the call fails with UNAUTHORIZED, and it
  fails before the id is looked at.
