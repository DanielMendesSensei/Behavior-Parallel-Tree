---
name: The validator is wrong
about: It accepted something it should refuse, or refused something valid
labels: bug
---

**Which way is it wrong.** It accepted a tree that breaks an invariant, or it refused a tree that holds.

**The config that shows it.** The smallest `bpt.config.yaml` that reproduces, plus the files it needs (a contract, a spec, a folder).

**What you ran and what you got.**

```
./bpt validate
```

Paste the output. If it is a traceback rather than a diagnostic message, say so explicitly: a validator that crashes instead of explaining is a separate defect from the check being wrong.

**What you expected instead**, naming the invariant if you know it (there are 7, listed in `docs/RULEBOOK.md`).

**Version.** The commit you are on, plus your Python version.
