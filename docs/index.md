---
type: index
title: obsidian-graph-doc-skill docs
description: Entry point to the documentation vault for obsidian-graph-doc-skill.
---

# obsidian-graph-doc-skill docs

Start with [[overview]]. Each note covers one unit; its frontmatter lists what it is part of and what it depends on. To find what depends on a unit, open its backlinks in Obsidian or search this folder for `[[its-note-name`.

If a note disagrees with the code, the code is right.

## Modules

- [[skill-instructions]]: The SKILL.md an agent follows to generate, validate or cross-check a docs vault for a codebase.
- [[note-templates]]: Starter files for module and index notes that the skill copies and fills in.
- [[vault-validator]]: Standard-library Python script that checks a vault's frontmatter, links, sources and staleness.

## Data

- [[note-format]]: The frontmatter keys, note types, link types and naming rules every vault note follows.

## External

- [[obsidian]]: The note-taking app whose vault conventions the generated docs must satisfy.

## Decisions

- [[minimal-skill-scope]]: The first version is model-only instructions with templates and one checker script, not a toolchain.
