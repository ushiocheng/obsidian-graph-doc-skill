---
type: module
title: Vault validator
description: Standard-library Python script that checks a vault's frontmatter, links, sources and staleness.
aliases: [validate.py]
sources:
  - skills/obsidian-graph-doc/scripts/validate.py
depends_on:
  - "[[note-format]]"
verified_commit: uncommitted
---

# Vault validator

A single script that reads every Markdown file under a vault folder and reports errors and warnings. It only reports; it never edits a note. It is the one deterministic piece of the skill.

## Key files

| Path | Role |
|---|---|
| `skills/obsidian-graph-doc/scripts/validate.py` | The whole checker |

## Public surface

- `python3 validate.py [VAULT_DIR]`, default `docs`.
- Exit code 0 with no errors (warnings allowed), 1 with errors, 2 for bad usage.
- Output: one `ERROR` or `WARN` line per finding, then a count line.

## Dependencies

- [[note-format]]: the allowed types, link keys and required keys are hard-coded from it.

It also shells out to `git` (for the repo root and the staleness check) and still runs without it.

## Invariants and gotchas

- `TYPES`, `LINK_KEYS` and `NEEDS_SOURCES` at the top of the script must match the tables in `SKILL.md`. Nothing enforces this.
- Only files whose frontmatter has a `type` key are checked. Other Markdown files in the vault are ignored but count as link targets.
- The frontmatter parser handles only scalars and flat lists, not general YAML.
- Wikilinks inside code fences and inline code are ignored.
- Staleness is `git diff --name-only <verified_commit> -- <sources>` against the working tree, so uncommitted edits count. A brand-new untracked file matching a glob does not.
- Stale notes, orphans and `uncommitted` notes are warnings; they do not fail the run.

## Notes
