---
cell: a-declaration
targets: bpt.config.yaml
question: what shape does a model reach for when it has to declare parts, dependencies and per-target presence
seeded_words_avoided: [behavior, side, kernel, wave, island, node, contract, surface, mirror, tree, parallel]
---
I am setting up a monorepo for a product. Several coding agents will work in it at the same
time, each one on a different part of the product, and each one should only have to read a
small slice of the repository rather than all of it.

I want a single file at the root of the repository that answers three questions: what the
parts are, which parts depend on which, and which of the applications in the monorepo each
part is present in.

Write that file. Choose the format and the field names yourself. Include a worked example with
three parts, where one part depends on another, and one part is present in only one of the
applications.

After the file, in no more than four sentences, say why you chose that format.

Write the complete file inline in your reply, inside a fenced code block.
