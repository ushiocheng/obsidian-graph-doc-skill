---
type: data-model
title: Note format
description: The frontmatter keys, note types, link types and naming rules every vault note follows.
aliases: [frontmatter schema, link types]
reviewed: 2026-11-15
sources:
  - skills/obsidian-graph-doc/SKILL.md
  - skills/obsidian-graph-doc/scripts/validate.py
depends_on:
  - "[[obsidian]]"
---

# Note format

The contract between the skill, the validator and anything built on the vault later. A note is a Markdown file with flat YAML frontmatter and a short body.

## Fields

| Key | Meaning |
|---|---|
| `type` | One of nine: `index`, `overview`, `module`, `interface`, `data-model`, `flow`, `external`, `concept`, `decision` |
| `title`, `description` | Required. `description` is one sentence and feeds the index |
| `aliases` | Other names for the unit |
| `sources` | Repo-root-relative paths or globs the note describes; required for `module`, `interface`, `data-model`, `flow` |
| `reviewed` | Optional date the note was last checked against its sources and left unchanged |
| `part_of`, `depends_on`, `implements`, `about`, `supersedes`, `see_also` | Typed links, as lists of quoted wikilinks |

## Invariants

- Frontmatter is flat: scalars and lists only.
- Each link is stored on one side. The reverse direction is found by backlinks or search.
- Every frontmatter link also appears as a body wikilink, because [[obsidian]] does not resolve links written in
  frontmatter: only body links reach its graph and backlinks.
- Note file names are unique across the vault, ignoring case, so bare wikilinks resolve.
- `part_of` has at most one target. `see_also` has at most five, which `SKILL.md` states but the validator does not
  enforce. No link keys other than the six above are allowed.
- Staleness is not stored. A note is stale when a file in `sources` has changed, committed or not, since the note file's last commit. An earlier `verified_commit` field was dropped for this (commit `8e66774`): a note cannot hold the hash of the commit that contains it, so every update needed a follow-up commit. The commit message records the change, not that reason.

## Dependencies

- [[obsidian]]: the format is shaped by what Obsidian's properties and link resolution support.

## Readers and writers

- Defined in prose by [[skill-instructions]].
- Instantiated by [[note-templates]].
- Enforced by [[vault-validator]].

## Gotchas

- The format is defined twice, in `SKILL.md` and in the validator's constants. Change both together.
- Wikilinks were chosen for body links too, so links are not clickable when the files are viewed on GitHub.

## Notes
