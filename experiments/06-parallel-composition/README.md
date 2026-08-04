# Experiment 06: do two uncoordinated changes compose?

**This file is the pre-registration. It is committed before the first combination is scored.**

## Why this one exists

The hypothesis in the root README has two clauses. Experiments 02, 04 and 05 all attacked the
first one, less context per change, and all three came back saying there was nothing there for
BPT to improve. The second clause, "independent changes can run in parallel without
coordination", has never been tested at all. Five experiments in, it is the only claim left
that could still change the answer about this architecture.

So it gets the same treatment the first clause got in experiment 04: probe the cheap arm before
building the expensive one. Run the conventional side alone and see whether it leaves any room.

## The trick that makes this free

Experiment 05 recorded 25 patches. Every one was produced by an agent working in its own fresh
copy of the same base commit, with no knowledge that the other runs existed. That is already
what "independent changes in parallel without coordination" means. The parallel work has been
done and paid for, and nobody ever tried to put it back together.

So this experiment fires no runs. It takes patches that already exist and composes them. It
costs no tokens, and because nothing is re-rolled there is no way to fish for a better draw.

## The design

**A combination** is one patch from cell A and one patch from cell B, both from run index `i`,
applied to a clean copy of the frozen base. Pairing by index is arbitrary, and it is fixed here
in advance so it cannot be chosen later.

**Six pairs, three of each kind, decided by what the runs actually touched rather than by what
the boundaries predicted:**

| Kind | Pairs | Files in common |
| --- | --- | --- |
| disjoint | `cr1`+`cr2`, `cr1`+`cr3`, `cr1`+`cr4` | none |
| overlapping | `cr2`+`cr3`, `cr2`+`cr4`, `cr3`+`cr4` | `views.py`, and for `cr2`+`cr4` also `rate_limit_service.py` |

Five run indexes per pair, so 15 disjoint combinations and 15 overlapping ones.

`cr5` is excluded. Its runs start from a repository with an injected bug applied, so composing
them would be composing against a different starting state than every other cell. Every pair
`cr5` takes part in happens to be disjoint, so including it would have loaded the disjoint side
and unbalanced the design.

**A combination conflicts** if any of three things happens, and which one is recorded:

1. **textual**: one of the two patches does not apply.
2. **order dependent**: both orders apply, A then B and B then A, but the two resulting trees
   are not identical.
3. **semantic**: the composed tree is fine textually, but one of the two acceptance suites fails
   on it, or the equivalence gate breaks. This is the interesting one. It is the case where two
   changes are each correct alone and wrong together, which is exactly what coordination exists
   to prevent.

Both acceptance suites run against the composed tree, so a change that quietly undoes the other
is caught rather than assumed away.

## Decision criteria, fixed in advance

**Ceiling reached, and the parallelism clause has nothing for BPT to improve.** All 15 disjoint
combinations compose with no conflict of any of the three kinds. Reading: two agents that never
coordinated, working on surfaces that do not overlap, already produce work that merges and stays
correct. That would put the second clause of the bet where the first one already is, and it is
the result that goes in the root README.

**Room exists.** Two or more of the 15 disjoint combinations conflict. Reading: coordination is
needed even when surfaces do not overlap, which is the thing BPT claims to remove. That is a
case for building the arm experiment 04 cancelled, under its own pre-registration.

**Exactly one disjoint combination conflicts.** Reported as one instance and no arm is built on
it, the same rule experiment 05 applied to a single discriminating cell.

**The control that decides whether any of the above means anything.** The 15 overlapping
combinations exist to prove the detector can detect. If fewer than 3 of them conflict, then this
instrument has never been seen finding a conflict, and a clean disjoint result would be
indistinguishable from a broken checker. In that case the disjoint result is **void**, reported
as an instrument failure rather than as a ceiling, and the probe is redesigned with a pair built
to collide inside the same function rather than merely inside the same file.

That last clause is written here because it is the likely one. Agents edit at the granularity of
a function, not a file, and two changes to different functions in one module may well compose
without trouble. If that is what comes back, the honest reading is that "same file" was the
wrong proxy for "same behavior", and the next probe has to cost tokens.

## What this cannot decide

Whether BPT's islands would turn an overlapping pair into a disjoint one. That is a question
about layout, and answering it needs the arm experiment 04 cancelled. This probe can only say
whether there is anything left to win on the disjoint case.

It also says nothing about agents running literally at the same wall clock moment against shared
state. The model here is the one real tooling uses, and the one BPT itself prescribes: separate
worktrees, merged at the end.

## What is not in this repository, and why

The same constraint as experiments 04 and 05. The patches are diffs of a private codebase, so
they stay outside this repository along with the acceptance suites and the composed trees. What
is published is the design, the criteria above, and the table in `RESULTS.md`.
