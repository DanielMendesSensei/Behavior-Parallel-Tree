Here is another behaviour of this same codebase, already finished and reviewed.
It is `note.list`. Read it before you write yours.

Its contract:

```yaml
id: note.list
version: 1
kind: query
title: List notes
authorization:
  required: true
  roles: [member]
input:
  search: { type: string, required: false }
  page:   { type: integer, min: 1, default: 1 }
  size:   { type: integer, min: 1, max: 50, default: 10 }
output:
  items:
    type: array
    of:
      object:
        id:       { type: string }
        title:    { type: string }
        archived: { type: boolean }
  total: { type: integer }
  page:  { type: integer }
rules:
  - id: ordering
    describe: notes ordered by title ascending
  - id: search-case-insensitive
    describe: search matches the title and ignores case
  - id: archived-excluded
    describe: archived notes are not returned and not counted
errors:
  - code: INVALID_PARAMETER
    category: validation
    retryable: false
    when: page or size out of range
  - code: UNAUTHORIZED
    category: user
    retryable: false
    when: session missing
```

Its implementation, the complete contents of its `behavior.py`:

```python
"""note.list: one page of the member's notes, ordered by title.

The contract is packages/contracts/note/list/contract.yaml. Everything this
behaviour needs lives in this file or in the kernel.
"""
from kernel import AppError, require_session

DEFAULT_PAGE = 1
DEFAULT_SIZE = 10
MAX_SIZE = 50


def _validated_input(search, page, size):
    """Apply the contract's defaults and refuse what it puts out of range."""
    page = DEFAULT_PAGE if page is None else page
    size = DEFAULT_SIZE if size is None else size
    if not isinstance(page, int) or page < 1:
        raise AppError("INVALID_PARAMETER")
    if not isinstance(size, int) or size < 1 or size > MAX_SIZE:
        raise AppError("INVALID_PARAMETER")
    return search, page, size


def _matching(store, search):
    """The rows the contract's rules keep: not archived, matching the search."""
    rows = [n for n in store.notes() if not n["archived"]]
    if search:
        needle = search.casefold()
        rows = [n for n in rows if needle in n["title"].casefold()]
    return sorted(rows, key=lambda n: n["title"])


def list_notes(store, session, search=None, page=None, size=None):
    """Return the contract's output for one page of notes."""
    require_session(session)
    search, page, size = _validated_input(search, page, size)

    rows = _matching(store, search)
    start = (page - 1) * size
    return {
        "items": [
            {"id": n["id"], "title": n["title"], "archived": n["archived"]}
            for n in rows[start:start + size]
        ],
        "total": len(rows),
        "page": page,
    }
```
