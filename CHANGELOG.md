# Changelog

BPT's promise to every clone is the schema string in `bpt.config.yaml`. This file records what that promise has meant over time, plus the changes to the convention, the formats and the validator.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The schema id (`bpt/v1`) moves independently of releases: it changes only when an existing, valid config would stop being valid.

## The schema contract

- **`bpt/v1`**: current. A config declares `schema`, `project`, `adapter`, `sides` (a map of side name to `root` and `kernel`), `contracts.root`, and `nodes` as a **list** of entries, each with `id`, `sides`, and optionally `deps`, `consumes`, `contract: none` and `prd`.
- Adding a new **optional** key keeps `bpt/v1`. Anything that invalidates a config that is valid today gets a new id, and the validator says so by name instead of failing on the first surprise.
- The validator refuses a schema it does not know. It will never silently guess.

## Unreleased

### Added
- `LICENSE` (MIT), so the clone-per-project premise is legally available.
- `CONTRIBUTING.md` for changing BPT itself, separate from the guide for using it.
- `CODE_OF_CONDUCT.md`, issue and pull request templates, `.editorconfig`.
- A CI workflow that runs the validator and asserts that every path quoted in the README and in `docs/` exists on disk, so the docs cannot drift away from the tree unnoticed.
- This changelog, and the schema contract stated above.

### Changed
- The README now opens with the problem BPT solves and who it is for, answers "why not just organize by feature", and shows the validator's real output.
- The contributing guide under `docs/` was renamed to `docs/ADDING-A-BEHAVIOR.md`, which is what it always was: a guide for the person using BPT, not for the person changing it. GitHub surfaces a file named CONTRIBUTING as a contributor guide, and that one was a user manual.
- `docs/CONTRACT-FORMAT.md`'s example is now a verbatim copy of the shipped `product.list` contract, and its field documentation matches it (`required: false`, boolean `retryable`, rules as `id` plus `describe`).
- `docs/NAMING.md`'s contract example is real, validatable syntax instead of pseudo-syntax.
- `docs/ADAPTER.md` points at `adapters/<name>/` where adapters actually live.

### Fixed
- `nodes` written as a mapping (the shape most people try first, and the shape three docs used to teach) now produces an explicit error that shows the list form, instead of an `AttributeError` traceback from the validator.
- The `nodes` examples in `docs/RULEBOOK.md` and `docs/ADDING-A-BEHAVIOR.md`, including the one-sided node and the per-side `deps` cases, now use the list form the validator accepts.
