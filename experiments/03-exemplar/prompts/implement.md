---
cell: one per target behaviour
measures: whether a finished sibling in context changes what gets written
note: >-
  Identical in both arms except for the {exemplar} block, which is empty in arm A
  and holds a finished behaviour in arm B. Nothing else moves: same contract, same
  spec, same kernel, same file rules.
---
You are implementing one behaviour of a backend, in Python 3, from its contract
and its specification.

Here is the contract:

```yaml
{contract}
```

Here is the specification:

```markdown
{spec}
```

Here is the kernel. It is read only: you import from it and you never change it.

```python
{kernel}
```

{exemplar}

Write the complete contents of `behavior.py`. The rules of that file:

- Python standard library only, plus what you import from the kernel.
- Expose exactly one public function. Everything else in the module must start
  with an underscore.
- That function takes `store` and `session` first, then the contract's input
  fields in the order the contract lists them, each defaulting to None.
- Raise the kernel's `AppError` with the contract's error code for every error
  the contract declares.

Write the complete file inline in your reply, inside a single fenced python code
block. Write nothing after the code block.
