---
type: decision
title: Keep the skill to one SKILL.md plus small helpers
description: The first version is model-only instructions with templates and one checker script, not a toolchain.
about:
  - "[[skill-instructions]]"
---

# Keep the skill to one SKILL.md plus small helpers

**Status:** accepted, 2026-11-15, by the project owner.

## Context

Five research reports proposed a larger design: a bundled dependency extractor in tiers, a committed JSON graph with per-edge provenance, content hashes, generated-region markers, plugin packaging, hooks and evals. See [[02-prior-art]], [[04-information-architecture]] and [[05-extraction-and-graph-tooling]].

## Decision

Recorded from the owner's answers:

- No extraction scripts: the model reads the code and writes the edges.
- `init` and `validate` live in the skill. Updating is opt-in, by adding an instruction to the target project's `CLAUDE.md`.
- "This should be pretty much a simple skill.md maybe with a few template file or python snippets."
- Wikilinks everywhere, including note bodies.

## Consequences

- Every dependency edge is the model's reading of the code; nothing deterministic backs it.
- Graph query and compare are not built. The flat frontmatter leaves room to add them.
- The only script is [[vault-validator]].

## Related

- About [[skill-instructions]].

## Notes
