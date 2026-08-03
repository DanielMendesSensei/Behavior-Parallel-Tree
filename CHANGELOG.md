# Changelog

BPT's promise to every clone is the schema string in `bpt.config.yaml`. This file records what that promise has meant over time, plus the changes to the convention, the formats and the validator.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The schema id (`bpt/v1`) moves independently of releases: it changes only when an existing, valid config would stop being valid.

## The schema contract

- **`bpt/v1`**: current. A config declares `schema`, `project`, `adapter`, `sides` (a map of side name to `root` and `kernel`), `contracts.root`, and `nodes` as a **list** of entries, each with `id`, `sides`, and optionally `deps`, `consumes`, `contract: none` and `prd`.
- Adding a new **optional** key keeps `bpt/v1`. Anything that invalidates a config that is valid today gets a new id, and the validator says so by name instead of failing on the first surprise.
- The validator refuses a schema it does not know. It will never silently guess.

## Unreleased

### Added
- **`./bpt run`**, the runner, in the core. It walks the waves the validator derives, cuts a worktree per `(side, id)` on `bpt/<side>/<id>`, drives `codegen -> plan -> execute -> verify -> review` with up to 3 attempts, carries `findings` forward as `feedback` and `artifacts` forward as `prior_artifacts`, leaves a blocked unit's worktree in place, and writes `.bpt/last-run.json`. Flags: `--dry-run`, `--only`, `--jobs`, `--mode yolo`, `--kernel`, `--base`, `--attempts`, `--timeout`.
- `experiments/`: the measurements the README's hypothesis section asks for, pre-registered before each run.
- `LICENSE` (MIT), so the clone-per-project premise is legally available.
- `CONTRIBUTING.md` for changing BPT itself, separate from the guide for using it.
- `CODE_OF_CONDUCT.md`, issue and pull request templates, `.editorconfig`.
- `./bpt check`: the whole self-check in one command (the tree validates, the gate turns red on five refusal cases, and no doc cites a path that does not exist). CI runs the same command, so the working copy and CI cannot disagree about what green means.
- A CI workflow, kept to a single job that calls `./bpt check`.
- A statement of the hypothesis in the README: what BPT bets, what would confirm it, what would refute it, and which half of it ships here.
- This changelog, and the schema contract stated above.

### Changed
- **The neutral type vocabulary lost three invented words and kept one.** `text` is now `string`, `list` is now `array`, `decimal` is now `number`. The reason is measured and written into `docs/CONTRACT-FORMAT.md`: asked to design this file with no BPT in sight, ten runs out of ten reached for the standard words and zero produced the invented ones, so those three bought nothing. `money` stays, because the same experiment found that `type: money` produced an exact decimal type in five implementations out of five while `type: string` plus a rule saying the same thing in prose produced it in zero. Existing contracts using the old words are not rejected by anything, since the validator does not read types; they just no longer match the documented vocabulary.
- `docs/KERNEL.md` now states the kernel's price before its benefits: it is the only thing in everyone's context, so the budget for a change is node plus contracts plus kernel and never the node alone, and a kernel change costs a serialized wave.
- `docs/TESTING.md` says what the semantic review writes (a report per changed module, with the lines inside that module's context) and why the unit layer's deliberate testing of the how does not carry the usual cost: a unit test is scoped to one worktree and can never block another node, and its source of truth is the plan's per-module spec rather than the code the same agent just wrote.
- **The line between core and adapter moved to where the protocol already put it.** `docs/ADAPTER.md` used to hand orchestration to the adapter, while the same document said the core assembles an envelope carrying `attempt`, the previous attempt's `feedback`, `prior_artifacts`, and the unit's worktree and branch. None of those five can be read off the tree, the contract or the spec, and the adapter cannot hold them because it is invoked once per hook and keeps nothing in between. So the document contradicted itself, and the half that required a runner on this side was the correct half. What is yours to write is the six hooks, which are the only part that knows a language.
- `docs/ADAPTER.md` also stopped promising what it could not do. It said the placeholder existed "so you can watch the loop run end to end", and there was no loop. Now there is.
- `./bpt check` gained a fourth group: the runner closes the loop against a stub adapter, and refuses to close when the stub keeps failing.
- The README now opens with the problem BPT solves and who it is for, answers "why not just organize by feature", and shows the validator's real output.
- The contributing guide under `docs/` was renamed to `docs/ADDING-A-BEHAVIOR.md`, which is what it always was: a guide for the person using BPT, not for the person changing it. GitHub surfaces a file named CONTRIBUTING as a contributor guide, and that one was a user manual.
- `docs/CONTRACT-FORMAT.md`'s example is now a verbatim copy of the shipped `product.list` contract, and its field documentation matches it (`required: false`, boolean `retryable`, rules as `id` plus `describe`).
- `docs/NAMING.md`'s contract example is real, validatable syntax instead of pseudo-syntax.
- `docs/ADAPTER.md` points at `adapters/<name>/` where adapters actually live.

### Fixed
- `nodes` written as a mapping (the shape most people try first, and the shape three docs used to teach) now produces an explicit error that shows the list form, instead of an `AttributeError` traceback from the validator.
- The `nodes` examples in `docs/RULEBOOK.md` and `docs/ADDING-A-BEHAVIOR.md`, including the one-sided node and the per-side `deps` cases, now use the list form the validator accepts.
