#!/usr/bin/env python3
"""Assert that every repository path the docs cite actually exists.

A template teaches by pointing: "the contract lives in
packages/contracts/product/list/contract.yaml". The moment a path in prose
stops matching the tree, the docs teach a lie and the person who trusted them
loses an afternoon. This check is cheap, and it exists because that drift was
real here: docs kept citing a side and an example node after both had been
renamed away.

What it deliberately does NOT flag, so that it stays trustworthy enough to
gate on:

- bare filenames used as nouns ("the `spec.md` sits next to it");
- links between docs (`MIGRATION.md` inside docs/ resolves doc-relative);
- the schema string (`bpt/v1`), which is a version, not a file;
- paths for behaviors that are NOT declared in bpt.config.yaml, and paths
  under `_flows/`. Those are illustrative by definition: the docs teach the
  advanced forms with invented ids (`catalog.filter`, `checkout.pay`), and a
  path for an undeclared node cannot be a claim about this tree;
- anything that does not start at a real entry of the repository root. A doc
  writing `src/`, `kernel/pricing` or `product/list` is naming a form or a
  structure, not asserting a location. A doc writing
  `packages/contracts/product/list/contract.yaml` or `apps/frontend/behaviors`
  IS asserting one, and that is what this check gates on.

Usage:
    python3 tools/bpt/check_docs.py [root]

Exit 0 when every cited path exists, 1 with the list of misses otherwise.
Development tooling, stdlib only, not the app's stack.
"""
import os
import re
import sys

BACKTICKED = re.compile(r"`([^`\n]+)`")
EXTENSIONS = (".md", ".py", ".yaml", ".yml", ".sh", ".json", ".txt")
SKIP_PREFIXES = ("http://", "https://", "./bpt", "bpt ", "-", "$", "~", "<")
SCHEMA = re.compile(r"^bpt/v\d+$")


def load_declared_domains(root):
    """Domains of the nodes actually declared in bpt.config.yaml.

    Read with a deliberately dumb line scan instead of PyYAML: this check has
    to run with nothing installed, which is the whole point of gating on it.
    """
    domains = set()
    config = os.path.join(root, "bpt.config.yaml")
    if not os.path.exists(config):
        return domains
    with open(config, encoding="utf-8") as f:
        for line in f:
            m = re.search(r"id:\s*([a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+)", line)
            if m:
                domains.add(m.group(1).split(".")[0])
    return domains


def is_illustrative(token, declared_domains):
    """A path about a node this project does not declare is an example."""
    if "/_flows/" in token or token.startswith("_flows/"):
        return True
    parts = [p for p in token.split("/") if p]
    for anchor in ("contracts", "behaviors"):
        if anchor in parts:
            i = parts.index(anchor)
            if i + 1 < len(parts):
                return parts[i + 1] not in declared_domains
    return False


def looks_like_path(token):
    if any(token.startswith(p) for p in SKIP_PREFIXES):
        return False
    if any(c in token for c in " \t*?<>|"):
        return False
    if token.startswith("/"):
        return False  # absolute paths are never repository-relative
    if SCHEMA.match(token):
        return False
    return "/" in token or token.endswith(EXTENSIONS)


def cited_paths(text):
    for token in BACKTICKED.findall(text):
        token = token.strip().rstrip(".,;:)")
        if looks_like_path(token):
            yield token


def docs_files(root):
    for name in sorted(os.listdir(root)):
        if name.endswith(".md"):
            yield os.path.join(root, name)
    docs = os.path.join(root, "docs")
    if os.path.isdir(docs):
        for name in sorted(os.listdir(docs)):
            if name.endswith(".md"):
                yield os.path.join(docs, name)


def resolves(root, doc_path, token):
    """True when the token names something real, root- or doc-relative."""
    target = token.rstrip("/")
    if os.path.exists(os.path.join(root, target)):
        return True
    return os.path.exists(os.path.join(os.path.dirname(doc_path), target))


def main(argv):
    root = os.path.abspath(argv[1]) if len(argv) > 1 else os.getcwd()
    declared = load_declared_domains(root)
    misses = []
    checked = 0
    skipped = 0

    root_entries = set(os.listdir(root))

    for doc_path in docs_files(root):
        with open(doc_path, encoding="utf-8") as f:
            text = f.read()
        for token in cited_paths(text):
            if resolves(root, doc_path, token):
                checked += 1
                continue
            if is_illustrative(token, declared):
                skipped += 1
                continue
            # Not a claim about this repository unless it starts at the root.
            if token.split("/")[0] not in root_entries:
                skipped += 1
                continue
            checked += 1
            misses.append((os.path.relpath(doc_path, root), token))

    if misses:
        print("docs cite paths that do not exist:")
        for doc, token in sorted(set(misses)):
            print("  %s -> %s" % (doc, token))
        print(
            "\nfailed: %d missing of %d checked paths (%d illustrative, not checked)"
            % (len(misses), checked, skipped)
        )
        return 1
    print(
        "ok: %d paths cited by the docs all exist (%d illustrative, not checked)"
        % (checked, skipped)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
