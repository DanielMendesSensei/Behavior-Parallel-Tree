**What changes, in one sentence.**

**Which part of BPT this touches.** The convention, a format, the validator, the docs, an adapter, or the schema.

**Checks.**

- [ ] `./bpt check` is green (the tree validates, the gate still turns red on the refusal cases, and no doc cites a path that does not exist)
- [ ] The two example nodes (`product.list`, `product.detail`) still work: they are the first thing a newcomer reads
- [ ] Nothing in `tools/bpt/` or `bpt.config.yaml` learned about a language, framework, package manager or vendor (that knowledge belongs in an adapter)

**If you changed the validator:** the config that trips the new check, and the message a person reads when it does.

**If you changed a format:** the example in the doc and the shipped file under `packages/contracts/` now agree. They are meant to be the same shape, so a reader can copy either one.

**If you changed the schema (`bpt/v1`):** what it accepts that it did not, or refuses that it used to accept; what an existing clone sees when it runs the new validator; and the `CHANGELOG.md` entry.
