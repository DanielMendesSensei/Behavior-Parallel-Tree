---
cell: extend
measures: whether the model writes the file's own type vocabulary or reverts to its prior
note: >-
  This is the sharpest near-miss test in the whole set. The model is handed a file
  written in a vocabulary and asked to add to it. If it writes `string` into a file
  whose every other field says `text`, the prior beat the document that was right in
  front of it, and that is what "the near-miss is worse than the novel" means in
  practice. Nothing in this prompt names a type.
---
Here is a contract file that describes one behaviour of a product:

```yaml
{contract}
```

Extend it with two things:

1. An optional input filter that keeps only products at or above a given price.
2. An output field on each product carrying the three letter code of the currency its price is
   in.

Change nothing else. Keep the file's existing conventions.

Write the complete new contents of the file inline in your reply, inside a single fenced yaml
code block. Write nothing after the code block.
