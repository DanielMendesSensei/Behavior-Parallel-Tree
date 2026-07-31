# Structural consistency checklist

Ten items, fixed before the first run of experiment 03. Each is scored yes or no
against the exemplar node, never against taste. A run's consistency score is the
count of yes answers, out of ten.

They are deliberately mechanical. "Is the code good" is not on the list, because
experiment 03 does not measure quality: it measures whether an agent that cannot
see its siblings produces something shaped like them.

1. **File names.** The files inside `src/` carry the same names as the exemplar's,
   for the same roles.
2. **Entry point.** The behavior is reached through the same entry file and the
   same exported name as the exemplar.
3. **Layering.** The same split between the entry, the domain logic and the
   input and output handling, with nothing collapsed and nothing extra.
4. **Where validation lives.** Input validation happens at the same layer as in
   the exemplar, not one layer in or out.
5. **How the contract is read.** The contract is consumed the same way: same
   import path shape, same materialisation, same use of `__generated__` or its
   absence.
6. **Error shape.** Errors are raised or returned in the exemplar's form, and
   carry the contract's `code` and `category` the way the exemplar does.
7. **Kernel usage.** The same kernel modules are reached for the same purposes,
   and nothing is reimplemented locally that the exemplar takes from the kernel.
8. **Test location and naming.** Tests sit where the exemplar's sit, with the
   same file naming and the same split between scenario and unit.
9. **Test style.** Scenarios are expressed in the exemplar's form, in the same
   given, when, then shape, at the same level of granularity.
10. **No stray abstraction.** No helper, base class, interface or utility module
    appears that the exemplar does not have and the contract does not require.

## How to score without fooling yourself

Score arm A and arm B outputs in one pass, shuffled, without knowing which arm
each came from. The scorer is the same person or model for every output. An item
that turns out to be ambiguous gets rewritten and every output is rescored, and
that fact goes into `RESULTS.md`.
