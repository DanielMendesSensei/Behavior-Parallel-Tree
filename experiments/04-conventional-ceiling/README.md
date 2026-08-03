# Experiment 04: does the conventional arm leave any room?

**This file is the pre-registration. It is committed before the first run.**

## Why this one exists

Experiments 01, 02 and 03 all compared BPT against variants of BPT. None of them compared
building something with BPT against building it without. The root README says the test is "the
same feature built with and without BPT", and that test has never been run.

The obvious next move is to migrate a real codebase to BPT and run the same change requests on
both arms. That migration is three to five days of work. Before spending them, this experiment
asks the cheap question first: **run the change requests on the conventional arm alone, and see
whether the conventional arm leaves any room to win.**

If a normal agent, handed a normal repository and a search tool, already gets these changes
right on the first pass, reading few files and breaking nothing, then there is nothing for BPT
to improve and the migration is not worth doing. Two of the three experiments above hit exactly
that ceiling, and both times it was discovered after the tokens were spent, not before.

## The design, and why it is this one

**Same code, two layouts, same changes.** Not building the same feature twice: whoever builds
second inherits the first build's decisions. And not measuring construction at all, but change,
because building a small codebase is the model's best case and it hit the ceiling in
experiments 02 and 03.

This experiment is the first half of that: the conventional arm only.

**The codebase.** A private FastAPI backend, roughly 5,300 lines of application code over 55
files and 6,000 lines of tests over 15 files, laid out layer first (`api`, `services`,
`schemas`, `models`). It was chosen because layer first is the layout BPT defines itself
against, and because it is real work with real entanglement rather than a fixture built for the
occasion.

**The frozen baseline.** 353 tests pass and 9 fail before anything is touched. The 9 failures
are pre-existing and are not repaired: repairing them would change the codebase and dirty the
comparison. An equivalence gate demands that every test land in exactly the state the baseline
recorded, so a failure that starts passing is reported as loudly as a pass that starts failing.

**One run.** A fresh copy of the repository, the change request on stdin, a tool set of
`Read`, `Grep`, `Glob`, `Edit`, `Write`, and no way to execute anything. The agent gets one
pass. Then the diff is applied to a scoring clone, a hidden suite runs against it, and the gate
runs against it.

**The tool asymmetry is the point.** The conventional arm gets the whole repository and a
search tool, because that is how anyone works in a normal repository, and every token it spends
searching is counted. When the BPT arm eventually runs, it gets the declared slice and a tool
limited to the island, and leaving the island is not a setup error, it is the measurement.

## The five change requests

Five shapes, each anchored on real code in three domains (`conversations`, `admin`,
`subscriptions`). The prompts themselves are not in this repository (see below), so their
sha256 is recorded here instead, which is what fixes them in advance.

| Cell | Shape | Where it should hurt | prompt sha256 |
| --- | --- | --- | --- |
| `cr1-derived-field` | a derived field added to an existing output | schema, service, api, and two endpoints that share one payload | `b77b004318a86206` |
| `cr2-new-rule` | a new rule on an existing behavior | the service raises, the api translates, and three older refusals must survive | `89c85877da739c1a` |
| `cr3-new-behavior` | a new behavior consuming an existing one | a route that does not exist yet, over a service function nothing calls | `a1f3daa715ec9494` |
| `cr4-shared-rule` | a rule shared by two behaviors | one function, two callers, and the rule has to differ per caller | `f95b270bdac6e588` |
| `cr5-boundary-bug` | a bug whose symptom is in another domain | the cause is written in one domain and shows up in another | `74e4ffa1e56f21c9` |

`cr4` is the one BPT should struggle with, and it was picked for that reason. The island rule
says a behavior never reads another behavior, and this change cannot be made correctly without
knowing that a second behavior calls the same function and needs the opposite outcome.

`cr5` uses a bug injected on purpose rather than one found in the wild. It is proved before the
first run to be invisible to the existing suite, so the baseline stays at 353 and 9 with the
bug in place. The fixed behavior is what the hidden suite checks.

Every request states every rule its hidden suite checks. Nothing is left implicit. Experiment
03 lost 30 runs to a fixture that asked the model to guess, and the guess, not the arm, decided
the result.

## What is measured

Per run:

- **first-attempt success**: the hidden suite passes in full **and** the gate still reports 353
  and 9. Behavior only. The suite never looks at which file changed.
- **files opened**: unique paths the agent read. This is the number BPT's whole thesis is
  about.
- **repository ingested**: total characters returned by every tool call, which is the honest
  version of "how much of the repository had to enter the context".
- **tokens and cost**: from the run envelope, including cache reads.
- **out of boundary**: files changed that are not in the intended file set, which was written
  down before the first run by implementing each change once as a reference.
- **turns**, and whether the turn cap was reached, because a run that ran out of turns is a run
  that did not finish and must not be read as a failure of the change request.

Per cell, the minimum and maximum of files opened and of cost are reported alongside the
median. That spread is the variance number. Without it there is no way to tell a real
difference from noise, and it is the step most people skip.

## Decision criteria, fixed in advance

**Ceiling reached, and the migration does not happen.** First-attempt success of at least 23 of
25 overall, no cell below 4 of 5, a median of 8 or fewer files opened per run, and at most one
run of the 25 touching a file outside its boundary. Reading: the conventional arm already
delivers what BPT promises, so the comparison cannot discriminate and three to five days of
migration buy nothing. That result goes in the root README as evidence against BPT, in the same
detail as the other outcome.

**Room exists, and the migration goes ahead.** A cell discriminates when at least one of these
holds: success of 3 of 5 or worse, or a median of 20 or more files opened, or 2 or more of its
5 runs changing a file outside the boundary or breaking the gate. If two or more cells
discriminate, the migration covers the slice containing them and both arms then run those cells
only. Cells that do not discriminate are reported as undiscriminating and dropped, the way
experiment 02's success axis was.

**Exactly one cell discriminates.** The migration goes ahead only if that cell fits inside the
two-domain slice, which is 8 behaviors and about a day. Otherwise the honest move is to stop
and write down the finding instead of buying a comparison with one usable cell.

**A cell splits on two defensible readings of its request.** That cell is void. Its runs move
to `runs-void-rN/` with the reason, the request is repaired, and the cell runs again. This
happened in experiment 03 and it is the expected failure mode, not an accident.

**One model, and no fishing.** Sonnet, the same model as experiments 02 and 03, and the same
ban: if the arm does not hit the ceiling on Sonnet, Opus is not swapped in afterwards to hunt
for one. Any Opus run is a separate arm with its own pre-registration. A ceiling on Sonnet is
not evidence of a ceiling on a stronger model, and the reverse is not evidence either.

N is 5 per cell, 25 runs, for the reason given in the shared rules: this detects a large effect
and nothing smaller, and an effect too small for N=5 to see is too small to justify rewriting
an architecture.

## What is not in this repository, and why

The codebase under test is a private product. The change requests name its real modules, the
diffs contain its source, and the raw run output would publish both. So the prompts, the
fixtures, the reference implementations, the patches and the raw runs stay outside this
repository. What is published here is the design, the metric definitions, the criteria above,
the sha256 of each prompt, and the scored table in `RESULTS.md`.

This is weaker than experiments 01, 02 and 03, where the raw output is committed and anyone can
re-score it. A reader cannot verify this one, only check that the criteria were fixed before
the runs. Saying so is the only honest option available. Anyone wanting a verifiable version
would have to rebuild the fixture on a public codebase, which is real work and is not being
claimed here.

## Limitations, named before the runs rather than after

1. **One pass, nothing executed.** The agent cannot run the suite, so this measures navigation
   and first-pass correctness, not the ability to repair. `./bpt run` has a three-attempt loop
   with findings fed forward, so a comparison that stops here understates it. Either both arms
   get the loop later, or the result is reported as being about the first pass only.
2. **The requests are explicit on purpose.** Every rule the hidden suite checks is stated in
   the request. That is a small contract written in prose, handed to the conventional arm for
   free, and it flatters that arm. The alternative, leaving rules implicit, measures whether
   the model guesses a house convention, and that is what voided 30 runs of experiment 03. The
   bias is recorded, not corrected.
3. **One codebase, one layout, one framework.** Whatever comes out is about a 5,300 line layer
   first FastAPI backend. It is not a statement about layer first in general, and it is not a
   statement about large codebases.
4. **The bug in `cr5` was planted by us.** A bug we chose is a bug we may have made easier to
   find than a real one.
5. **No test writing.** Every request forbids touching `tests/`, so the gate stays meaningful
   and the runs stay comparable. Real work includes writing tests, and this does not measure
   that.

## When this is finished

1. This file is committed with a timestamp earlier than the first recorded run.
2. Each hidden suite was proved both ways before the first run: red against the untouched
   repository and green against a reference implementation. A suite that has only ever been
   seen failing proves nothing.
3. The injected bug in `cr5` was proved invisible to the existing suite before the first run.
4. `RESULTS.md` names which pre-registered criterion was hit, including when it is the one that
   says the migration was never worth doing.
