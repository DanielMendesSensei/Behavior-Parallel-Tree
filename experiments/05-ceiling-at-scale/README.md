# Experiment 05: does the ceiling survive a codebase three times the size?

**This file is the pre-registration. It is committed before the first run.**

## Why this one exists

Experiment 04 ran five change requests against a real layer-first codebase with no BPT, hit
the ceiling on all four pre-registered conditions, and cancelled the migration that would
have built the BPT arm. That result came with two limitations written down before the runs,
not after. This experiment attacks the first one.

The limitation was stated like this: "One codebase, one layout, one framework. Whatever
comes out is about a 5,300 line layer first FastAPI backend. It is not a statement about
layer first in general, and it is not a statement about large codebases."

That matters more than it sounds. BPT's argument is about context: a declared boundary is
supposed to earn its keep when reading the whole repository stops being affordable. At
5,300 lines of application code the repository fits in the window with room to spare, so
the arm was never asked the question BPT is built to answer. A ceiling found under those
conditions could be a fact about agents, or it could be a fact about small repositories.

So the same instrument runs again, unchanged, against a codebase where reading everything
is no longer free.

## What is different from experiment 04, and what is deliberately identical

**Identical:** the runner, the scorer, the equivalence gate, the executor and its exact
tool set, N of 5 per cell, Sonnet only, one arm, the five change request shapes, and every
decision threshold below. Nothing about the measurement was retuned for the new codebase.
That is the point. A threshold rewritten to fit a bigger repository is a threshold chosen
after seeing the terrain.

**Different:** the codebase, and only the codebase.

## The codebase

A private Django and Django REST Framework backend: roughly 16,000 lines of application
code over 74 files, and 10,700 lines of tests over 28 files. Measured as characters of
Python, which is the honest proxy for what a context window has to swallow, it is 1.07 MB
against the 412 KB of experiment 04's arm, so about 2.6 times larger. That figure is the
reason this codebase was chosen: 1.07 MB of source does not fit in a 200k token window, and
412 KB comfortably does. Reading the whole repository stopped being free somewhere between
those two numbers.

**The layout is a hybrid, and saying so is not optional.** Domains get their own package
(`apps/downloads`, `apps/users`, `apps/core`) with layers inside each one, and on top of
that sit two shared layers every domain reaches into: `services/` and `api/`. Experiment
04's arm was layer first throughout. This one is layer first only where the entanglement
actually lives, which is the shared service layer.

This cuts both ways and both are recorded here in advance. It is a weaker test of "layer
first hurts", because part of this codebase is already grouped by domain, which is closer
to what BPT advocates. It is a stronger test of "does size change the answer", because the
shared service layer is where four of the five change requests land, and that layer is
reached from several domains at once.

## The frozen baseline

934 tests, 932 passing and 2 failing, before anything is touched. The 2 failures are
pre-existing and are not repaired: repairing them would change the codebase and dirty the
comparison, which is the rule inherited from experiment 04, where 9 failures were left
alone for the same reason. Both failures are date dependent, which is recorded here as a
known risk to the baseline rather than discovered later.

The equivalence gate demands every test land in exactly the state the baseline recorded, so
a failure that starts passing is reported as loudly as a pass that starts failing.

## One run

A fresh copy of the repository, the change request on stdin, a tool set of `Read`, `Grep`,
`Glob`, `Edit`, `Write`, and no way to execute anything. The agent gets one pass. Then the
diff is applied to a scoring clone, a hidden suite runs against it, and the gate runs
against it.

## The five change requests

Five shapes, the same five as experiment 04, each anchored on real code in this codebase.
The prompts themselves are not in this repository (see below), so their sha256 is recorded
here instead, which is what fixes them in advance.

| Cell | Shape | Where it should hurt | prompt sha256 |
| --- | --- | --- | --- |
| `cr1-derived-field` | a derived field added to an existing output | one serializer feeding a list endpoint and a detail endpoint | `3e4da50118e3c5b2` |
| `cr2-new-rule` | a new rule on an existing behavior | the service refuses, the view translates the refusal, and four older refusals must survive | `aa6608b13515e92b` |
| `cr3-new-behavior` | a new behavior consuming an existing one | a route that does not exist yet, over a service function nothing calls | `9846541cba0df2ee` |
| `cr4-shared-rule` | a rule shared by two behaviors | one function, two endpoints calling it, and the answer now has to differ per caller | `746f23e7d08010ed` |
| `cr5-boundary-bug` | a bug whose symptom is in another domain | the cause is a branch in `services/`, the symptom comes out of an endpoint in `apps/downloads` | `50a548f7d1034b80` |

`cr4` is again the cell BPT should struggle with, and this codebase gives a sharper version
of it than experiment 04 did. The shared function is called by two distinct endpoints that
already disagree about who the caller is, and the change requires them to get different
answers. The island rule says a behavior never reads another behavior, and this change
cannot be made correctly without knowing what the second caller needs.

`cr5` uses a bug injected on purpose. Experiment 04's injected bug was a case divergence
that a regex finds, and that cell measured less than it should have. This one was chosen by
measuring coverage first: it sits on a line the existing suite never executes, so it is
invisible by construction rather than by hope, and it was verified invisible before the
first run. Finding it means following an endpoint into the service layer, not grepping for
the symptom.

Every request states every rule its hidden suite checks. Nothing is left implicit.
Experiment 03 lost 30 runs to a fixture that asked the model to guess, and the guess, not
the arm, decided the result. That bias is named again in the limitations below, because
stating the rules flatters the conventional arm.

## What is measured

Per run:

- **first-attempt success**: the hidden suite passes in full **and** the gate still reports
  932 and 2. Behavior only. The suite never looks at which file changed.
- **files opened**: unique paths the agent read. This is the number BPT's whole thesis is
  about, and the number this experiment exists to see move.
- **repository ingested**: total characters returned by every tool call, which is the honest
  version of "how much of the repository had to enter the context".
- **tokens and cost**: from the run envelope, including cache reads.
- **out of boundary**: files changed that are not in the intended file set, which was
  written down before the first run by implementing each change once as a reference.
- **turns**, and whether the turn cap was reached, because a run that ran out of turns is a
  run that did not finish and must not be read as a failure of the change request.

Per cell, the minimum and maximum of files opened and of cost are reported alongside the
median. That spread is the variance number. Without it there is no way to tell a real
difference from noise.

Every one of these is also reported next to experiment 04's figure for the same cell shape,
because the comparison between the two sweeps is the actual result of this experiment.

## Decision criteria, fixed in advance

The thresholds below are experiment 04's, copied without change. One reading is new, and it
covers a case experiment 04 left undefined. Adding it closes a hole before any run rather
than after, which is the only time a criterion can honestly be added.

**Ceiling reached, and size does not change the answer.** First-attempt success of at least
23 of 25 overall, no cell below 4 of 5, a median of 8 or fewer files opened per run, and at
most one run of the 25 touching a file outside its boundary. Reading: the conventional arm
delivers what BPT promises at this size too, and 04's result was not an artefact of a small
repository. That goes in the root README as evidence against BPT, in the same detail as the
other outcomes.

**Room exists.** A cell discriminates when at least one of these holds: success of 3 of 5 or
worse, or a median of 20 or more files opened, or 2 or more of its 5 runs changing a file
outside the boundary or breaking the gate. If two or more cells discriminate, there is a
case for a BPT arm at this size, and it gets built only under its own pre-registration
naming the slice and the cells, not by extending this file.

**Exactly one cell discriminates.** Reported as one usable cell, and no arm is built on it.
Buying a comparison with a single discriminating cell is what experiment 04 declined to do
at a smaller size, and the reasoning does not improve with scale.

**Correct but more expensive, which experiment 04 never wrote a reading for.** Success at
ceiling (23 of 25 or better, no cell below 4 of 5) and at most one boundary violation, but
the median files opened lands between 9 and 19 in one or more cells. Reading: the arm still
gets the work right while paying more context to do it, so the number BPT exists to reduce
did move with size while correctness did not. The consequence, fixed here: no arm is built,
and what gets written down is that first-attempt correctness is insensitive to size across
this range while context per change is not, with the medians from both experiments side by
side. Any later argument for BPT resting on the context number alone would need its own
pre-registration saying exactly that, because correctness would not be supporting it.

**Anything else.** Any outcome that fires none of the branches above is reported as
inconclusive, with the numbers in the open and no arm built. The criteria are meant to be
exhaustive, and a result that escapes them is a defect in this file worth admitting rather
than a result worth interpreting freely.

**A cell splits on two defensible readings of its request.** That cell is void. Its runs
move to `runs-void-rN/` with the reason, the request is repaired, and the cell runs again.
This happened in experiment 03 and it is the expected failure mode, not an accident. A cell
is not void because its result is inconvenient: experiment 04's `cr5` measured less than it
should have and was reported with the caveat instead of being dropped.

**One model, and no fishing.** Sonnet, the same model as experiments 02, 03 and 04, and the
same ban: if the arm does not hit the ceiling on Sonnet, Opus is not swapped in afterwards
to hunt for one. Any Opus run is a separate arm with its own pre-registration.

N is 5 per cell, 25 runs, for the reason given in the shared rules: this detects a large
effect and nothing smaller, and an effect too small for N=5 to see is too small to justify
rewriting an architecture.

## What is not in this repository, and why

The codebase under test is a private product. The change requests name its real modules, the
diffs contain its source, and the raw run output would publish both. So the prompts, the
fixtures, the reference implementations, the patches and the raw runs stay outside this
repository. What is published here is the design, the metric definitions, the criteria
above, the sha256 of each prompt, and the scored table in `RESULTS.md`.

This is the same weakness experiment 04 carries, and it is worth repeating rather than
burying. A reader cannot verify this one, only check that the criteria were fixed before the
runs. Anyone wanting a verifiable version would have to rebuild the fixture on a public
codebase, which is real work and is not being claimed here.

## Limitations, named before the runs rather than after

1. **Two things changed at once, not one.** The intent was to vary size alone, and the
   framework moved with it: experiment 04 measured a FastAPI backend and this one measures
   Django and DRF. No larger FastAPI codebase was available to test. So a difference between
   the two sweeps cannot be attributed to size with confidence, and a similarity is the
   safer of the two readings to trust.
2. **The layout is a hybrid.** Described above. If this arm does well, some of the credit
   may belong to the domain-shaped packages rather than to the agent, and that reading has to
   stay on the table.
3. **One pass, nothing executed.** The agent cannot run the suite, so this measures
   navigation and first-pass correctness, not the ability to repair. `./bpt run` has a
   three-attempt loop with findings fed forward, so a comparison that stops here understates
   it.
4. **The requests are explicit on purpose.** Every rule the hidden suite checks is stated in
   the request. That is a small contract written in prose, handed to the conventional arm for
   free, and it flatters that arm. It is also the bias experiment 04 identified as the likely
   explanation of its own result, and this experiment does not remove it. Removing it is a
   different experiment, and it is the one the 04 result actually argues for.
5. **The bug in `cr5` was planted by us.** A bug we chose is a bug we may have made easier to
   find than a real one, even after choosing it by coverage rather than by taste.
6. **No test writing.** Every request forbids touching `tests/`, so the gate stays meaningful
   and the runs stay comparable. Real work includes writing tests, and this does not measure
   that.
7. **1.07 MB is bigger, not big.** It exceeds a 200k token window, which is the threshold
   this experiment was designed to cross. It is not a million line monolith, and nothing here
   is a statement about one.

## When this is finished

1. This file is committed with a timestamp earlier than the first recorded run.
2. Each hidden suite was proved both ways before the first run: red against the untouched
   repository and green against a reference implementation. Done, and recorded privately in
   `PROOF.md` alongside the runs.
3. The injected bug in `cr5` was proved invisible to the existing suite before the first run,
   by measuring coverage to choose the line and by running the gate to confirm it.
4. `RESULTS.md` names which pre-registered criterion was hit, including when it is the one
   that says nothing new was learned, and prints the experiment 04 figures next to the new
   ones.
