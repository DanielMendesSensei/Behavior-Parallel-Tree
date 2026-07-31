# Results

**Status: no runs yet.** This file exists so that the pre-registration in
`README.md` can be committed before any data is produced, and so that `git log`
carries the proof of that order. Anything written below before a `runs/`
directory has content is a placeholder, not a finding.

## How to read this file

For each experiment, three things get written, in this order and no other:

1. What was run: model, date, run count, and the cost.
2. The numbers, copied from `score.py` without editing.
3. Which pre-registered criterion the numbers hit, named exactly as it is written
   in `README.md`, including when the criterion hit is the one that contradicts
   this repository's own audit of itself.

A finding that surprises the person who ran it is worth more than one that does
not, and it is the one most likely to get quietly softened. If that happens, the
raw JSONL in each `runs/` directory is the appeal court.

## Experiment 01: hallucination probe

Not run yet.

Contamination check (rule 8 of the pre-registration): not run yet.

## Experiment 02: notation penalty

Not run yet. Blocked on experiment 01, which decides whether this experiment is a
discovery or a confirmation.

Baseline variance: not measured yet.

## Experiment 03: island with and without an exemplar

Not run yet.

Baseline variance: not measured yet.

## What these results do not decide

- Nothing about parallelism. Waves and the executing half are throughput, not
  generation quality, and no experiment here touches them.
- Nothing about whether BPT is worth adopting in any specific product. These
  measure the architecture's claims, not a migration.
- Nothing permanent. Every number here is attached to a model and a date, because
  the distribution moves. Re-running the probe against a newer model is the
  intended use.
