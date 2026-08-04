# The verdict, after eight experiments

Eight experiments, 228 runs, 36.99 usd, two and a half hours of model time. This file says what
came out and what it means for the architecture this repository proposes. It is written by the
people who proposed it, which is exactly why every criterion below was fixed in writing before
its runs and why the ones that went against the idea are the ones reported in most detail.

## The bet, restated

The root README makes one claim in two clauses:

> when the boundary of a change is declared, checkable and machine-readable, an agent needs less
> context to make that change correctly, and independent changes can run in parallel without
> coordination.

Both clauses have now been measured on the arm that does not use BPT. Neither survived.

## Clause one: less context per change

| Experiment | What it asked | What came back |
| --- | --- | --- |
| 02 | does the bespoke contract format beat JSON Schema | it does not pay for itself |
| 04 | does a conventional layer-first codebase leave room to improve | 25 of 25 first pass, 1 to 6 files opened, no run leaving its boundary |
| 05 | does that survive a codebase 2.6 times larger | 25 of 25, and files opened did not grow with the codebase |
| 08 | was that ceiling an artefact of over-specified requests | requests cut in half, still 25 of 25 |

The number BPT exists to reduce is files opened per change. Across two codebases at 5,300 and
16,000 lines it was 3, 4, 6, 4, 1 and then 1, 5, 4, 4, 1. It did not move.

**The reason is the finding, and it is worth more than the verdict.** The agent never reads the
repository. It greps for a symbol, gets a path back, and opens that file. Repository size is paid
by the search index, not by the context window. A declared boundary is an answer to a question
the tool already answers for free.

Experiment 08 closed the last objection to this. The requests in 04 and 05 stated every rule
their hidden suites checked, which is a contract in prose handed to the conventional arm at no
cost, and both experiments named that as the likeliest explanation of their own results. Halving
the requests changed nothing. The agent recovered the conventions from the code beside the code
it was editing.

## Clause two: parallel without coordination

| Experiment | What it asked | What came back |
| --- | --- | --- |
| 06 | do uncoordinated patches compose | void, and the design error was ours |
| 07 | do different behaviors sharing a module compose | 34 or 35 of 35, depending on the merge model, and no semantic conflict anywhere |

Thirty five pairs of changes, each made by an agent that had never seen the other's work, put
back together. Every acceptance suite passed on every composed tree. Not once did two changes
turn out each correct alone and wrong together, which is the damage coordination exists to
prevent.

One combination in 35 produced a textual clash, two agents inserting a new view at the same
anchor in one module. That is real, it is the case island ownership would prevent, and it is
also something a person resolves in about thirty seconds.

## So: is BPT useful?

**No, on the evidence, for the codebases and the model tested.**

Not because it is wrong about software. Because the thing it improves is already at the floor
without it. You do not need to build the second arm to know it cannot win a comparison where the
first arm scores 50 of 50 on first attempt and opens between one and six files to do it.

That reasoning is the method this project ended up proving out, and it is the part worth keeping:
**probe the cheap arm before building the expensive one.** Experiment 04 cost 4.08 usd and
cancelled three to five days of migration. Experiment 06 cost nothing and killed a design that
would have been the wrong experiment. In both cases the probe was worth less than a tenth of what
it prevented.

## What survives

**The contract, partially, and not for the reason claimed.** Experiment 08's voided runs are the
sharpest datum in the whole set. With the rules removed from the request, every run still got the
entire business rule right, 16 or 17 of 18 assertions, and failed only on two strings it had to
name on its own. So what a written contract buys is not correctness. It is agreement on arbitrary
names, which matters when two parties must match exactly and does not matter for whether the
change works. Experiment 02 already said the notation should be JSON Schema rather than a bespoke
format, and nothing since has argued otherwise.

**The measurement discipline.** Pre-registration, an equivalence gate against a frozen baseline,
suites proved red before green, negative controls, and reading raw output instead of summary
tables. Every design defect in these eight experiments was found that way, and there were five of
them: a system prompt that silently deleted runs, a fixture that asked the model to guess, a gate
that aged out at a timezone boundary, a control and treatment assigned backwards, and a rule
classified as discoverable that was not.

**The tree has no evidence behind it.** Four experiments gave it a chance to matter and in all
four there was nothing for it to improve.

## What would change this verdict

Stated plainly, because a result with no stated escape route is a belief.

- **A much larger codebase.** 16,000 lines exceeds a 200k token window but is not a monolith.
  Whether search keeps scaling is untested past that.
- **A codebase whose conventions are not legible.** Experiment 08's result rests on the agent
  reading conventions off neighbouring code. In a codebase with no conventions, or contradictory
  ones, a written contract would have something to do. Note that experiment 08 found exactly that
  locally: the two rules it got wrong were the two the codebase was inconsistent about.
- **A weaker or a differently tooled model.** Everything here is Sonnet with `Grep`, `Glob` and
  `Read`. Take the search tool away and the whole argument inverts.
- **Parallelism at volume.** One clash in 35 is small. At a hundred concurrent changes in one
  module it might not be.
- **The repair loop.** Every run here was a single pass with no ability to execute anything.
  `./bpt run` has a three attempt loop, and both arms would need it to be compared fairly.

## What this repository is now

A template for an architecture with no evidence behind its central claim, and a directory of
experiments that says so with the numbers attached. That is a smaller thing than it set out to be
and a more honest one. Anyone can re-run 01, 02 and 03 from what is committed here. Experiments
04 through 08 ran against a private codebase and publish their design, their criteria fixed in
advance, and their prompt hashes, which is weaker and is said plainly in each of them.

If you came here looking for a way to make agents work on large codebases, the measured answer
from this repository is that they already do, and that the tool doing the work is search.
