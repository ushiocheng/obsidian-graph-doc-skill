---
type: external
title: Obsidian
description: The note-taking app whose vault conventions the generated docs must satisfy.
---

# Obsidian

The generated `docs/` folder must open as an Obsidian vault with no plugins installed. The skill ships no Obsidian code and never calls the app; Obsidian only constrains the file format.

## What we rely on

- A folder of Markdown files is a vault.
- YAML frontmatter is shown as properties.
- `[[name]]` in a note body resolves to the note with that file name anywhere in the vault.

## Constraints it imposes

- Properties cannot be nested, so frontmatter stays flat.
- Links in frontmatter must be quoted, and are not resolved without a plugin (stated by the project owner; the research could not confirm graph-view behaviour either way). This is why every typed link is repeated in the body.
- The core graph view has no link types: no edge labels or filtering by relation.
- Two notes with the same file name make a bare wikilink ambiguous.
- GitHub does not render wikilinks in repository files.

## Related

- Shapes [[note-format]].
- Background: [[01-obsidian-vault-format]].

## Notes
