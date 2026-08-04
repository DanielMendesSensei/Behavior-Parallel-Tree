# Experiments

The root README states a hypothesis, names what would confirm it, names what would refute it,
and admits that this repository does not measure any of it. This directory is that
measurement.

**This file is the pre-registration.** It is committed before the first run. The decision
criteria below are fixed in advance, on purpose: whoever runs these experiments already has a
favourite hypothesis, and a favourite hypothesis contaminates the reading of a result. If a
criterion turns out to be badly chosen, the honest move is to say so in `RESULTS.md` and
re-run, not to reinterpret the number that came out.

## What is being tested, and why these three

BPT rests on claims about how a language model behaves. Three of those claims can be measured
cheaply, and each one decides a different part of the design.

| Experiment | Question | What it decides |
| --- | --- | --- |
| 01 hallucination probe | What shape does a model produce on its own for the problem BPT solves? | Whether BPT's notation sits inside or outside the distribution, and which parts specifically |
| 02 notation penalty | Does the same contract, written in `bpt/v1` and in JSON Schema, produce the same code? | Whether the bespoke contract format pays for itself |
| 03 island with and without an exemplar | Does one reference node in context improve the result enough to pay for the tokens it costs? | Whether the pure island rule stays, or gains a mandatory exemplar |

Experiment 01 is a design method borrowed from the talk that produced BPT: let the model
produce the artifact that does not exist yet, and read its expectation as a measurement of the
distribution. Experiment 02 is the same talk's "invent a small variation of a known language
and watch performance collapse" claim, pointed at BPT's own file formats. Experiment 03 tests
an internal contradiction in BPT: the island rule hides sibling implementations from the
agent, and a model learns from examples in context.

## Rules that apply to all three

1. **Pre-registration.** These criteria are committed before the first line lands in any
   `runs/` directory. `git log` proves the order.
2. **The prompt describes the problem, never the solution.** Experiment 01 is void if the
   prompt seeds the vocabulary under test. No "contract", no "behavior", no "side", no
   "kernel", no "wave", no "island", no "node".
3. **Baseline variance before any comparison.** For 02 and 03, run one cell twice with
   everything identical and record the spread. Without that number there is no way to tell a
   real difference between arms from noise. This is the step most people skip and the one that
   invalidates the most results. For 01 the within-cell spread is not a control, it is the
   finding: an unstable spontaneous form is itself evidence that the problem has no canonical
   shape in the distribution.
4. **Clean session per run.** `--safe-mode` (no CLAUDE.md, no skills, no hooks, no MCP, no
   plugins), `--tools ""`, `--strict-mcp-config`, `--no-session-persistence`, and a fresh empty
   working directory. The runner records the exact command with every run.
5. **N = 5 per cell.** This detects a large effect and nothing smaller. That is the right
   trade: an effect too small for N=5 to see is too small to justify rewriting an
   architecture.
6. **Model and date on every record.** A result here has a shelf life, because the
   distribution changes with every new model. "Models are bad at frontend" was true and then
   stopped being true. Re-running the probe against a new model is the intended use, not an
   exception.
7. **English for all prompts and artifacts.** BPT is written in English and the mass of the
   code distribution is in English. Mixing languages would add a variable nobody is trying to
   measure.
8. **Contamination check.** This repository is three weeks old, so it is almost certainly not
   in any training set. Confirm it anyway: ask each model, in a clean session, whether it knows
   "Behavior Parallel Tree", and record the answer in `RESULTS.md`.

### The limitation that was underestimated, and what it cost

This section originally said that keeping the default agentic system prompt was a mild
contaminant, constant across cells, and therefore harmless. That was wrong, and the first 14
runs are what proved it. They are kept, voided, in `01-hallucination-probe/runs-void-r1/`.

The agentic prompt tells the model it is working in a repository with tools. So instead of
answering the question, it tried to create the file, reached for the disabled Write tool, and
stopped. Four of five Sonnet runs and one of five Opus runs came back with no artifact at all,
just an intention to write one. A contaminant that silently deletes runs, and deletes more of
one model's runs than the other's, is not a constant: it biases the surviving sample.

Revision 2 removes the cause. A neutral system prompt replaces the agentic one, and each
prompt asks for the file inline. Neither change mentions a format or a field name, so the
probe still measures the thing it was built to measure. The isolation itself was checked
rather than assumed: every record carries `num_turns` and the contents of its working
directory, and across all 14 voided runs the turn count was 1 and the directory stayed empty,
which is how we know nothing executed.

The general lesson goes in `RESULTS.md` too, because it is the more useful finding: an
experiment whose failure mode is an empty answer will quietly shrink its own sample, and only
reading the raw output catches it. The summary table looked perfectly healthy.

`codex` is not installed on this machine, so the cross-family axis of experiment 01 runs
against two Claude models instead of two vendors. The runner takes an arbitrary command
template, so adding a second vendor later is a config change, not a rewrite. Until that
happens, `RESULTS.md` must not claim a cross-vendor finding.

## Experiment 01: hallucination probe

Three prompts, in `01-hallucination-probe/prompts/`. Each describes a problem BPT solves,
using none of BPT's words, and asks the model to pick the format and the field names itself.

5 runs per prompt per model, 2 models, 30 outputs.

Scored against `01-hallucination-probe/rubric.yaml`, which is fixed before the first run and
lists: the standards a model might reach for on its own (JSON Schema, OpenAPI, TypeSpec,
protobuf, GraphQL, Gherkin, AsyncAPI, Nx, Turborepo, and others), the BPT keys that might
appear spontaneously, the type vocabulary, and the `required` convention.

The headline metric runs in two directions. Of the fields BPT defines, how many appear on
their own. Of the fields the model produces, how many BPT does not have.

**Decision criteria, fixed in advance:**

- The contract prompt yields JSON Schema or OpenAPI in more than 60% of runs: BPT's contract
  notation is a tax, and experiment 02 becomes a confirmation rather than a discovery.
- The declaration prompt yields, unprompted, an envelope carrying an identity, a dependency
  list, and a per-target list: that part of `bpt.config.yaml` is inside the distribution and
  stays exactly as it is.
- No stable pattern across runs: the problem has no canonical shape in the distribution, the
  cost of inventing one is lower than this repository's own audit assumed, and BPT's notation
  is not the liability it looks like.

## Experiment 02: notation penalty

Three real contracts of comparable size, in two semantically identical versions:

- arm A: `contract.yaml` in `bpt/v1`, unchanged
- arm B: the same envelope (`id`, `kind`, `deps`, `rules`, `errors`) with `input` and `output`
  rewritten as plain JSON Schema

Same task in both arms: implement the server side from the contract, in a fixed clean
scaffold. Randomised order, 5 runs per cell, plus the baseline variance cell.

Measured: first-attempt success (the spec scenario passes with no human intervention), the
count of near-miss errors (writing `string` where the contract says `text`, treating
`required` as an object-level list where BPT puts it per field, inventing an HTTP verb,
inventing `$ref`), tokens spent before the first code that runs, and how often the model
invents a field the contract does not have.

The JSON Schema version tends to be longer. That is recorded as a covariate, not corrected
away, because context is the resource under dispute.

**Decision criteria, fixed in advance:**

- Arm B wins on first-attempt success and spends fewer tokens overall: the contract notation
  is replaced.
- The two arms sit inside the baseline variance: `bpt/v1` stays, because transport neutrality
  is worth something and in that case it cost nothing.
- Arm A wins: the near-miss claim is refuted for contracts. That goes in the root README,
  because it is a counter-intuitive result and it is exactly the kind of thing BPT should be
  claiming.

## Experiment 03: island with and without an exemplar

This is the only experiment here that tests a **principle** of BPT rather than a notation.
The island rule says a behavior never reads another behavior. A model learns from examples in
its context. Those two pull against each other, and nothing in experiments 01 or 02 touched it.

**The fixture.** A small codebase of its own, in `03-exemplar/fixture/`, rather than this
repository's `apps/`, so that the template keeps shipping empty and the experiment stays
reproducible by anyone who clones it. It has one kernel (`AppError`, `require_session`, a
`Store`), one finished and reviewed behavior used as the exemplar (`note.list`, contract plus
implementation), and three targets that exist only as a contract and a spec: `note.detail`,
`tag.list`, `note.archive`.

**The arms.** Identical in everything except one block of the prompt.

- **arm A, pure island:** the contract, the spec, and the kernel read-only. Exactly what BPT's
  context budget allows.
- **arm B, island plus exemplar:** the same, plus the finished `note.list` in full.

Three targets, five runs per arm per target, 30 runs, one model.

**What is measured.**

- **first-attempt success**: the target's scenarios run against what came back. Byte identical
  in both arms, behavior only, never looking at the notation. Each suite was proved both ways
  before the first run: green against a reference implementation, red against a stub.
- **structural consistency**: the ten items in `03-exemplar/checklist.md`, scored over the
  items that apply.
- **tokens**: the exemplar costs context, so any gain has to cover what it spends.

**One model, and no fishing.** Sonnet, for the same reason as experiment 02 and with the same
ban: if the gap between arms falls inside the within-arm spread, the answer is "could not
measure", and the other model does not get added afterwards to hunt for a difference.

**Decision criteria, fixed in advance:**

- **Arm B wins on consistency and on first-attempt success**, by more than the within-arm
  spread, and the win covers the exemplar's token cost: the exemplar joins the context budget
  as a rule, and `docs/RULEBOOK.md` principle 5 gains a sentence saying an island is shown one
  sibling on purpose.
- **Arm B wins on consistency alone**: the exemplar becomes recommended rather than required,
  and the rulebook says when to reach for it instead of saying always.
- **Arm B wins nothing that covers its token cost**: the pure island rule stays exactly as
  written, and the sharpest criticism this repository made of itself was wrong. That outcome
  gets written down in as much detail as the other two.
- **First-attempt success hits the ceiling in both arms**, as it did in experiment 02: that
  half is reported as undiscriminating rather than as a tie, and consistency decides alone.

## Experiment 04: does the conventional arm leave any room?

Added after 01, 02 and 03 had run, because all three of them compared BPT against variants of
BPT and none of them compared BPT against not using BPT. It has its own pre-registration, in
`04-conventional-ceiling/README.md`, for two reasons: it was fixed later, so folding it into
this file would blur the order that `git log` is supposed to prove, and it runs against a
private codebase, so its prompts and raw output cannot live here. That file records the sha256
of each prompt instead, and says plainly what a reader of this repository can and cannot verify.

## Experiment 05: does the ceiling survive a codebase three times the size?

Added after 04 cancelled the migration, and it attacks 04's own main limitation rather than
its conclusion. 04 measured a 5,300 line backend, which never stressed the context limits BPT
is built around, so its ceiling could be a fact about agents or a fact about small
repositories. 05 runs the same instrument, the same five shapes, the same thresholds and the
same model against a codebase 2.6 times larger by source volume, large enough that reading all
of it no longer fits a 200k token window. Its pre-registration is in `05-ceiling-at-scale/README.md`,
for the same two reasons 04 has its own: it was fixed later, and it runs against a private
codebase, so it publishes prompt hashes instead of prompts.

## Layout

```
experiments/
  README.md                      this file, the pre-registration for 01, 02 and 03
  RESULTS.md                     what happened, and which criterion it hit
  lib/runner.py                  fires N runs in a clean session, writes raw JSONL
  lib/score.py                   applies the rubric, prints the table
  01-hallucination-probe/
    plan.yaml                    cells, models, run count
    prompts/                     the three prompts
    rubric.yaml                  the scoring rubric, fixed before the first run
    runs/                        raw output, one JSONL per cell
  02-notation-penalty/
  03-exemplar/
    checklist.md                 the ten structural consistency items
  04-conventional-ceiling/
    README.md                    its own pre-registration, and the prompt hashes
  05-ceiling-at-scale/
    README.md                    same, for the repeat on a larger codebase
```

## Running

```bash
pip install pyyaml
python experiments/lib/runner.py --plan experiments/01-hallucination-probe/plan.yaml
python experiments/lib/score.py  --plan experiments/01-hallucination-probe/plan.yaml
```

The runner is resumable: a run already present in the JSONL is skipped, so an interrupted
sweep continues where it stopped instead of paying for the same tokens twice. Use `--dry-run`
to print the commands without spending anything, and `--budget-usd` to cap the sweep.

## When this is finished

Not when the scripts run. When all four of these hold:

1. This file is committed with a timestamp earlier than the first record in any `runs/`.
2. A baseline variance number exists, and it is smaller than the gap between arms in at least
   one experiment. If it is not, the result is "could not measure", and that goes in
   `RESULTS.md` as a legitimate outcome.
3. The experiment 01 rubric was applied twice by independent evaluators, deterministically and
   by a model, and the two readings agree. High disagreement means the rubric is bad: fix the
   rubric and re-score, never the result.
4. `RESULTS.md` names, for each experiment, which pre-registered criterion was hit, including
   when the criterion hit is the one that contradicts this repository's own audit.
