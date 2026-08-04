# Experiment 07: do different behaviors sharing a module compose?

**This file is the pre-registration. It is committed before the first run.**

## Why this one exists, and what experiment 06 got wrong

Experiment 06 tried to probe the second clause of the hypothesis, "independent changes can run
in parallel without coordination", by composing patches that already existed. It came back void
under its own control clause, and writing up why exposed a design error worth stating plainly.

**The roles were assigned backwards.** BPT's parallelism claim is about behaviors: two different
behaviors are different nodes, they get separate worktrees, and they merge without coordination.
In a layer-first codebase two different behaviors land in the same files. So the pairs that
shared `views.py` were not the control. They were the treatment, and the pairs that shared
nothing were the trivial case.

Experiment 06 registered it the other way around, which is why fifteen clean results on the
interesting pairs bought nothing. Re-reading those fifteen as the treatment now would be
choosing the meaning of a number after seeing it, so they stay void and this experiment
generates its own data.

**A corollary that saved the wrong experiment from being run.** The obvious next move looked
like "write two requests that collide inside one function". That tests nothing. Two changes to
the same function are the same behavior, the same node, and BPT would serialise them too. The
question is only interesting for changes BPT would call independent.

## The design

Two new cells are added to the experiment 05 fixture, chosen so that each is a different
behavior from every other cell, and so that both land in modules other cells already touch.

| Cell | Change | Lands in | prompt sha256 |
| --- | --- | --- | --- |
| `cr6` history summary | a new endpoint aggregating the caller's own download volume | `urls.py`, `views.py` | `cd9dab25c1e071c9` |
| `cr7` download presets | a new endpoint publishing the yt-dlp presets nothing calls today | `urls.py`, `views.py` | `23b264882247ca19` |

Five runs each, Sonnet, same runner and same executor as experiments 04 and 05, each run alone
in its own fresh copy of the same base commit with no knowledge that the others exist. Ten runs,
roughly 3 to 4 usd at experiment 05's rates.

**The treatment is every pair that involves at least one new cell**, so no pair scored in
experiment 06 is reused:

`cr6`+`cr7`, `cr6`+`cr3`, `cr7`+`cr3`, `cr6`+`cr2`, `cr6`+`cr4`, `cr7`+`cr2`, `cr7`+`cr4`

Seven pairs, five run indexes each, 35 combinations. The first three also share `urls.py`, which
is the sharper case: a routing table is a registry that every behavior has to write into, and it
is the classic place where parallel work in a layer-first tree collides.

**The positive control, fixed here rather than added later.** Two runs of the *same* cell, which
are two agents solving the same request: `cr6` run 0 with run 1, `cr6` run 2 with run 3, and the
same two pairings for `cr7`. Four combinations. These must conflict. Experiment 06 needed a
positive control and did not have one registered, and this is that gap closed.

**A combination conflicts** if a patch fails to apply, if the two application orders produce
different trees, or if the composed tree breaks either acceptance suite or the equivalence gate.
Composition, conflict taxonomy and scoring are experiment 06's, unchanged.

## Said in advance, so the result cannot be read as arranged

The two reference implementations for `cr6` and `cr7` were written before this file and they
**compose cleanly**. Each inserts its route next to the route it belongs with rather than at the
end of the list, so they never touch the same lines. Whether independent agents do the same is
exactly what is being measured, and it is not being steered: the requests say what the endpoint
must do and say nothing about where to put the line.

So a clean sweep is a live possibility here, not a surprise, and the criteria below are written
knowing that.

## Decision criteria, fixed in advance

**Ceiling reached, and the parallelism clause has nothing for BPT to improve.** All 35 treatment
combinations compose with no conflict of any kind, and the positive control conflicts. Reading:
agents that never coordinated, making different behaviors that land in the same modules and in
the same routing table, already produce work that merges and stays correct. That puts the second
clause of the bet where the first one already is, and it is the last claim this architecture had.

**Room exists.** Two or more of the 35 conflict. Reading: coordination is needed for changes BPT
would call independent, which is the thing it promises to remove, and there is a case for
building the arm experiment 04 cancelled. That case goes in its own pre-registration naming the
pairs that conflicted.

**Exactly one combination conflicts.** Reported as one instance, no arm built on it, the rule
experiments 05 and 06 both applied.

**The control fails.** If fewer than 3 of the 4 positive control combinations conflict, the
checker has not been shown to detect on this data and the whole result is void, exactly as in
experiment 06, with no reinterpretation afterwards.

## What this still cannot decide

Whether BPT's layout would have prevented a conflict that does appear. This is the conventional
arm alone. If conflicts show up, the next step is the comparison, not the conclusion.

It also models parallelism the way real tooling and BPT itself do: separate worktrees, merged at
the end. Two agents writing to one working tree at the same instant is a different question and
nobody builds that way.

## What is not in this repository, and why

The same constraint as experiments 04, 05 and 06. The prompts, patches, suites and composed
trees are diffs and tests of a private codebase and stay outside. Published here: the design,
the criteria, the prompt hashes, and the table in `RESULTS.md`.
