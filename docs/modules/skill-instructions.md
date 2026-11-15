---
type: module
title: Skill instructions
description: The SKILL.md an agent follows to generate or validate a docs vault for a codebase.
aliases: [SKILL.md, obsidian-graph-doc]
sources:
  - skills/obsidian-graph-doc/SKILL.md
depends_on:
  - "[[note-format]]"
  - "[[note-templates]]"
  - "[[vault-validator]]"
---

# Skill instructions

The whole skill is this one file of prose: an agent loads it and follows it. It defines two modes, `init` (survey a repo and write the vault) and `validate` (check a vault and repair it). It is not responsible for keeping a vault current; that is handed to the target project as an opt-in block for its `CLAUDE.md` or `AGENTS.md`.

## Key files

| Path | Role |
|---|---|
| `skills/obsidian-graph-doc/SKILL.md` | Frontmatter (`name`, `description`) plus all instructions |

## Public surface

- **Trigger**: the `description` field decides when an agent loads the skill.
- **init**: survey, plan notes, find edges, write leaf notes first and the index last, validate, report, offer follow-ups.
- **validate**: run the checker, then fix errors, refresh stale notes, and resolve orphans.
- **cross-check**: explicit only. Scopes the affected notes from the pending ledger, hands batches to cheaper subagents that report findings, applies the fixes itself, then moves `last_cross_check` forward.
- **"Keeping it current" block**: text offered to the user for their project instructions file.

## Dependencies

- [[note-format]]: the file states the format every generated note must follow.
- [[note-templates]]: init is told to start notes from these.
- [[vault-validator]]: validate runs it, and init runs it as its last step.

## Invariants and gotchas

- Frontmatter uses only `name` and `description`, the fields every Agent Skills host accepts, so the folder works when copied into any agent's skills directory.
- The script path is given as `${CLAUDE_SKILL_DIR}/scripts/validate.py` for Claude Code; other agents must resolve it relative to the skill folder themselves.
- The skill must never write `docs/.obsidian/` or the user's instructions file without a yes.
- Init adds `docs/.obsidian/` to the target repo's `.gitignore`, because [[obsidian]] creates that folder with personal state as soon as the vault is opened.
- A stale note that turns out to be correct is cleared by setting its `reviewed` date, since only a commit to the note makes it fresh.
- The skill assumes docs drift between cross-checks. Drift is recorded in `docs/pending-cross-check.md` and cleaned up later, usually before a deploy, instead of being prevented.
- Cross-check subagents only report. The main agent edits, so two batches never touch the same note, and it re-reads the code before acting on a `wrong` finding.
- The scope is deliberately small; see [[minimal-skill-scope]].

## Notes
