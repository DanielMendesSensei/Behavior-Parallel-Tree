---
name: The protocol needs something
about: Your adapter cannot do its job with what the envelope or the hooks give it
labels: protocol
---

**What your adapter is trying to do**, and for which stack.

**Which hook**, and what the envelope gives you today that is not enough. The hooks and the envelope are in `docs/ADAPTER.md`.

**What you had to do instead.** Reading a file the envelope did not name, inferring a path by convention, calling out to the repo: say which, because the workaround shows where the protocol leaks.

**The smallest addition that would fix it.** A field, a hook, a guarantee. Proposals that keep the core stack-agnostic land faster: if the addition would make the core know a language or a package manager, it belongs in the adapter, and the interesting question becomes what the core has to hand over so the adapter can do it.
