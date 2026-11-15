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

- The Properties editor cannot show or edit nested properties, so frontmatter stays flat.
- Links in frontmatter must be quoted. Whether core Obsidian resolves them is disputed: [[01-obsidian-vault-format]] found documentation that they appear in backlinks and Bases, with only indirect evidence for the graph view, while the project owner, who checked a vault in the app, states they do not resolve without a plugin. Nobody has settled it with a controlled test. The format sidesteps the question by repeating every typed link in the body.
- The core graph view has no link types: no edge labels or filtering by relation.
- Two notes with the same file name make a bare wikilink ambiguous.
- GitHub does not render wikilinks in repository files.
- Opening a folder as a vault creates `.obsidian/` inside it, including `workspace.json` (personal window and tab state). This repo ignores `docs/.obsidian/` in `.gitignore`, and the skill adds the same entry to repos it documents. A `git add -A` picks the folder up; that happened here once and was caught before pushing (the commit was amended, so history does not show it).

## Related

- Shapes [[note-format]].
- Background: [[01-obsidian-vault-format]].

## Notes
