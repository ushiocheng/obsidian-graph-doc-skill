---
type: module
title: Note templates
description: Starter files for module and index notes that the skill copies and fills in.
sources:
  - skills/obsidian-graph-doc/templates/*.md
depends_on:
  - "[[note-format]]"
verified_commit: a43459f
---

# Note templates

Two Markdown skeletons with placeholder text in angle brackets. They give generated notes a consistent section order. They are not a schema: nothing checks that a note keeps the template's sections.

## Key files

| Path | Role |
|---|---|
| `skills/obsidian-graph-doc/templates/module.md` | Module note: Key files, Public surface, Dependencies, Related, Invariants and gotchas, Notes |
| `skills/obsidian-graph-doc/templates/index.md` | Index note: one list section per note type |

## Public surface

Read by an agent following [[skill-instructions]]. Other note types reuse the module template's frontmatter with sections that fit the type.

## Dependencies

- [[note-format]]: the templates are instances of it and must use only its keys.

## Invariants and gotchas

- The templates contain placeholder wikilinks such as `[[<note>]]`. They live outside any vault, so they are never validated; a filled-in note must not keep one.
- The `## Notes` section at the end of the module template is reserved for human-written text.

## Notes
