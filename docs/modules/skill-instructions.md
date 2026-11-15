---
type: module
title: Skill instructions
description: The SKILL.md an agent follows to generate, validate or cross-check a docs vault for a codebase.
aliases: [SKILL.md, obsidian-graph-doc]
sources:
  - skills/obsidian-graph-doc/SKILL.md
depends_on:
  - "[[note-format]]"
  - "[[note-templates]]"
  - "[[vault-validator]]"
see_also:
  - "[[obsidian]]"
---

# Skill instructions

The skill's instructions are this one file of prose: an agent loads it and follows it. It also ships templates and one checker script. It defines three modes: `init` (survey a repo and write the vault), `validate` (check a vault and repair it) and `cross-check` (verify the notes against the code, on explicit request only). It is not responsible for keeping a vault current; that is handed to the target project as an opt-in block for its `CLAUDE.md` or `AGENTS.md`.

## Key files

| Path | Role |
|---|---|
| `skills/obsidian-graph-doc/SKILL.md` | Frontmatter (`name`, `description`) plus all instructions |

## Public surface

- **Trigger**: the `description` field decides when an agent loads the skill.
- **init**: survey, plan notes, find edges, write leaf notes first and the index last, validate, report, offer follow-ups.
- **validate**: run the checker, then fix errors, refresh stale notes, and resolve orphans.
- **cross-check**: explicit only. Scopes the notes from pending changed files, stale notes, ledger entries and the notes linking to those (or every note with `all`), hands batches to cheaper subagents that report findings, applies the fixes itself, then moves `last_cross_check` forward.
- **"Keeping it current" block**: text offered to the user for their project instructions file.

## Dependencies

- [[note-format]]: the file states the format every generated note must follow.
- [[note-templates]]: the Note format section points init at these for notes, and the ledger section at the ledger template.
- [[vault-validator]]: validate runs it, and init runs it at step 7 of 9, after writing the notes and the ledger and before the report.

## Related

- See also [[obsidian]]: the skill's "Obsidian setup" section and its link rules exist because of how Obsidian behaves.

## Invariants and gotchas

- Frontmatter uses only `name` and `description`. Per [[03-skill-authoring-and-distribution]] these are in the subset every Agent Skills host accepts, so the folder should work when copied into another agent's skills directory. Only Claude Code has been tried.
- The script path is given as `${CLAUDE_SKILL_DIR}/scripts/validate.py` for Claude Code; other agents must resolve it relative to the skill folder themselves.
- The skill must never create or modify `docs/.obsidian/`, and must not create or edit the user's instructions file without a yes.
- Init adds `docs/.obsidian/` to the target repo's `.gitignore`, because [[obsidian]] creates that folder with personal state as soon as the vault is opened.
- A stale note that turns out to be correct is cleared by setting its `reviewed` date, since only a commit to the note makes it fresh.
- The skill assumes docs drift between cross-checks. Drift is recorded in `docs/pending-cross-check.md` and cleaned up later, usually before a deploy, instead of being prevented.
- Cross-check subagents only report. The main agent edits, so two batches never touch the same note, and it opens the cited code before acting on a `wrong` or `contradiction` finding.
- `last_cross_check` can only name a commit. So a cross-check starts from committed code, and if it changes code, that is committed before the ledger is updated in a commit of its own.
- The scope is deliberately small; see [[minimal-skill-scope]].

## Notes
