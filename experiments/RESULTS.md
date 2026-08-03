# Results

## Experiment 01: hallucination probe

### What was run

Revision 2 of the plan, on 2026-07-31, against Claude Opus 5 and Claude Sonnet 5 through
`claude -p` with `--safe-mode`, tools off, a neutral system prompt and a fresh empty working
directory per run. 34 runs, 0 failures, 5.18 usd including the 14 voided runs of revision 1.
Raw output is in `01-hallucination-probe/runs/`, scored output in `scored.json`.

Isolation was verified rather than assumed: every record carries `num_turns` of 1 and an empty
working directory listing, so nothing executed and nothing was written.

**Contamination check.** 4 of 4 runs say plainly that they do not know Behavior Parallel Tree
or BPT. The repository is not in either model's training data, so nothing below is recall.

An unasked finding came out of that cell. Across the eight contamination answers of both
revisions, three volunteered, without being prompted, that the name collides with **behavior
trees** from game AI and robotics, and one went further and named the parallel composite node.
The cell asked only whether the model knew BPT. It reached for the collision on its own.

### The numbers

| Cell | Model | Mean artifact | Times BPT's file | Standard inside the artifact |
| --- | --- | --- | --- | --- |
| a-declaration | Opus | 4,704 chars | 5.2x | none |
| a-declaration | Sonnet | 1,470 chars | 1.6x | none |
| b-contract | Opus | 15,421 chars | 11.2x | JSON Schema 4/5 |
| b-contract | Sonnet | 2,967 chars | 2.2x | JSON Schema 2/5 |
| c-spec | Opus | 24,362 chars | 20.2x | none (bespoke YAML) |
| c-spec | Sonnet | 5,539 chars | 4.6x | Gherkin 5/5 |

Key agreement, counted over keys that recur in two or more runs of a cell, so that domain
identifiers do not inflate the count:

| Cell | BPT keys appearing unprompted | The recurring names BPT does not use |
| --- | --- | --- |
| a-declaration | 4 of 23: `id`, `schema`, `version`, `contract` | `parts`, `depends_on`, `present_in`, `applications`, `path`, `owns` |
| b-contract | 14 of 23: `id`, `kind`, `input`, `output`, `errors`, `code`, `category`, `retryable`, `when`, `authorization`, `title`, `version`, `schema`, `contract` | `$ref`, `$defs`, `$schema`, `additionalProperties`, `allOf`, `bindings`, `constraints` |
| c-spec | 7 of 23: `id`, `title`, `version`, `rules`, `code`, `category`, `contract` | `cases`, `applies_to`, `fixtures`, `background`, `body_match`, `capture` |

Type vocabulary, over the ten contract runs: BPT's four invented types (`text`, `money`,
`list`, `decimal`) appeared **zero** times. Every artifact used `string`, `integer`, `number`,
`boolean`, `object`, `array`, `null`.

The `required` convention: the object level list appeared in 6 of 10 and the per field flag in
9 of 10. Both conventions are live, often in the same file.

### Which pre-registered criterion was hit

**Criterion 1, contract yields JSON Schema or OpenAPI in more than 60% of runs: ambiguous, and
therefore not declared hit.** Detecting over the whole answer gives 8 of 10, which clears the
threshold. Detecting over the artifact alone gives 6 of 10, which is exactly at a threshold
written as "more than". The pre-registration never said which text detection runs over. That
is a defect in how the criterion was written, not in the data, and the discipline the
pre-registration exists to enforce says the tie goes to nobody. It is recorded as
undiscriminating. What the data supports without needing the threshold is below, and it is
stronger than the criterion would have been.

**Criterion 2, the declaration yields an identity, a dependency list and a per-target list
unprompted: hit on substance, missed on vocabulary.** Every one of the ten runs produced all
three ideas in one root file. Four of BPT's names for them survived. The names the models
reach for are `parts` where BPT says `nodes`, `depends_on` where BPT says `deps`, and
`present_in` where BPT says `sides`.

**Criterion 3, no stable pattern across runs: not hit.** Each cell converged.

### What the data supports, independent of any threshold

1. **BPT's four invented types are pure tax.** Zero uses in ten runs, against seven
   in-distribution types used everywhere. This is the cleanest confirmation of the near-miss
   claim and it is the one change that costs nothing to make.

2. **BPT's contract envelope is already inside the distribution.** Fourteen of twenty three
   keys appear unprompted, including the whole error shape: `code`, `category`, `retryable`,
   `when`. That vocabulary was not invented, it was guessed right, and it should not be
   touched.

3. **A bespoke root manifest is what the distribution reaches for, and this refutes the
   audit.** The audit that motivated these experiments claimed Nx and Turborepo already derive
   the dependency graph, so `bpt.config.yaml` is redundant notation. Nx was mentioned zero
   times. Turborepo once, in ten runs. Nine of ten wrote a hand rolled YAML manifest, which is
   exactly what BPT did. The claim was wrong.

4. **Verbosity runs the other way, and the audit ignored it.** In-distribution notation costs
   between 1.6 and 20 times more characters than BPT's file for the same behavior. Context is
   the resource BPT exists to conserve, so this belongs on BPT's side of the ledger. It does
   not rescue the type vocabulary, where the cost of conforming is zero. It does complicate
   "replace the contract with JSON Schema", which now has to be argued as a trade rather than
   asserted as an obvious win.

5. **There is no single in-distribution answer for the spec, and one of the two answers is
   BPT's.** Sonnet wrote Gherkin five times out of five. Opus never did: it wrote a bespoke
   YAML with `cases`, an `applies_to` field selecting the surface per case, `fixtures`, and two
   harnesses that verify a server and a client from the same file. That is BPT's bilateral
   contract test, arrived at independently by a model that had never seen BPT. The audit
   treated `spec.md` as notation to be replaced by Gherkin. Half the evidence says the design
   is right and only the file format is a coin flip.

6. **The `required` inversion was overstated.** The audit called BPT's per field `required` a
   semantic inversion sitting on a high frequency pattern. Both conventions appear, frequently
   in the same file. This one should be dropped from the case against BPT.

7. **The name collides, measurably.** Three of eight answers volunteered behavior trees when
   asked only whether they knew BPT.

### What the audit got wrong

Recorded explicitly, because the point of pre-registering was to make this cost something:

- "Nx and Turborepo make the declaration file redundant." Refuted. Nine of ten runs wrote a
  bespoke manifest.
- "The `required` inversion is a near-miss liability." Weakened to the point of withdrawal.
  Both forms are ordinary.
- "The spec format should be Gherkin." Half refuted. The stronger model produced BPT's design
  instead.
- The audit never priced verbosity, and verbosity is the largest single number in this table.

### What this does not decide

Nothing about parallelism, nothing about adopting BPT in any product, and nothing permanent.
Every number here is attached to two models and one date. Re-running the probe against a newer
model is the intended use, not an exception.

## Experiment 02: notation penalty

### What was run

30 runs on 2026-07-31, Sonnet 5 only as pre-registered, 1.68 usd, 0 failures. Three contracts
carrying identical information for one behaviour, two cells, five runs per arm per cell.

### The `implement` cell: could not measure, and that is the result

| Arm | Scenarios passed, all 5 runs | Output chars, mean (range) | Cost usd, mean (range) |
| --- | --- | --- | --- |
| `arm-a-bpt` | 12 of 12, every run | 2,219 (2,071 to 2,299) | 0.0468 (0.0309) |
| `arm-b-types` | 12 of 12, every run | 1,783 (1,736 to 1,899) | 0.0219 (0.0102) |
| `arm-c-jsonschema` | 12 of 12, every run | 2,086 (1,713 to 2,318) | 0.0280 (0.0280) |

The primary metric hit the ceiling in all fifteen runs. Within-arm variance is zero, the gap
between arms is zero, and the pre-registered rule for that case says **could not measure**.

The secondaries do not rescue it. Arm A wrote 436 more characters than arm B on average, and
the widest within-arm range is 605, so the gap sits inside the noise. Arm A cost roughly twice
arm B, and that gap also sits inside the widest within-arm range. Both are recorded as noise,
not as findings, because the baseline was defined before the numbers existed.

**Criterion hit: "all three inside the baseline, could not measure."** The narrow reading is
that this task was too easy to separate the arms. The wider reading is worth stating too: with
a specification this precise, the contract's notation did not drive correctness at all. That is
evidence against the near-miss worry rather than for it.

### The static metric, which is where the surprise is

`price` had to be an exact amount, and every arm said so in the same words in its `rules`
block. What differed was only whether a type could say it.

| Arm | Implementations using `Decimal` for price |
| --- | --- |
| `arm-a-bpt` (`type: money`) | 5 of 5 |
| `arm-b-types` (`type: string`) | 0 of 5 |
| `arm-c-jsonschema` (`type: string`) | 0 of 5 |

Neither arm is wrong: each followed its own contract. But BPT's invented `money` type carried
a semantic into the code that the in-distribution vocabulary lost, and the prose rule did not
recover it. Arms B and C read "never held in binary floating point" and still returned
strings.

That is an argument for keeping `money`, produced by an experiment designed to find the
opposite, and it is the single most useful thing here.

One honest limit on it: arm C's JSON Schema says `type: string` and does not say
`format: decimal`, which is the in-distribution way to express exactly this. That was my
mapping choice, so arm C may have lost this metric to my hand rather than to JSON Schema. A
follow-up would need arm C revised, pre-registered, and re-run.

### The `extend` cell: the near-miss claim is refuted for contracts

Given a contract written in a vocabulary and asked to add two fields to it:

| Arm | What the added fields say | Conformance |
| --- | --- | --- |
| `arm-a-bpt` | `minPrice: { type: money }`, `currency: { type: text }` | 5 of 5 |
| `arm-b-types` | `currency: { type: string }` | 5 of 5 |
| `arm-c-jsonschema` | `currency: { type: string }`, and correctly added to the `required` array | 5 of 5 |

Not one run reverted to its prior. Handed a file that says `text` and `money`, the model wrote
`text` and `money`, every time.

**Criterion hit: "arm A conformance high, the near-miss worry is overstated for contracts, and
that is a result in BPT's favour."**

### What experiments 01 and 02 say together

They disagree, and the disagreement is the point.

Experiment 01 measured **preference**: left alone, a model does not reach for BPT's vocabulary.
Experiment 02 measured **performance**: handed BPT's vocabulary, the model follows it exactly,
produces correct code at the same rate as with the in-distribution alternative, and in the one
place the vocabularies differ in meaning, BPT's version produced the better code.

Preference and performance are not the same thing, and only one of them decides an
architecture. The audit assumed they moved together because the talk implied it. For BPT's
contract format, at this task size, they do not.

### What is NOT concluded from this

One behaviour, one model, one easy task, and a ceiling. The arms might separate on something
harder.

That is not a licence to keep raising the difficulty until a difference appears. Escalating a
task until the hypothesis wins is the same fishing the pre-registration bans, just slower. A
harder task is a new experiment, with its own criteria written before its own first run.

Nothing here tests the declaration file or the spec format, whose vocabularies experiment 01
found further out of distribution than the contract's.

## What changed in the repository because of these results

Recorded here, and not only in the changelog, because an experiment that changes
nothing was a way of passing the time.

- **The type vocabulary moved.** `text` became `string`, `list` became `array`,
  `decimal` became `number`, in `docs/CONTRACT-FORMAT.md`, in both shipped
  contracts, and in every doc that listed the types. Zero of ten runs produced
  the old three, and conforming costs nothing.
- **`money` stayed, and the reason is written next to it in the format doc.**
  Five of five implementations reached for an exact decimal type when the
  contract said `money`; zero of five did when it said `string` plus a rule in
  prose saying the same thing. It is the one invented type that carries meaning
  the standard vocabulary loses, and now it is an exception someone can audit
  rather than a preference.

Note for anyone reading experiment 02 later: `02-notation-penalty/contracts/arm-a-bpt.yaml`
still uses `text` and `list`, because it is the pre-registered material and it
recorded the format as it was on the day. It is deliberately not updated. The
format changed because of that run, so making the run match the format
afterwards would erase the only evidence for the change.

## Experiment 03: island with and without an exemplar

Not run. Material confirmed to exist: `content.deliver` and `vault.sync` are implemented on
both sides with tests and can serve as the exemplar.

Baseline variance: not measured yet.

## A lesson worth more than the experiment

The first fourteen runs were voided because the model, told it was an agent with tools, tried
to create the file, hit the disabled tool, and stopped. Four of five Sonnet runs came back with
an intention and no artifact.

The summary table looked healthy the whole time. Every run was recorded as ok, because the
process exited zero and returned text. Only reading the raw output caught it, and the failure
was not evenly distributed across models, so the surviving sample was biased toward the model
that stalls less.

An experiment whose failure mode is a well formed empty answer will quietly shrink its own
sample and report a clean table while doing it.
