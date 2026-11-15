---
type: module
title: Vault validator
description: Standard-library Python script that checks a vault's frontmatter, links, sources and staleness.
aliases: [validate.py]
sources:
  - skills/obsidian-graph-doc/scripts/validate.py
depends_on:
  - "[[note-format]]"
  - "[[note-templates]]"
---

# Vault validator

A single script that reads every Markdown file under a vault folder, skipping directories whose name starts with `.`, and reports errors and warnings. It only reports; it never edits a note. It is the one deterministic piece of the skill.

## Key files

| Path | Role |
|---|---|
| `skills/obsidian-graph-doc/scripts/validate.py` | The whole checker |

## Checks

- **Errors**: unknown or missing `type`; missing `title` or `description`; an unquoted wikilink in frontmatter; a link entry that is not a wikilink; a wikilink under a key that is not a link key; more than one `part_of`; a link, in frontmatter or body, that resolves to no note; a frontmatter link missing from the body; a note linking to itself; duplicate note names; missing `sources` on a type that needs them; a `sources` path matching no file; not exactly one `index` and one `overview`.
- **Warnings**: stale notes; orphans (any note but the `index` that nothing links to); more than 20 pending items.

## Public surface

- `python3 validate.py [VAULT_DIR]`, default `docs`.
- Exit code 0 with no errors (warnings allowed), 1 with errors, 2 for bad usage.
- Output: one `ERROR`, `WARN` or `PENDING` line per item, then a count line (`N notes, N errors, N warnings, N pending cross-check`).

## Dependencies

- [[note-format]]: the allowed types, link keys and required keys are hard-coded from it.
- [[note-templates]]: the pending check reads the ledger's `last_cross_check` key and `## Entries` heading, which the ledger template defines.

It also shells out to `git` (for the repo root, the staleness check and the pending check). Without git, or outside a git repo, those checks are skipped and the rest still runs.

## Invariants and gotchas

- `TYPES`, `LINK_KEYS` and `NEEDS_SOURCES` at the top of the script must match the tables in `SKILL.md`. Nothing enforces this.
- Only files whose frontmatter has a `type` key are checked. Other Markdown files in the vault are otherwise ignored, but they count as link targets and take part in the duplicate-name check.
- The frontmatter parser handles only scalars and flat lists, not general YAML.
- Wikilinks inside code fences and inline code are ignored.
- Staleness is derived from git, not from a field: the script finds the note file's last commit and runs `git diff --name-only <that commit> -- <sources>` against the working tree. Uncommitted source edits count. A brand-new untracked file matching a glob does not.
- A note that is not committed yet, or has pending edits, is never reported stale.
- Any commit to a note makes it fresh, including a typo fix. The check cannot tell whether the edit addressed the source change.
- Stale notes and orphans are warnings; they do not fail the run.
- If `pending-cross-check.md` exists in the vault, the script prints one `PENDING` line per file changed outside the vault since its `last_cross_check` commit, and one per list item (a line starting `- `) anywhere after the `## Entries` heading. More than `PENDING_LIMIT` (20) items adds a warning. Untracked new files are not counted. If `last_cross_check` is empty or not a known commit, it warns and lists no changed files.

## Notes
