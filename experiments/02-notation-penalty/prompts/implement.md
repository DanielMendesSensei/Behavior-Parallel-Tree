---
cell: implement
measures: first attempt pass rate, tokens, and whether the notation changes the code
---
You are implementing one behaviour of a backend, in Python 3, from its contract and its
specification.

Here is the contract:

```yaml
{contract}
```

Here is the specification:

```markdown
{spec}
```

The code lives in a directory that already contains these files, which you must not change:

`_support.py`

```python
{support}
```

`products.py` is the only file you write. Its current contents are:

```python
{stub}
```

Implement `list_products` so that it satisfies the contract and the specification. Use the
Python standard library only. Raise `ProductError` with the contract's error code for every
error the contract declares.

Write the complete new contents of `products.py` inline in your reply, inside a single fenced
python code block. Write nothing after the code block.
