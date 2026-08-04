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

### What was run

Revision 2 of the plan, on 2026-08-03, Sonnet 5 only as pre-registered. 30 runs, 0 failures,
0.43 usd. Three targets, two arms, five runs per cell. Revision 1 ran 30 times and was voided;
its output is in `03-exemplar/runs-void-r1/` and the reason is below.

### First-attempt success: the ceiling, as predicted

**30 of 30 answers passed every scenario, in both arms.** Not one run needed a second attempt,
in either arm, on any of the three targets.

**Criterion 4 hit**, the one written for exactly this case: it is reported as undiscriminating
rather than as a tie, and consistency decides alone. The prediction that it would hit was
written down before the run, which is the only reason it is worth anything.

### Structural consistency: the pre-registered bar was not cleared

| Item | arm A, pure island | arm B, with exemplar |
| --- | --- | --- |
| module docstring in the exemplar's form | 3/15 | 15/15 |
| `from kernel import ...`, not a plain import | 15/15 | 15/15 |
| `require_session` first in the public function | 15/15 | 15/15 |
| validation isolated in a helper | 4/5 | 5/5 |
| helpers private | 8/8 | 15/15 |
| contract literals hoisted to constants | 1/5 | 5/5 |
| every raise is `AppError` with a declared code | 15/15 | 15/15 |
| output built as a dict literal in place | 15/15 | 15/15 |
| ordering as `sorted(..., key=...)` | 0/10 | 5/10 |
| no class, no module level mutable state | 15/15 | 15/15 |

| | arm A | arm B |
| --- | --- | --- |
| consistency, mean | 78% | 96% |
| note-detail | 76% (spread 14) | 88% (spread 0) |
| tag-list | 74% (spread 30) | 100% (spread 0) |
| note-archive | 83% (spread 0) | 100% (spread 0) |
| chars written, mean | 821 | 1,245 |
| cost of 15 answers | 0.188 usd | 0.245 usd |

The gap between the arms is 18 points. The baseline, defined in advance as the widest
within-arm range across the cells, is 30 points, and it comes from arm A on `tag-list`.
**18 is inside 30, so on the pre-registered rule this is "could not measure",** and the
outcome that fires is the third one: the pure island rule stays exactly as written.

That is not the reading I expected to write. The mean gap is large, every per-target
comparison favours arm B, and two items are not close. None of that matters: the rule that
decides was fixed before the numbers existed, precisely so that a favourable-looking table
could not talk its way past it. The baseline definition is arguably too blunt here, because it
applies the noisiest cell's spread to every cell. Sharpening it is a change to make **before**
the next run, not after this one.

Rubric integrity: every item was decided by walking the syntax tree rather than matching text,
and an independent model reading of the judgement-based items agreed with it **92%** of the
time, above the 80% the protocol requires.

### The finding nobody pre-registered

Arm B's within-arm spread is **zero on all three targets**. Fifteen answers, three different
behaviours, and within each behaviour every answer scored identically. Arm A's spreads are 0,
14 and 30.

The exemplar did not only move the average. It removed the variance. A rule about whether a
gap exceeds the noise has nothing to say about one arm having no noise at all, and that is a
different claim from the one this experiment was built to test.

It is written here as an observation and not as a result, because it was not pre-registered
and reinterpreting a run around something spotted afterwards is the failure the whole protocol
exists to prevent. If it is worth chasing, it is worth its own experiment, with variance as
the declared primary metric and a criterion written before the first run.

### What it cost

The exemplar is not free: arm B wrote 52% more characters and cost 30% more for the same
fifteen behaviours. Any future decision to put a sibling in the context budget has to carry
that number with it.

### The void, and the lesson that repeats

Revision 1's arms came back separated: with the exemplar, two of three targets scored worse,
one of them 3 of 8 against 7 of 8, stable across all five runs.

It was the fixture. Nothing in the contract, the spec or the kernel said how a note relates to
a tag, so both arms invented it. One invented `t.get("note_id")`, which returns None and
degrades quietly to an empty list. Another invented `t["note_id"]`, which raises and takes
five tests down with it. What separated the arms was which key a run made up and whether it
reached for `.get` or a bracket: a coin flip about defensive coding, measured to three
significant figures.

The fix was symmetric and landed in the one file both arms already read: the kernel now
documents the shape of the rows it returns. Both arms gained the same sentence.

That is twice in three experiments that the summary table looked healthy and the raw output
said otherwise. In experiment 01 an empty answer shrank the sample without failing. Here an
underspecified task turned a coin flip into a stable difference between arms. **An experiment
does not warn you when it is measuring the wrong thing. It reports it cleanly.**

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

## Experiment 04: does the conventional arm leave any room?

### What was run

Five change requests against a private layer-first FastAPI backend, 5 runs each, Sonnet, 25
runs, 4.08 usd, no failures. Pre-registration in `04-conventional-ceiling/README.md`, committed
before the first run, with the sha256 of each prompt.

One run is a fresh copy of the repository, the request on stdin, a tool set of `Read`, `Grep`,
`Glob`, `Edit`, `Write`, and no way to execute anything. Then the diff goes onto a scoring
clone, a hidden suite runs against it, and the equivalence gate runs against it. The baseline
is 353 passing and 9 failing, and the gate demands that every test land in exactly that state.

### The numbers

| Cell | k/n | files read | chars of repo ingested | cost usd | turns | outside boundary | gate broken |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `cr1` derived field | 5/5 | 3 (3 to 5) | 12,268 | 0.128 (0.106 to 0.137) | 11 | 0 | 0 |
| `cr2` new rule | 5/5 | 4 (4 to 5) | 20,995 | 0.201 (0.153 to 0.231) | 15 | 0 | 0 |
| `cr3` new behavior | 5/5 | 6 (5 to 7) | 26,520 | 0.202 (0.162 to 0.251) | 15 | 0 | 0 |
| `cr4` shared rule | 5/5 | 4 (3 to 5) | 33,394 | 0.221 (0.172 to 0.241) | 11 | 0 | 0 |
| `cr5` boundary bug | 5/5 | 1 (1 to 2) | 11,401 | 0.076 (0.072 to 0.081) | 6 | 0 | 0 |

Medians, with the within-cell spread in brackets. First-attempt success means the hidden suite
passed in full and the gate still reported 353 and 9.

### Which pre-registered criterion was hit

**The ceiling, on all four of its conditions.** The criterion asked for at least 23 of 25, no
cell below 4 of 5, a median of 8 or fewer files opened, and at most one run touching a file
outside its boundary. What came back was 25 of 25, every cell at 5 of 5, medians of 1 to 6
files, and zero runs leaving their boundary.

The pre-registered consequence is that the migration does not happen. Three to five days of
work, priced at 30 to 80 usd of tokens starting from a clean session, would have bought a
comparison against an arm that is already at the top of every axis being compared.

### The cell that was supposed to hurt did not

`cr4` was chosen because it is the case BPT should lose: one function, two callers, and the
rule has to change for one caller and stay for the other. The island rule says a behavior never
reads another behavior, and this change cannot be made correctly without knowing about the
second caller.

Five runs, two different correct strategies, neither breaking the other caller. Three runs
added a defaulted parameter to the shared function, so the untouched caller keeps its old
behavior. One run never touched the shared function at all and did the arithmetic at the call
site. Both are defensible, both passed, and both stayed inside the boundary.

### What nothing in 25 runs did

No run touched a file outside its pre-registered boundary. No run moved any of the 9
pre-existing failures, in either direction. No run modified anything under `tests/`, which was
forbidden by the request. The number BPT exists to improve, how often a change reaches for a
file outside its declared island, came back at zero without BPT.

### The reading that is sharper than "BPT is useless"

Every request stated every rule its hidden suite checked. That is a contract, written in prose,
handed to the conventional arm for free. It was done deliberately, because leaving a rule
implicit is what voided 30 runs of experiment 03, and it was recorded as a bias before the
runs rather than discovered after them.

So the honest statement of what happened is not that the layout does not matter. It is that
**given a precise specification, the layout did not matter measurably here.** The specification
did the work.

That lines up with experiment 02, where the contract notation earned its keep on a real
measurement (`type: money` produced `Decimal` 5 of 5, against 0 of 5 for prose plus
`type: string`). Two experiments now point the same way: the part of BPT with evidence behind
it is the contract, and the part still without any is the tree.

### What this does not decide

**The other half of the bet is untouched.** The hypothesis has two clauses, less context per
change and independent changes running in parallel without coordination. This experiment
measured the first one only. Nothing here says anything about the second.

**Size.** The codebase is 5,300 lines of application code. BPT's argument is about context
limits, and 5,300 lines does not come close to stressing them. A ceiling at this size is not
evidence of a ceiling at 50,000 or 500,000 lines, and the most likely place for the next honest
test is a codebase big enough that whole-repository reasoning stops being free.

**One pass, nothing executed.** The arm could not run the suite, so this is first-pass
navigation and correctness, not repair. `./bpt run` has a three-attempt loop with findings fed
forward, and that loop is untested by this.

**Sonnet only**, as pre-registered, and the ban held: no Opus runs were added afterwards.

**`cr5` was easier than it looked.** The injected bug was a case drift, `"Active"` where the
rest of the code writes `"active"`. Every run found it with two greps and one file read. That
cell therefore measured whether a regular expression finds a case typo, not whether an agent
can cross a domain boundary. The limitation was named in the pre-registration in the abstract
and it landed in the concrete. The cell is not voided, because all five runs agreed and the
number is true for that instance, and voiding a cell for producing an inconvenient result is
how a favourite hypothesis wins. A harder instance, a rounding or a timezone or a sign, would
need its own pre-registration.

### How the instrument was checked before the result was believed

A 25 of 25 deserves more suspicion than a mixed table, so the instrument was made to fail on
purpose.

Each hidden suite was proved both ways before the first run: red against the untouched
repository, green against a reference implementation written for that purpose. Every red was a
failing assertion on an API response, never an import or fixture error, because a suite that
crashes proves nothing about the arm it crashes on.

After the sweep, a patch that applies cleanly and changes nothing relevant was pushed through
the whole scoring path. It came back with the suite failing 3 of 4 and the gate green, which is
exactly right: harmless change, no fix. A patch that does not apply at all is recorded as such
and scored as a failure. The gate's own output text is stored in every scored run, so
"equivalent: 353 pass and 9 fail" is evidence rather than a boolean somebody set.

### What changed in the repository because of this

The migration is cancelled. The root README's hypothesis section now says that half the bet has
been tested once, in one direction, and what came back.

## Experiment 05: does the ceiling survive a codebase three times the size?

### What was run

The instrument from experiment 04, unchanged, against a different codebase: a private Django
and DRF backend of roughly 16,000 lines of application code over 74 files, which is 1.07 MB of
Python against the 412 KB of experiment 04's arm. That was the whole point. 412 KB fits in a
200k token window and 1.07 MB does not, so this is the first time the conventional arm was
asked the question BPT is actually built around.

Same runner, same scorer, same gate, same executor and tool set, same five change request
shapes, same model, same N of 5, same thresholds. Twenty five runs, 8.48 usd.

Frozen baseline: 934 tests, 932 passing and 2 failing, and the 2 are pre-existing and were not
repaired.

### The numbers

| Cell | first-attempt | files opened | repo ingested | usd | turns | outside boundary | gate broke |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `cr1` derived field | 5/5 | 1 (1 to 1) | 8,352 | 0.107 (0.077 to 0.136) | 7 | 0 | 0 |
| `cr2` new rule | 5/5 | 5 (4 to 6) | 151,181 | 0.794 (0.717 to 0.886) | 21 | 5 | 0 |
| `cr3` new behavior | 5/5 | 4 (3 to 4) | 94,957 | 0.343 (0.184 to 0.435) | 12 | 0 | 0 |
| `cr4` shared rule | 5/5 | 4 (3 to 4) | 59,824 | 0.369 (0.316 to 0.425) | 16 | 0 | 0 |
| `cr5` boundary bug | 5/5 | 1 (1 to 1) | 17,118 | 0.083 (0.082 to 0.089) | 4 | 0 | 0 |

### The one number that answers the question this experiment was for

Files opened per change, experiment 04 first and experiment 05 second, on a codebase 2.6 times
larger: `cr1` 3 then 1, `cr2` 4 then 5, `cr3` 6 then 4, `cr4` 4 then 4, `cr5` 1 then 1.

It did not move. On three of five shapes it fell. The agent does not read more of a repository
because the repository is bigger, because it never reads the repository: it greps for a symbol,
gets a path back, and opens that file. Size is paid by the search index, not by the context.

That is the claim BPT is built to make, measured on the arm that does not have BPT.

### What did move, and it is worth naming

Characters of repository ingested per run, 04 then 05: `cr1` 12,268 then 8,352, `cr2` 20,995
then 151,181, `cr3` 26,520 then 94,957, `cr4` 33,394 then 59,824, `cr5` 11,401 then 17,118.
Cost followed, most sharply on `cr2`, from 0.201 to 0.794 usd.

So the honest split is that the count of files did not grow with the codebase but the volume
behind each answer did, up to seven times on the heaviest cell. `cr2` is the three file change,
and it is the one where the agent had to read a large view module and a large service module in
full rather than a serializer. A bigger codebase makes individual files bigger, and that is
where the cost went.

Whether a declared boundary would have cut that volume is not something this sweep can say. It
would need the arm that experiment 04 cancelled.

### Which pre-registered criterion was hit

By the letter, none cleanly, and this is where it has to be read carefully rather than rounded
in the convenient direction.

The ceiling condition required first-attempt success of at least 23 of 25, no cell below 4 of
5, a median of 8 or fewer files opened, and **at most one run of the 25 touching a file outside
its boundary**. The first three passed by a wide margin: 25 of 25, no cell below 5 of 5, medians
of 1 to 5. The fourth did not. Five runs went outside, all of them in `cr2`.

The discriminate condition says a cell discriminates when 2 or more of its 5 runs change a file
outside the boundary. `cr2` did, in all five. So exactly one cell discriminates, and the
pre-registered consequence of exactly one is that it is reported as one usable cell and no arm
is built on it.

Both readings land in the same place, which is the only reason this is reportable at all: no
BPT arm is built.

### What the boundary violation actually was

All five `cr2` runs wrote a Django migration for the new `block_reason` choice, in
`apps/downloads/migrations/`, which is not in that cell's pre-registered file set.

The file set is the file list of the reference implementation, and the reference did not write
one, because the test suite does not check for pending migrations. The five runs did. Changing
`choices` on a Django model does call for a migration, so the runs were more complete than the
reference they are measured against.

The pre-registration says a run outside its set "is not automatically wrong, it is counted and
read with judgement, because a defensible change can land somewhere the reference did not go".
That sentence was written for this, and it is being honoured rather than quietly used: the five
are counted, the criterion they trip is reported as tripped, and the judgement is written here
where it can be argued with. Reading those five as evidence that a declared boundary would have
helped would be backwards. A boundary that forbade the migration would have made the change
worse.

The defect is in the boundary definition, and it belongs to us. Deriving the intended file set
from a reference implementation assumes the reference is the most complete correct answer, and
here it was not.

### The gate aged out mid sweep, and what was done about it

The pre-registration named a risk before the first run: both baseline failures are date
dependent. That risk fired the same evening. At 00:00 UTC the two flipped from fail to pass and
the gate started calling every run damaged, including runs that changed nothing near them.

The check that settled it: the untouched arm, with no patch applied, fails its own baseline
after that hour. A gate that condemns a pristine repository is measuring the clock.

The two ids were exempted and all 25 runs were scored again, which costs nothing because
scoring spends no tokens. The amendment in `05-ceiling-at-scale/README.md` records what changed,
why it is a repair rather than a loosened criterion, and what the exemption costs: the gate can
no longer speak about those two tests.

Checked afterwards, across all 25 runs: no run moved any test other than those two, and no run
touched anything under `tests/`. So the exemption hid nothing.

### How the instrument was checked before the result was believed

A second 25 of 25 deserves more suspicion than the first one did.

Every hidden suite was proved both ways before the first run: red against the untouched
repository, green against a reference written for that cell, with the gate clean afterwards in
all five. The `cr5` bug was chosen by measuring coverage rather than by taste, planted on one of
the five lines the existing suite never executes, and then verified invisible by running the
gate with it applied. Experiment 04's `cr5` bug was a case drift that a regex finds, and that
cell measured less than it should have. This one has to be found by following an endpoint into
the service layer.

After the sweep, a patch that applies cleanly and changes nothing relevant was pushed through
the whole scoring path. It came back with the acceptance suite failing and the gate green,
scoring 0 of 1, which is exactly right: harmless change, no fix, no credit.

### What this does not decide

The second limitation of experiment 04 is untouched and is now the one that matters most. Every
request still states every rule its hidden suite checks. That is a contract written in prose and
handed to the conventional arm for free, and two experiments have now produced ceilings under
that condition. The fair summary after 05 is the same as after 04, with more weight behind it:
a precise specification does the work, and the layout has not been shown to add anything on top
of it, at 5,300 lines or at 16,000.

The framework also moved with the size, FastAPI to Django, so a difference between the two
sweeps could not have been attributed to size alone. There was no difference to attribute,
which is the reading that survives that confound rather than falling to it.

And the second half of the bet, independent changes running in parallel without coordination,
has still never been tested.

## Experiment 06: do two uncoordinated changes compose?

### What was run

Nothing was run. Experiment 05's 25 patches were each produced by an agent alone in its own copy
of the same base commit, with no knowledge that the other runs existed, which is already what
parallel work without coordination means. This experiment is the step nobody had taken: putting
pairs of them back together and looking for damage. Zero tokens.

Thirty combinations, six pairs of five run indexes. Three pairs whose runs touched no file in
common, three whose runs shared `views.py` and in one case `rate_limit_service.py` as well.

### The numbers

| Kind | combinations | textual conflicts | order dependent | semantic conflicts |
| --- | --- | --- | --- | --- |
| disjoint | 15 | 0 | 0 | 0 |
| overlapping | 15 | 0 | 0 | 0 |

Every composed tree was checked properly rather than assumed: both acceptance suites ran against
it and passed in full, and the gate came back clean on all thirty.

### Which pre-registered criterion was hit, and it is the unhappy one

The void clause. The pre-registration said the overlapping pairs were there to prove the
detector can detect, and that fewer than three conflicts among them would make a clean disjoint
result indistinguishable from a broken checker. Zero came back. So the disjoint result is void
as a statement about parallelism, and it is reported that way rather than as the ceiling it
superficially resembles.

That clause was written before the composition, with the note that it was the likely outcome.
It was.

### The finding that is real, even though the probe is void

**"Same file" is not "same behavior", and the gap between them is where this probe fell in.**
Three pairs that both edit `views.py`, a 1,700 line module, composed fifteen times out of
fifteen without a single conflict of any kind. Agents edit at the granularity of a function.
Two changes to different functions in one module do not collide, textually or semantically, even
when the module is large and the changes are substantial.

That is worth stating plainly because it is the reason the probe could not answer its question.
A pair was needed that collides inside the same function, and file overlap was the wrong proxy
for building one.

### What the positive control adds, and what it does not

The void clause reasons that a clean sweep could mean a broken checker. That is testable, so it
was tested afterwards: two patches from the same cell, two agents solving the same request, were
composed. The second patch failed to apply, in both pairs tried. The checker detects.

So the thirty clean results are real data rather than an artifact, and that is worth having. It
is not, however, the evidence the pre-registered criterion asked for, and it is not being
swapped in for it now. The disjoint result stays void.

### What this costs, and what comes next

The probe was free and it bought one useful negative: the cheap version of this question cannot
be answered with the patches already on disk. The next version has to cost tokens. It needs two
change requests written to collide inside a single function, run as their own cells, and then
composed the same way.

Until that runs, the second clause of the hypothesis remains what it has been since the
beginning: untested.
