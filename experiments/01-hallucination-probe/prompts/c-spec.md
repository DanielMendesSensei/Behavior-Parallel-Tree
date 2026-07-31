---
cell: c-spec
targets: packages/contracts/<path>/spec.md
question: does the model reach for Gherkin, for prose, or for something else when one specification must verify two implementations
seeded_words_avoided: [spec, scenario format, behavior, side, surface, given/when/then, mirror]
---
For the same "list products" functionality, I need a second file, sitting next to the first
one: the written specification of what is observable from the outside, with cases that a test
can check.

There is one server implementation and one client implementation, and both have to be
verified against this single file. There must not be one copy per implementation.

Write that file. Choose the format yourself.

After the file, in no more than four sentences, say why you chose that format.

Write the complete file inline in your reply, inside a fenced code block.
