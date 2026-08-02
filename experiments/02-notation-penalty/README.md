# Experiment 02: notation penalty

**Pre-registration. Committed before the first run.**

Experiment 01 measured what a model reaches for when nothing constrains it. That is a
measurement of preference. This one measures whether the preference changes what the model
produces, which is a different question and the only one that decides anything. A notation
could be unfamiliar and harmless. Experiment 01 cannot tell the difference. This can.

## What changed from the original plan, and why

The first pre-registration said arm B would rewrite `input` and `output` as JSON Schema.
Experiment 01 made that the wrong first cut, for two reasons it measured. Fourteen of BPT's
twenty three keys are already what a model produces unprompted, so replacing the envelope
would be changing something that is not broken. And in-distribution notation costs between 1.6
and 20 times more characters for the same behavior, so a wholesale swap confounds the
vocabulary question with a verbosity question.

So arm B is now the narrow change, and the wholesale swap becomes arm C, kept because pricing
the verbosity is worth a third of the budget.

## The three arms

All three carry identical information about identical behaviour.

| Arm | What it is |
| --- | --- |
| `arm-a-bpt` | `bpt/v1` exactly as `docs/CONTRACT-FORMAT.md` specifies |
| `arm-b-types` | arm A with only the four invented type tokens replaced: `text` to `string`, `money` to `string`, `list` to `array` |
| `arm-c-jsonschema` | arm A with `input` and `output` as JSON Schema, envelope untouched |

Two judgement calls were needed to make "identical information" true, and both are recorded
here because they are the places where this experiment could be quietly rigged.

**The price rule is in every arm.** `money` is the one BPT type with no in-distribution
equivalent: it does not mean "a number", it means "an exact amount that must not touch binary
floating point". Arms B and C cannot say that with a type token, so a `price-exact` rule was
added to the `rules` block. It was added to arm A as well. Arm A therefore states money
semantics twice and the others once. Without it the experiment would be measuring a deleted
sentence rather than a notation.

**`money` maps to `string`, not `number`.** A decimal string is how an exact amount survives
JSON and a database, and experiment 01's runs used exactly that. Mapping it to `number` would
have handed arms B and C a semantic defect and made arm A win for the wrong reason.

## The two cells

**`implement`.** Given the contract, the specification and a scaffold, write the
implementation. Twelve behavioural scenarios then run against it. The tests are byte identical
in every arm, assert only behaviour, and never look at the notation.

The suite was proved in both directions before the first run: twelve of twelve green against a
reference implementation, and red against the stub and against a file that does not parse. A
suite that has only ever been seen failing proves nothing about the arm it fails.

It deliberately does not assert how `price` is represented, because `Decimal`, `str` and
`float` all survive `Decimal(str(value))` for these amounts. A test that cannot discriminate
should not pretend to. Representation is read out of the code instead.

**`extend`.** Given the contract alone, add an optional minimum price filter and a currency
field. This is the sharpest near-miss test in the whole set, and it is cheap. The model is
handed a file written in a vocabulary and asked to add to it. If it writes `string` into a
file whose every other field says `text`, then the prior beat a document that was open in
front of it. That is what "the near-miss is worse than the novel" means in practice, and
nothing else here measures it directly.

## Baseline variance

Defined before the numbers exist, so it cannot be defined around them: the within-arm spread
is the range between the best and the worst of an arm's five runs on the primary metric, and
the baseline is the widest such range across the three arms. A difference between arm means
counts only when it exceeds that baseline. Anything smaller is reported as noise.

## One model, and no fishing afterwards

Sonnet only. It showed the wider spread in experiment 01, so it is the more likely to reveal
an effect, and one model keeps the sweep inside a few dollars.

Pre-registered so this cannot turn into a fishing licence: **if the gap between arms falls
inside the baseline, Opus does not get added afterwards to hunt for a difference.** The result
is "could not measure", and it gets written down that way.

## Decision criteria, fixed in advance

On `implement`, the primary metric is the mean number of the twelve scenarios passed, with the
full-pass rate and the token cost as secondaries.

- **Arm B beats arm A by more than the baseline:** the four invented type names cost measurable
  accuracy, not just familiarity. Replace them, and the case is closed with evidence rather
  than with a preference.
- **Arm C beats arm B by more than the baseline:** full JSON Schema earns its verbosity, and
  the contract format moves further than the type tokens.
- **Arm C ties arm B on accuracy and loses on tokens:** keep BPT's shorthand and change only
  the type names. This is what the audit now expects, which is exactly why it is written down
  before the run.
- **All three inside the baseline:** could not measure. The type change would then rest on
  experiment 01 alone, where it is justified by costing nothing rather than by winning
  anything, and that weaker claim is the one that gets made.

On `extend`, the metric is the conformance rate: does the added field use the vocabulary of
the file it was added to.

- **Arm A conformance below 60% while arms B and C stay high:** the near-miss claim is
  confirmed on its own terms, in the exact failure mode the talk described.
- **Arm A conformance high:** the model follows the document in front of it, the near-miss
  worry is overstated for contracts, and that goes in the root README because it is a result
  in BPT's favour.

## Running

```bash
python3 experiments/lib/runner.py --plan experiments/02-notation-penalty/plan.yaml --budget-usd 6
```
