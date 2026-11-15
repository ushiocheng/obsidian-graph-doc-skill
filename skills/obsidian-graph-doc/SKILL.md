---
name: obsidian-graph-doc
description: Generate or check graph-structured documentation for a codebase - a docs/ folder that is also an Obsidian vault, with one short note per module, YAML frontmatter, and typed wikilinks (depends_on, part_of, see_also...) between notes. Use when the user asks to document a codebase as an Obsidian vault, build a docs graph or knowledge graph of a repo, create linked/atomic architecture notes, or validate, refresh or cross-check such a vault against the code.
---

# obsidian-graph-doc

Build `docs/` as an Obsidian vault that documents the codebase as a graph: many small notes, each about one unit, connected by typed links. A human browses it in Obsidian. An agent reads the index, opens the one or two notes for the area it is changing, and sees every dependency without reading the rest.

Three modes. Pick from the request or the argument; default to **init** if `docs/` has no vault notes yet, otherwise **validate**.

- **init**: survey the repo and write the vault.
- **validate**: cheap mechanical check of an existing vault; fix or report problems.
- **cross-check**: expensive check of the notes against the code, delegated to subagents. Run it only when the user asks for it explicitly (`/obsidian-graph-doc cross-check`); never start it on your own.

The working assumption: between cross-checks the docs will drift and mistakes will be made. That is acceptable as long as the drift is recorded in `docs/pending-cross-check.md` and cleaned up later, usually before a deploy or release.

Keeping the vault current after init is not a mode. It is a standing instruction the user can opt into (see "Keeping it current").

## Principles

1. **The code is the source of truth.** Every structural claim (what depends on what, what a module exports) must come from reading the code now, never from memory or from an older note.
2. **Write what the code cannot say quickly.** Purpose, responsibilities, invariants, gotchas, why. Do not restate signatures or walk through code line by line.
3. **Small notes.** Aim for under about 60 lines per note. If a note grows past about 150, split it.
4. **Unit level, not symbol level.** One note per module, package, service, or other cohesive unit. Classes and functions are headings or table rows inside a note, never their own notes, unless the user asks.
5. **Every link is real.** Never link to a note that does not exist. Never invent a dependency; if one is suspected but not confirmed in code, say so in the body in words and leave it out of the frontmatter.

## Note format

Every vault note starts with flat YAML frontmatter. No nested objects (Obsidian's property editor cannot show them).

```yaml
---
type: module
title: Session store
description: Persists login sessions and expires them.
aliases: [SessionStore]
sources:
  - src/auth/session.py
  - src/auth/session_gc.py
part_of:
  - "[[auth]]"
depends_on:
  - "[[db-pool]]"
  - "[[config]]"
see_also:
  - "[[login-flow]]"
---
```

| Key | Required | Meaning |
|---|---|---|
| `type` | yes | One of the note types below. |
| `title` | yes | Human name of the unit. |
| `description` | yes | One sentence. The index is built from these. |
| `aliases` | no | Other names people search for (class name, package name). |
| `sources` | for `module`, `interface`, `data-model`, `flow` | Repo-root-relative paths or globs this note describes. |
| `reviewed` | no | Date (`YYYY-MM-DD`) the note was last checked against its sources and found correct without edits. See "Staleness". |
| link keys | as applicable | Lists of quoted wikilinks; see below. |

### Link types

Links in frontmatter are always quoted: `"[[note-name]]"`. Store each link on one side only; Obsidian backlinks and a search for `[[note-name` give the reverse direction.

Obsidian does not resolve frontmatter links without a plugin. So the frontmatter is the typed record that tools and agents query, and the body is what Obsidian's graph and backlinks see. **Every frontmatter link must also appear as a wikilink in the body.**

| Key | Meaning | Written on |
|---|---|---|
| `part_of` | This unit is contained in the target. At most one parent. | the child |
| `depends_on` | This unit needs the target to build or run: imports it, calls it, reads or writes its data, talks to it over the network. | the dependent |
| `implements` | This unit provides the behaviour that the target `interface` or `concept` note specifies. | the implementer |
| `about` | This `flow`, `concept` or `decision` note explains or constrains the target. | the explaining note |
| `supersedes` | This note replaces the target. | the newer note |
| `see_also` | Related, none of the above. At most five. | either side |

Do not add other link keys.

### Staleness

Staleness comes from git history, not from a field in the note. A note is **stale** when any file in its `sources` has changed after the note file's own last commit. A note with uncommitted edits, or not committed yet, is treated as being worked on and is not reported.

So a note is made fresh by committing a change to it together with, or after, the source change. If you checked a stale note against the new code and nothing needed changing, set `reviewed` to today's date; that edit is what marks it fresh. Never touch a note to clear staleness without reading what changed.

In the body, use plain wikilinks: `[[note-name]]` or `[[note-name|display text]]`. Put each `depends_on` target in a Dependencies section with the reason it is needed. Put every other frontmatter link in a Related section that names the relation in words ("Part of [[auth]]", "Explains [[login-flow]]").

### Note types and layout

| Type | Folder | When | One note per |
|---|---|---|---|
| `index` | `docs/index.md` | always, exactly one | vault |
| `overview` | `docs/overview.md` | always, exactly one | repo |
| `module` | `docs/modules/` | always | cohesive unit of code |
| `interface` | `docs/interfaces/` | if the repo exposes one | HTTP API, CLI, event contract, public library surface |
| `data-model` | `docs/data/` | if present | table, schema, message or file format |
| `flow` | `docs/flows/` | for the few paths that cross several modules | end-to-end path (request, job, build) |
| `external` | `docs/external/` | only for dependencies that shape the design | third-party system or library |
| `concept` | `docs/concepts/` | for domain terms the code assumes | term or pattern |
| `decision` | `docs/decisions/` | only when a recorded reason exists | decision |

Never invent rationale for a `decision` note. Write one only from an existing ADR, a commit message, a comment, or what the user tells you.

### File names

- Lower-case kebab-case, ASCII: `auth-session.md`.
- **Unique across the whole vault**, ignoring case, so a bare `[[auth-session]]` always resolves. If two units would share a name, qualify both (`api-auth`, `worker-auth`).
- Put the unit's real name in `title` and `aliases`.

Templates: `templates/module.md` and `templates/index.md` next to this file. Other types use the module template's frontmatter with body sections that fit the type.

### The pending cross-check ledger

`docs/pending-cross-check.md` (from `templates/pending-cross-check.md`) is not a vault note; it has no `type`. It holds two things:

- `last_cross_check` in its frontmatter: the commit the docs were last fully checked against. Every code file changed since then is pending, and the checker finds that list from git, so nobody has to maintain it.
- An `## Entries` list, one line each, for what git cannot show: a note someone changed code under but did not update, a link they were unsure of, two notes that seem to disagree.

The checker prints every pending item and warns when there are more than 20, because by then the docs have probably drifted in several places at once.

## init

1. **Survey.** List tracked files (`git ls-files`), read the README, manifests (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`...), entry points, and any existing docs. Skip vendored, generated and build-output directories.
2. **Plan the notes.** Choose units by cohesion, not by file count: a 50-file repo usually gives 5 to 15 module notes; a large monorepo gives one note per package first, with deeper notes only where the user asks. Show the user the plan as a list (`type`, note name, sources) with the expected note count. For more than about 40 notes, or a repo too large to read in one session, ask which areas to cover first rather than cover everything thinly.
3. **Leave existing docs alone.** Files already in `docs/` that are not vault notes stay untouched. Link to them from the relevant notes where useful.
4. **Find the edges.** For each planned unit, read its sources and search imports and calls to find which other planned units it uses. Also look for dependencies imports do not show: HTTP or RPC calls, queues, shared tables, config and environment variables. Only confirmed edges go in frontmatter.
5. **Write leaf notes first**, then notes that contain them, then `overview.md`, then `index.md` last (built from every note's `description`). On large repos, if subagents are available, give each one a disjoint set of notes plus the full plan (so it only links to names that will exist).
6. **Create the ledger** `docs/pending-cross-check.md` from its template, with `last_cross_check` set to the current short `HEAD` hash (leave it empty if the repo has no commits) and no entries.
7. **Validate** (next section) and fix every error.
8. **Report**: note count by type, anything left uncovered, any dependency you suspected but could not confirm.
9. **Offer the follow-ups** in "Keeping it current" and "Obsidian setup". Do not apply them without the user's yes.

## validate

If Python 3 is available, run the bundled checker from this skill's directory (in Claude Code: `${CLAUDE_SKILL_DIR}/scripts/validate.py`):

```
python3 <skill-dir>/scripts/validate.py docs
```

It reports errors (exit code 1) and warnings:

- missing or malformed frontmatter, unknown `type`, missing required keys, unquoted or unknown link keys
- wikilinks, in frontmatter or body, that resolve to no note
- duplicate note names
- `sources` paths that match no file
- frontmatter links that do not also appear in the body
- orphan notes (nothing links to them)
- **stale notes**: files in `sources` changed after the note's last commit (needs git)
- **pending cross-check**: one `PENDING` line per code file changed since `last_cross_check` and per ledger entry, with a warning above 20

Without Python, do the same checks by hand with file listing and search.

Then act on the result:

- **Errors**: fix them. A broken link is fixed by correcting the name or removing the link, never by creating an empty note.
- **Stale notes**: the checker names the changed files. Read what changed since the note's last commit (`git log -1 --format=%h -- <note>` gives that commit, then `git diff <commit> -- <sources>`), and update the note's body and links to match. If nothing needed changing, set `reviewed` to today's date.
- **Orphans**: link them from their parent or the index, or delete them if the unit is gone.
- **Pending warning**: tell the user the docs may have drifted and that `/obsidian-graph-doc cross-check` will clean it up. Do not start the cross-check yourself.

## cross-check

Verifies the notes against the code and against each other, then clears the ledger. It reads a lot of code, so it runs only on an explicit request. `cross-check all` covers every note; plain `cross-check` covers the affected ones.

1. **Start from committed code.** `last_cross_check` can only name a commit, so code checked while uncommitted would still show as pending afterwards. If the working tree has uncommitted changes outside `docs/`, ask the user to commit them first (or commit them if they have asked you to). Then run validate, fix the mechanical errors, and keep the `PENDING` and stale output.
2. **Choose the notes in scope.** Every note whose `sources` match a pending changed file, every stale note, every note named in a ledger entry, and every note that links to one of those. List pending changed files that no note covers; they may need a new note. With `all`, take every note.
3. **Delegate in batches.** Split the notes into batches of about five and give each batch to a subagent running a smaller, cheaper model (in Claude Code: `model: sonnet`). Run batches in parallel. Without subagents, work through the batches yourself. Each subagent is told to report only, not edit, and for each note in its batch to:
   - read the note and every file in its `sources`;
   - for each typed link, find the evidence in the code (for `depends_on`: the import, call, query or request) and give the file and line, or say none was found;
   - look for dependencies in the code that the note does not list;
   - check each factual statement in the body against the code;
   - read the notes this one links to and report anything the two say that cannot both be true;
   - return one finding per problem: note, the claim, verdict (`wrong`, `missing`, `contradiction`, `unverifiable`), evidence as `path:line`, and a suggested fix. Confirmed claims need no finding; return a count of them.
4. **Apply the fixes yourself**, not the subagents, so two batches never edit the same note. For a `wrong` or `contradiction` finding, open the cited code before changing the note; a cheaper model's finding is a lead, not a fact. Leave `unverifiable` items as ledger entries.
5. **Run validate again** until it has no errors.
6. **Update the ledger**: set `last_cross_check` to the current short `HEAD` hash, delete resolved entries, keep unresolved ones with a note on why.
7. **Report**: notes checked, findings by verdict, what was fixed, what remains in the ledger, and any code with no note.

If the scope is more than about 60 notes, tell the user the size and ask whether to check everything or one area first.

## Keeping it current

After init, offer to add this block to the project's `CLAUDE.md` or `AGENTS.md` (create neither without asking):

```markdown
## Docs vault

`docs/` is an Obsidian vault that maps this codebase. Start at `docs/index.md`,
open the notes for the area you are changing, and follow their `depends_on` links.
To find what depends on a unit, search `docs/` for `[[its-note-name`.

- If a note disagrees with the code, the code is right. Fix the note.
- When you change files listed under a note's `sources`, update that note in the
  same commit. If the note is still correct, set its `reviewed` date instead.
  A note is stale when its sources have a newer commit than the note itself.
- When you add, rename or remove a module, add, rename or remove its note and
  update `docs/index.md`.
- If you cannot update the docs now, or are unsure they still match, add one line
  under "Entries" in `docs/pending-cross-check.md`: the date, the files or notes
  involved, and what may be wrong. Recording a known gap is fine; hiding one is not.
- Before a deploy or release, or when validation warns that many items are pending,
  ask the user to run `/obsidian-graph-doc cross-check`.
```

Keep it short and do not import the vault into the instructions file: notes are read on demand.

## Obsidian setup

Do not create or modify `docs/.obsidian/`. Tell the user they can open `docs/` as a vault directly, and mention that wikilinks are not clickable when the files are viewed on GitHub.

Obsidian creates `docs/.obsidian/` the moment the folder is opened as a vault, and it includes `workspace.json`, the user's personal window and tab state. A later `git add -A` will pick it up. So during init, add `docs/.obsidian/` to the repo's `.gitignore` (create the file if needed) and say so in the report. If the user wants to share vault settings, ignore only `docs/.obsidian/workspace*.json` instead. Before any commit you make that touches `docs/`, check that nothing under `docs/.obsidian/` is staged unless the user asked for it.
