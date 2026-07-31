---
cell: b-contract
targets: packages/contracts/<path>/contract.yaml
question: does the model reach for JSON Schema or OpenAPI when asked for a transport neutral machine readable interface description
seeded_words_avoided: [contract, neutral, behavior, side, kernel, node, surface, query, command]
---
I need a single file that describes one piece of product functionality: what it accepts as
input, what it returns, and the ways it can fail.

The same description has to hold whether that functionality is reached over HTTP, run as a
terminal command, or executed as a background job, so it must not assume any particular
transport. It also has to be machine readable, because code generators for more than one
programming language will read it.

Write that file for this functionality: list products, paginated, with an optional search by
name, where the caller must be signed in.

Choose the format and the field names yourself.

After the file, in no more than four sentences, say why you chose that format.
