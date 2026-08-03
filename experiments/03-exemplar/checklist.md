# Structural consistency checklist

Ten items, scored yes or no against the exemplar, never against taste. A run's
score is the count of yes answers over the count of items that apply to it.

They are deliberately mechanical. "Is the code good" is not on the list, because
experiment 03 does not measure quality. It measures whether an agent that cannot
see its siblings writes something shaped like them.

## Revision 2, and why

Revision 1 was written before the fixture existed and assumed a node made of
several files: entry point file, layers, a tests folder, a `__generated__`
folder. The fixture is one module, because the point of the experiment is the
island rule and not the file tree, and a single artifact keeps everything except
the exemplar identical between the arms. Nine of the ten items had no referent.

This revision is committed before the first run, and the reason is here rather
than in a commit message so that anyone reading the result sees what was
measured and what was not.

## The items

1. **Module docstring.** Present, one line, in the exemplar's form: the behaviour
   id, a colon, and what it returns.
2. **Import shape.** `from kernel import ...` naming what it uses, as the
   exemplar does. Not `import kernel`, not a wildcard.
3. **Session first.** `require_session(session)` is the first statement of the
   public function, before any input is looked at.
4. **Validation isolated.** Input validation lives in a private helper, not
   inline in the public function. Does not apply to a behaviour whose contract
   declares no constraint to check beyond presence.
5. **Helper naming.** Private helpers start with an underscore and are named for
   what they return, the way `_validated_input` and `_matching` are. Does not
   apply when the answer has no helper and item 4 did not apply either.
6. **Contract literals as constants.** Any literal the contract fixes (a default,
   a bound, a limit) appears as an UPPER_CASE module constant rather than inline.
   Does not apply when the contract fixes none.
7. **Errors.** Every failure path raises `AppError` with the contract's code.
   Nothing raises a bare exception, and no code appears that the contract does
   not declare.
8. **Output built inline.** The return is a dict literal assembled in the public
   function with exactly the contract's fields, not accumulated into a variable
   somewhere else and returned.
9. **Same idioms for the rules.** Ordering with `sorted(..., key=...)`, case
   insensitivity with `.casefold()`, filtering with a comprehension, as in the
   exemplar. Only the idioms the behaviour actually needs count.
10. **No stray abstraction.** No class, no dataclass, no module level mutable
    state, no helper that exists for a case the contract does not describe.

## How to score without fooling yourself

Score every answer in one pass, shuffled, without knowing which arm it came
from. The same scorer does all of them. An item that turns out to be ambiguous
gets rewritten and everything is scored again, and that fact goes into
`RESULTS.md`.
