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

### Known limitation, stated up front

`--safe-mode` removes user customisation but keeps the default agentic system prompt. That
prompt is a constant across every cell and every arm, so it cannot explain a difference
between arms. For experiment 01 it is a mild contaminant on the absolute numbers, and it is
also the environment the architecture would actually be used in, which is the environment
worth measuring.

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

Three nodes of comparable size, none of them implemented yet, plus one finished and reviewed
node used as the exemplar.

- arm A, pure island (BPT as written): the node folder, its own contract, the contracts it
  consumes, the kernel read-only
- arm B, island plus exemplar: the same, plus the finished node in full

5 runs per cell, same model, same task.

Measured: first-attempt success, structural consistency against the fixed ten-item checklist
in `03-exemplar/checklist.md`, and tokens spent, because the exemplar costs context and the
gain has to cover that cost.

**Decision criteria, fixed in advance:**

- Arm B wins on consistency and on first-attempt success by a margin that covers the
  exemplar's token cost: the exemplar joins the context budget as a rule, and the rulebook
  changes.
- Arm B wins on consistency alone, without covering the cost: the exemplar becomes optional,
  recommended past some node count.
- The arms sit inside the baseline variance: the pure island rule stays and the contradiction
  raised against it was wrong.

## Layout

```
experiments/
  README.md                      this file, the pre-registration
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
