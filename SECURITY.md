# Security

## What BPT itself runs

The core is small on purpose, and so is its attack surface: `./bpt validate` reads `bpt.config.yaml` and walks the tree with PyYAML's `safe_load`. It executes nothing from your repository and makes no network call.

## What an adapter runs, and why that is the part to think about

BPT's design hands execution to an adapter: an executable named in `bpt.config.yaml` that the core invokes once per hook, per unit. That is a deliberate boundary, and it means:

- **Choosing an adapter is choosing what runs on your machine.** `adapter: <name>` resolves to `adapters/<name>/`, and the core will execute it. Read an adapter before you declare it, exactly as you would read a build plugin.
- **Adapters that drive coding agents deserve extra care.** An adapter's `execute` hook may hand the node's island to an agent with write access and then act on the result. If you write or adopt such an adapter, decide explicitly: which directories it may write, whether it may run shell commands, whether its output merges anywhere automatically, and whether a human reads the diff before it does. BPT's write-boundary rules (an adapter's `execute` writes only inside the node's folders; only `codegen` writes `__generated__/`) exist so those questions have crisp answers, but the core cannot enforce them for you: the adapter is the one holding the file handles.
- **The placeholder shipped here writes files.** `adapters/placeholder/` has a real `scaffold` hook that creates folders and stub files under the roots declared in your config. It is small enough to read in full, and it does nothing else: the other hooks answer with an empty ok.

## Secrets

Nothing in the template reads credentials, and nothing should. A contract is neutral data and a spec describes observable behavior; if either needs a secret to be understood, something has leaked into the wrong file. Keep credentials in your own environment handling, outside `packages/contracts` and outside `bpt.config.yaml`.

## Reporting a vulnerability

Open a GitHub security advisory on the repository, or an issue if the problem is not sensitive. Please include the smallest tree that reproduces it. There is no bounty, and no promised response window: this is a template maintained in the open.
