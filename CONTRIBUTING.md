# Contributing to BPT

This file is about changing **BPT itself**: the convention, the formats, the validator, the docs. If you are using BPT in your own project and want to add a behavior, you want [docs/ADDING-A-BEHAVIOR.md](./docs/ADDING-A-BEHAVIOR.md) instead.

## Running the checks

Everything BPT needs to check itself is Python 3 with PyYAML. That is tooling, not the stack of the app you build with it.

```bash
pip install pyyaml
./bpt check
```

That is the whole gate, and it is the same command CI runs. It covers three
things: the tree validates, the gate turns red when an invariant breaks (the
checker is fed configs it must refuse, because a validator that never fails
proves nothing), and no doc cites a repository path that does not exist.

If you add an invariant, add its refusal case to `MUST_REFUSE` in
`tools/bpt/check.py`. A check with no failing case is a check nobody can trust.

## What a change to BPT has to hold

- **The core stays stack-agnostic.** Nothing in `tools/bpt/` or in `bpt.config.yaml` may mention a language, a framework, a package manager or a vendor. If a change needs that knowledge, it belongs in an adapter.
- **The docs and the tree agree.** Every path a doc cites must exist, and every example a doc shows must be the shape the validator accepts. The example contract in `docs/CONTRACT-FORMAT.md` is a verbatim copy of `packages/contracts/product/list/contract.yaml` for exactly this reason: if you change one, change the other.
- **The two example nodes keep working.** `product.list` and `product.detail` are the teaching material. A change that breaks them breaks the first thing a newcomer reads.
- **English throughout**, per `docs/RULEBOOK.md`: structural keys are BPT vocabulary, domain words belong to the project using it.
- **A new invariant comes with its failure case.** If you add a check to the validator, show a config that trips it and the message a person reads when it does.

## Commits

Conventional Commits, scoped by area: `feat(validate):`, `fix(adapter):`, `docs(rulebook):`, `chore:`. Write the body for someone who was not in your head: what changed, and what would break if it were wrong.

## Proposing a change to the schema

`bpt/v1` in `bpt.config.yaml` is the one promise this template makes to every clone. Changing what that string means breaks other people's repositories silently, so a schema change needs, in the pull request:

1. what the new schema accepts that the old did not, or refuses that it used to accept;
2. what a clone on the old schema sees when it runs the new validator;
3. an entry in `CHANGELOG.md`.

Additive changes (a new optional key) do not need a new schema id. Anything that invalidates an existing config does.

## Adapters

An adapter lives in `adapters/<name>/` and honors the protocol in [docs/ADAPTER.md](./docs/ADAPTER.md): one JSON on stdin, one JSON on stdout, logs on stderr, exit 0 when it ran (with the business status in the payload). Adapters for real stacks are welcome as separate repositories or as directories here, as long as `adapters/placeholder/` stays the minimal reference that depends on nothing.

## Reporting

Three kinds of report, and they are different: the architecture is unclear (a docs issue), the validator is wrong (a bug), or your adapter needs something the protocol does not give (a protocol proposal). Say which one it is and the rest of the conversation goes faster.
