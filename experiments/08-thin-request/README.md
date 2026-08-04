# Experiment 08: how much of the ceiling was the specification?

**This file is the pre-registration. It is committed before the first run.**

## Why this one exists

Experiments 04 and 05 both found the conventional arm at the ceiling, and both wrote down the
same caveat before their runs rather than after:

> The requests are explicit on purpose. Every rule the hidden suite checks is stated in the
> request. That is a small contract written in prose, handed to the conventional arm for free,
> and it flatters that arm.

That caveat has been named three times and measured zero times. While it stands, a fair reader
can say the ceiling is an artefact of handing the answer over with the question, and they would
have a point. This experiment removes it.

It is also the last cheap thing left. The context clause of the hypothesis has been probed three
times and the parallelism clause twice, all on the conventional arm, and all came back with
little or nothing for BPT to improve. What has never been separated is how much of that was the
layout doing nothing and how much was the prose specification doing everything.

## The design, and the one variable

**Only the prompt changes.** The acceptance suites are byte for byte the ones experiments 05 and
07 used. The reference implementations, the equivalence gate, the frozen baseline, the runner,
the executor, the tool set, the model and N are all unchanged. So the result is directly
comparable to a number that already exists: these same five cells scored 25 of 25 with the full
requests.

Five cells, five runs each, 25 runs, roughly 8 usd.

| Cell | full prompt | thin prompt | thin sha256 |
| --- | --- | --- | --- |
| `cr1` derived field | 169 words | 73 | `6438416ed8708f44` |
| `cr2` new rule | 332 words | 160 | `237e58927b6e0115` |
| `cr3` new behavior | 234 words | 105 | `b432f38b976d3b06` |
| `cr6` history summary | 196 words | 126 | `cb0bbc09b8f4e066` |
| `cr7` download presets | 197 words | 103 | `8bfd6509adc837bf` |

`cr4` and `cr5` are not in this sweep. Almost every rule they state is definitional rather than
conventional, so thinning them would leave nothing to remove or would leave the model guessing.
That choice is made here, before any run, and the two cells stay out of the comparison entirely
rather than being dropped later if they misbehave.

## The rule that keeps this from repeating experiment 03

Experiment 03 lost 30 runs to a fixture that asked the model to guess, and the guess, not the
arm, decided the result. The difference between a fair thin request and that mistake is whether
the removed rule is **discoverable** or merely **unstated**.

So every rule was classified before removal:

- **definitional**: it says what the feature is. Removing it makes the model guess an arbitrary
  choice. These stay in the prompt. Exact messages, formulas, endpoint paths, field names and
  the specific reason strings the suites assert are all definitional and all remain.
- **conventional**: it says how this codebase does things, and the answer is visible in code the
  agent can read. These are removed, and the suites keep checking them.

What was removed, and where the convention is legible:

| Cell | removed | visible at |
| --- | --- | --- |
| `cr1` | field is null when its inputs are missing or zero; key always present; nothing existing changes | `get_download_speed_formatted` and `get_eta_formatted` in `serializers.py`, both ending in `return None` when their source is falsy |
| `cr2` | the `details` entry shape `{'passed': bool, 'message': str}`; registering the new reason in the model's choices; the four older limits keeping their behaviour | the four sibling entries built in `check_all_limits`, and `BlockedAttempt.BLOCK_REASON_CHOICES` |
| `cr3` | open to anonymous; the success envelope; the 503 when the service is unavailable; the neighbouring endpoints unchanged | `QualityProfilesView` immediately above it, which is `AllowAny`, returns the envelope and has the 503 branch |
| `cr6` | requires authentication; the success envelope; only the caller's own rows count | `DownloadHistoryView.permission_classes = [IsAuthenticated]`, and `download_stats` filtering `user=request.user` |
| `cr7` | open to anonymous; the success envelope; the option dictionaries published as they are | `QualityProfilesView` again, the closest neighbour and the same shape of endpoint |

The success envelope `{'success': True, 'data': ...}` appears 21 times in the same `views.py` the
agent is editing, so calling it discoverable is a statement about the file, not a hope.

**If a cell fails on a rule this table called discoverable and the convention turns out not to be
legible from the code, that cell is void**, its runs are kept with the reason, and the request is
repaired. That is the experiment 03 rule, applied in advance to the failure mode this design is
most likely to hit.

## Decision criteria, fixed in advance

The comparison point is 25 of 25, which is what these five cells scored with the full requests.

**The specification was not doing the work.** First-attempt success of at least 23 of 25, no cell
below 4 of 5. Reading: the ceilings in 04 and 05 survive their own main caveat. The conventional
arm infers this codebase's conventions from the codebase, and the prose contract was not what was
carrying it. That closes the last open question about those two results, and it also says BPT's
contract has nothing to add here either, since the thing a contract would supply is exactly what
was removed.

**The specification was doing the work.** Success of 18 of 25 or worse, or any single cell at 2 of
5 or worse. Reading: a precise contract is what produced the ceiling, not the agent and not the
layout. That is a result for the contract half of BPT, and for any spec-first approach including
ones with no tree in them. It is not a result for the tree, and the write up must not let it be
read as one.

**Anything between.** Success of 19 to 22 of 25, or one cell at exactly 3 of 5. Reported as
partial with the per-cell numbers and the failures described, and no claim is made in either
direction. A middling number is a middling result and dressing it up is how favourite hypotheses
survive.

**One model, and no fishing.** Sonnet, as in 02, 03, 04, 05 and 07, and the same ban on swapping
in a stronger model afterwards to hunt for a different answer.

## What this cannot decide

Whether BPT's machine-readable contract beats prose. This experiment has two arms only in the
sense that a previous experiment already ran the full-prompt one. Both are prose. A comparison
between prose and `contract.yaml` is experiment 02's question and 02 already answered it: the
bespoke notation did not pay for itself against JSON Schema.

It also cannot say anything about the tree. Nothing in this design distinguishes a layout from a
specification, and the write up has to keep saying so whichever way the number falls.

## What is not in this repository, and why

The same constraint as 04, 05, 06 and 07. The prompts name a private codebase, so they stay
outside and their hashes are published here instead.
