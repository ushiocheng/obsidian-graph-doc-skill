# 01 — The Obsidian vault format as a machine-written target

Research date: 2026-11-15. Current public Obsidian release at time of writing: **1.15.1** (desktop and mobile, 2026-11-12) ([changelog](https://obsidian.md/changelog/)).

How this was verified:

- Official help text was read from the source repository of the help site, `obsidianmd/obsidian-help`, at commit `0a01159` (2026-11-12). Note that `help.obsidian.md/*` now 301-redirects to `obsidian.md/help/*`; URLs below use the new location.
- Plugin and tool status comes from the last commit date on the default branch and the `manifest.json` of each repository, read on 2026-11-15. The GitHub REST API was rate-limited, so **"archived" flags and star counts were not checked**.
- Anything marked **[unverified]** was not confirmed against a primary source. Anything marked **[undocumented]** is behaviour or a file format that Obsidian does not document officially; the source is a community one.

---

## Summary of recommendations

Each recommendation is explained in the section named in brackets.

**Frontmatter**

- R1. Emit frontmatter with a real YAML serializer, as the first bytes of the file, with unique top-level keys only. No nested objects. [§1]
- R2. Use only the seven property types Obsidian knows: text, list, number, checkbox, date, date & time, tags. Keep each property name one type across the whole vault. [§1]
- R3. Use `tags`, `aliases`, `cssclasses` (plural, always YAML lists). Never emit `tag`, `alias`, `cssclass`: support was dropped in 1.9. [§1]
- R4. Write every link in frontmatter as a double-quoted wikilink: `"[[path/to/note]]"`. Markdown-style links are not recognised in properties. [§1]
- R5. Name property keys in `snake_case` with no dots (for example `depends_on`). A dot in the key breaks link updating on rename, still reproducible in 1.15. [§1]
- R6. Put the unit's real name in `aliases` (and a `title` text property), because the filename will often be a sanitised form of it. [§1, §6]
- R7. Use `description` for the one-line summary. It is a plain text property that Obsidian Publish also reads. [§1]

**Links**

- R8. Body links: standard Markdown links with a relative path and the `.md` extension, `[session](../auth/session.md)`. These work in Obsidian (graph, backlinks, rename) and render on GitHub and GitLab. Wikilinks do not render on GitHub. [§2]
- R9. Frontmatter links: quoted wikilinks with the path from the vault root, `"[[modules/auth/session]]"`, never the bare basename, because code units share names (`utils`, `index`). [§2]
- R10. Never rely on shortest-path (bare basename) resolution when two notes can share a basename. Obsidian documents no tie-break rule. [§2]
- R11. Avoid cross-note heading links in the body if GitHub rendering matters: Obsidian anchors use the heading text, GitHub uses a lower-case hyphenated slug, and one link cannot satisfy both. Link to the note, or split the heading into its own note. [§2]
- R12. Do not use block references (`#^id`) or `![[embeds]]` for anything a GitHub reader needs. They are Obsidian-only. [§2]
- R13. Do not emit links to notes that will not be generated. Unresolved links become phantom nodes in the graph. Validate that the unresolved-link count is zero. [§2]
- R14. Ship `app.json` with `useMarkdownLinks: true` and `newLinkFormat: "relative"` so links that humans add in Obsidian match the generated style. [§2, §5]

**Typed links**

- R15. The canonical store for a typed relation is a frontmatter list property whose values are quoted wikilinks (`depends_on`, `used_by`, `see_also`, ...). It is the only typed form that core Obsidian indexes with no plugin. [§3]
- R16. Mirror each relation in the body as a short section of Markdown links (for example `## Depends on`), so that the relation is clickable on GitHub and visible in reading view. [§3]
- R17. Do not make any plugin a requirement. Choose property names that Breadcrumbs, Extended Graph, Graph Link Types and ExcaliBrain can consume unchanged. [§3]
- R18. Do not use Dataview inline fields (`key:: [[X]]`) as the primary encoding: core Obsidian sees them as plain links with no type, and Dataview has had no commits since April 2025. [§3]
- R19. Tell users that the core graph view cannot show, label, colour or filter by link type. Node colour (by path, tag or property) is the only core-native visual channel. [§3, §4]

**Core features**

- R20. Give every note a `type` text property (`module`, `class`, `function`, ...) and a matching nested tag (`kind/module`). These drive graph colour groups, search and Bases filters. [§4, §6]
- R21. Generate `.base` files as the dynamic indexes (all modules, orphans, "depended on by"). Requires Obsidian 1.9+. Use only `table` and `list` views for the widest version support. [§4]
- R22. Optionally generate one `.canvas` per subsystem as an architecture map, with `file` nodes and labelled edges. Canvas is the only core feature that shows a relation label on an edge. [§4]
- R23. Use the official Obsidian CLI (1.12+) as an optional validation step (`unresolved`, `orphans`, `deadends`, `properties`, `base:query`). It needs the desktop app running, so the generator needs its own offline validator too. [§4, §7]
- R24. Do not depend on Obsidian Publish or Obsidian Headless. Headless only covers Sync and Publish. [§4]

**`.obsidian/`**

- R25. Commit only a small, stable subset: `app.json`, optionally `graph.json`, optionally `types.json`. Gitignore `workspace.json`, `workspace-mobile.json`, `workspaces.json`, `cache`, and `.trash/`. [§5]
- R26. Never overwrite an existing `.obsidian/` file: merge keys, or skip. Obsidian rewrites these files while running. [§5]
- R27. Never pre-install community plugins or commit `plugins/`. [§5]

**Names, folders, tags**

- R28. Filenames: lower-case ASCII, `[a-z0-9._-]` only, no spaces, no trailing dot or space, no Windows reserved names, and no two names in a folder that differ only by case. [§6]
- R29. Folder notes: name the note after its folder and put it inside (`auth/auth.md`). There is no core folder-note feature, so always link to it explicitly. [§6]
- R30. Root index: one generated MOC note at the vault root plus `.base` views. Do not hand-maintain long link lists that a Base can compute. [§6]
- R31. Tags: lower-case, `[a-z0-9_/-]`, at least one non-digit, nested with `/`, written without `#` in YAML. [§6]

**Validation**

- R32. Ship a built-in validator that checks: YAML parses, links resolve to exactly one file, filenames are legal, no case collisions, `.base` files parse as YAML, `.canvas` edges point at existing node ids. [§7]
- R33. For CI outside Obsidian, recommend `lychee` for Markdown links and note that `markdown-link-check` and `markdownlint` do not understand wikilinks. [§7]

---

## 1. Frontmatter / Properties

Source for this section unless stated: [Properties](https://obsidian.md/help/properties).

### 1.1 Format

Properties are YAML between `---` lines "at the top of the file". Names are separated from values by a colon and a space. "each name must be unique within a note".

JSON frontmatter is accepted but "will be read, interpreted, and saved as YAML", so a generator should write YAML.

### 1.2 Supported property types

| Type | YAML form | Notes |
|---|---|---|
| Text | `title: A New Hope` | Single line. Markdown is not rendered. `#hashtags` do not create tags. May hold a URL or a quoted wikilink. |
| List | block list, one `- item` per line | Items may be text, numbers, or quoted wikilinks. |
| Number | `year: 1977`, `pie: 3.14` | "must always be a literal number, not an expression". |
| Checkbox | `favorite: true` | `true` or `false`. An empty value is "indeterminate". |
| Date | `date: 2020-08-21` | |
| Date & time | `time: 2020-08-21T10:30:00` | |
| Tags | block list | "used exclusively by the `tags` property", cannot be assigned to other names. |

"Once a property type is assigned to a property name, all properties with that name across your vault will use the same type." A generator must therefore never emit `owner: alice` in one note and `owner: [alice, bob]` in another.

### 1.3 Default and reserved names

| Property | Type | Used by |
|---|---|---|
| `tags` | List (Tags) | core |
| `aliases` | List | core |
| `cssclasses` | List | core |
| `publish` | checkbox | Obsidian Publish |
| `permalink` | text | Obsidian Publish |
| `description` | text | Obsidian Publish (link previews) |
| `image`, `cover` | text | Obsidian Publish (link previews) |

Deprecated: `tag`, `alias`, `cssclass`. "These properties were deprecated in Obsidian 1.4 ... Support for them as Default properties is dropped in Obsidian 1.9."

`aliases` gives a note alternative names for link suggestions and unlinked mentions. An alias is **not** a link target: Obsidian writes `[[Artificial Intelligence|AI]]`, not `[[AI]]` ([Aliases](https://obsidian.md/help/aliases)). The `kepano/obsidian-skills` reference states it directly: "A bare `[[Alias]]` doesn't resolve; write `[[Note|Alias]]`" ([source](https://github.com/kepano/obsidian-skills/blob/main/plugins/obsidian/skills/obsidian-markdown/references/PROPERTIES.md)).

### 1.4 What is not supported

Quoted from the "Not supported" list:

- "**Nested properties**: To view nested properties, we recommend using the source mode."
- "**Markdown in properties**: This is an intentional limitation".
- Bulk editing (irrelevant to a generator).

Nested YAML is therefore legal and preserved, but the Properties UI cannot edit it. Whether links inside nested objects are indexed is **[unverified]**: a 2023 forum thread reports that they are not ([thread](https://forum.obsidian.md/t/backlink-nested-yaml-frontmatter/69764/2)), and no staff statement was found.

### 1.5 Links inside frontmatter

Syntax, from the help page:

```yaml
---
link: "[[Episode IV]]"
links:
  - "[[Link]]"
  - "[[Link2]]"
---
```

"Internal links in text properties must be surrounded with quotes." The reason is YAML: an unquoted `[[X]]` parses as a list inside a list.

The public API confirms the same form and shows display text:

```yaml
key1: "[[wikilink]]"
key2: "[[wikilink|alias]]"
```

(`CachedMetadata.frontmatterLinks`, "since 1.4.0", in [obsidian.d.ts](https://github.com/obsidianmd/obsidian-api/blob/master/obsidian.d.ts).)

Where frontmatter links count:

| Feature | Counts? | Evidence |
|---|---|---|
| Backlinks pane | Yes | "Properties with links will now properly show in backlink entries." ([1.4.5 changelog](https://obsidian.md/changelog/2023-08-31-desktop-v1.4.5/)) |
| Bases `file.links` | Yes | "List of all internal links in the note, including frontmatter" ([Bases syntax](https://obsidian.md/help/bases/syntax)) |
| Graph view | Yes, **indirect evidence only** | No official statement found. A June 2026 feature request asks for a way to hide them: frontmatter links make "the Local Graph show up a lot of connections", "There is no workaround at the moment" ([thread](https://forum.obsidian.md/t/an-option-to-disable-frontmatter-links-to-show-up-in-graph-view/114940)). |
| Auto-update on rename | Yes for plain top-level keys, **with known bugs** | A 1.5.6 bug where text-property links were not renamed was acknowledged by staff: "We are aware of this. Will be fixed 1.5.7" ([thread](https://forum.obsidian.md/t/links-in-properties-are-not-renamed-automatically-after-renaming-a-linked-note/77249)). Keys that contain a dot (`Person.name`) are still not updated, reported up to 1.15 ([thread](https://forum.obsidian.md/t/property-names-with-dots-break-link-updating-on-note-rename/102860)). |
| Markdown-style links `[t](x.md)` in properties | No | Not supported by core; a community plugin, "Frontmatter Markdown Links", exists to add it ([listing](https://community.obsidian.md/plugins/frontmatter-markdown-links)). |
| Obsidian Publish | **[unverified]** | A forum request says property links are ignored on published sites ([thread](https://forum.obsidian.md/t/obsidian-publish/105533)). |

Heading or block subpaths inside a property link (`"[[Note#Heading]]"`) were not verified either way. **[unverified]**

### 1.6 YAML rules a generator must follow

- Quote any string that contains `: `, ` #`, or starts with one of `[ ] { } & * ! | > ' " % @ `` ` ``, and any string that YAML would read as another type (`yes`, `no`, `null`, `1.0`, `2024-01-01`). The simplest safe policy is to double-quote every text value.
- Write tags without `#`: an unquoted `#` starts a YAML comment.
- "Tags in YAML should always be formatted as a list" and "Aliases should always be formatted as a list in YAML" ([Tags](https://obsidian.md/help/tags), [Aliases](https://obsidian.md/help/aliases)).
- An empty value (`key:`) is not the same as `""` or `[]`: property search `[key:null]` only matches the first ([Search](https://obsidian.md/help/plugins/search)).

### 1.7 Example of a generated note header

```yaml
---
title: "SessionStore"
aliases:
  - "SessionStore"
  - "auth.session.SessionStore"
type: class
description: "Persists login sessions and expires them."
source_path: "src/auth/session.py"
tags:
  - kind/class
  - lang/python
depends_on:
  - "[[modules/auth/token-signer]]"
  - "[[modules/db/connection-pool]]"
used_by:
  - "[[modules/api/login-handler]]"
see_also:
  - "[[modules/auth/auth]]"
generated: 2026-11-15
---
```

---

## 2. Links

Source for this section unless stated: [Internal links](https://obsidian.md/help/links).

### 2.1 Two equivalent syntaxes

```md
[[Three laws of motion]]                                   wikilink
[[Three laws of motion.md]]                                wikilink, extension optional for .md
[Three laws of motion](Three%20laws%20of%20motion.md)      Markdown link
[[Projects/Three laws of motion]]                          path from the vault root, forward slashes
```

"The examples above are equivalent, and they appear the same way in the editor and links to the same note."

Rules:

- Markdown-format destinations must be URL-encoded: "blank spaces become `%20`".
- Non-Markdown files need the extension: `[[Figure 1.png]]`.
- "A string which contains the following characters may not work as a link: `# | ^ : %% [[ ]]`."
- A link to a missing note that includes a folder path creates the note at that path when clicked.

### 2.2 Headings, blocks, display text, embeds

```md
[[#Heading in this note]]
[[Note#Heading]]
[[Note#Heading#Subheading]]
[[Note#^block-id]]
[[Note|Display text]]
[[Note#Heading|Display text]]
[Display text](Note.md#Heading)

A paragraph that can be linked to. ^block-id
```

- Block ids: "can only consist of Latin letters, numbers, and dashes". For lists, quotes, callouts and tables the id goes on its own line with a blank line before and after.
- "Block references are specific to Obsidian and not part of the standard Markdown format."
- Embeds are a link with `!` in front: `![[Note]]`, `![[Note#Heading]]`, `![[Note#^id]]`, `![[image.png|640x480]]`, `![[File.base#View]]`, `![[My canvas.canvas]]` ([Embed files](https://obsidian.md/help/embeds)). Embedded canvases "display shapes but not the text inside cards".

### 2.3 Resolution rules

What is documented:

- The "New link format" setting only controls what Obsidian **writes**: "Shortest path when possible — Uses the shortest unique path", "Relative path to file", "Absolute path in vault" (Settings → Files and links, [source](https://github.com/obsidianmd/obsidian-help/blob/master/en/User%20interface/Settings.md)).
- Obsidian **reads** all three forms regardless of the setting. The API describes resolution as "Get the best match for a linkpath", taking the source file's path "to resolve relative links", with this example: `getFirstLinkpathDest('foo/bar', 'baz/qux.md')` returns the file at `'baz/foo/bar.md'` or `'some/other/path/foo/bar.md'` ([obsidian.d.ts](https://github.com/obsidianmd/obsidian-api/blob/master/obsidian.d.ts)). So a partial path can match as a suffix of a longer path.
- When Obsidian generates link text: "If file name is unique, use the filename. If not unique, use full path." (`fileToLinktext`, same file.)

What is not documented:

- Which file a bare `[[utils]]` resolves to when several `utils.md` exist. No official tie-break rule was found; forum answers conflict ([thread](https://forum.obsidian.md/t/settings-new-link-format-what-is-shortest-path-when-possible/6748)). **[unverified]**
- The exact order of "relative to the source file" versus "suffix match anywhere". **[unverified]**
- Whether resolution is case-insensitive. **[unverified]**

Consequence for a generator: a path-qualified link that names exactly one file is the only form with predictable behaviour. The suffix-match behaviour also means `[[modules/auth/session]]` should still resolve when a user opens the repository root, not `docs/`, as the vault (inferred from the API example above; not tested).

### 2.4 Rename behaviour

"Obsidian can automatically update internal links in your vault when you rename a file." The setting is "Automatically update internal links"; when off, Obsidian prompts. This applies to renames made **inside Obsidian** (or via the CLI `move` / `rename` commands). Files renamed by a generator or by `git mv` are not followed, so the generator must rewrite links itself.

### 2.5 Unresolved links

A link to a note that does not exist is valid. In the graph it becomes a node unless the "Existing files only" filter is on ([Graph view](https://obsidian.md/help/plugins/graph)). The metadata cache tracks them separately (`MetadataCache.unresolvedLinks`), and the CLI lists them with `obsidian unresolved`.

### 2.6 What renders on GitHub and GitLab

| Syntax | Obsidian | GitHub repository view | GitLab repository view |
|---|---|---|---|
| `[text](../a/b.md)` relative link | Link, in graph | Link. "Relative links are easier for users who clone your repository." ([GitHub docs](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax)) | Link |
| `[[Note]]` | Link, in graph | Plain text. GFM, which GitHub applies to repository `.md` files, has no wikilink syntax; users confirm ([forum](https://forum.obsidian.md/t/internal-links-not-working-on-github/50058)). `[[Page|Text]]` only works in GitHub **wikis** ([GitHub docs](https://docs.github.com/en/communities/documenting-your-project-with-wikis/editing-wiki-content)). | `[[Home]]` is a reference to a **wiki page**, not to a repository file ([GitLab docs](https://docs.gitlab.com/user/markdown/)). |
| `#Heading Text` anchor | Heading text, as written | Slug: lower-case, spaces to hyphens | Slug |
| `#^block` / `![[embed]]` | Works | Plain text | Plain text |
| YAML frontmatter | Properties panel | Rendered as a table at the top (secondary sources only, **[unverified]** against GitHub docs) | "displayed as-is, in a box at the top of the document" ([GitLab docs](https://docs.gitlab.com/user/markdown/)) |
| `> [!note]` callout | Callout, many types | Alert, five types only: `NOTE`, `TIP`, `IMPORTANT`, `WARNING`, `CAUTION` | **[unverified]** |
| ` ```mermaid ` | Renders | Renders | Renders |
| ` ```base ` / ` ```query ` / ` ```dataview ` | Renders (with the feature on) | Code block | Code block |

### 2.7 Trade-off and recommendation

| | Wikilinks everywhere | Markdown relative links in body + wikilinks in frontmatter (recommended) |
|---|---|---|
| Obsidian graph, backlinks, rename | Yes | Yes |
| Clickable on GitHub / GitLab | No | Body: yes. Frontmatter: no (shown as text in a table). |
| Frontmatter typed links | Yes | Yes (wikilinks are the only form properties accept) |
| Readable raw text | Best | Slightly noisier |
| Spaces in names | Fine | Need `%20`, so forbid spaces in filenames |
| Heading links | Work in Obsidian | Cannot work in both; avoid |

Workarounds if wikilinks are wanted in the body anyway:

- Convert on export with `obsidian-export`, which turns `[[note]]` and `![[note]]` into CommonMark ([repo](https://github.com/zoni/obsidian-export)); the last commit is from August 2025.
- Publish a rendered site instead of relying on the GitHub file view (Quartz v5 understands Obsidian syntax; [repo](https://github.com/jackyzha0/quartz), active November 2026).
- Emit both: wikilink plus a Markdown link. This doubles every link and is not recommended.

Links from a note to a **source file outside the vault** (`../../src/auth/session.py`) work on GitHub. How Obsidian treats a Markdown link that leaves the vault root was not tested. **[unverified]** The safe form is a plain text property (`source_path`) plus, optionally, an `https://` permalink, which Obsidian treats as an external URL.

---

## 3. Typed / semantic links

Core Obsidian has no typed links. There is a long-running feature request ([thread](https://forum.obsidian.md/t/add-support-for-link-types/6994)). Every method below encodes the type somewhere near the link.

| Method | Syntax | Plugin needed | Status (2026-11-15) | Type visible in core graph view |
|---|---|---|---|---|
| **Frontmatter list property** | `depends_on: ["[[X]]"]` | None | Core since 1.4 | Edge is drawn; the type is **not** shown. Queryable in Bases, Search (`[depends_on:X]`), CLI. |
| **Body section convention** | `## Depends on` + list of links | None | n/a | Edge drawn, type not shown. Human-readable only. |
| **Dataview inline field** | `depends_on:: [[X]]`, `[depends_on:: [[X]]]`, `(depends_on:: [[X]])` | Dataview to query; none to store | Dataview 0.5.68, last commit 2025-04-08 ([repo](https://github.com/blacksmithgu/obsidian-dataview)). Successor Datacore 0.1.29 is "a work-in-progress", last commit 2026-06-22 ([repo](https://github.com/blacksmithgu/datacore)). | Edge drawn (it is a normal body link); type not shown. |
| **Breadcrumbs** | Frontmatter `parent: "[[A]]"`, `child: ["[[B]]", "[[C]]"]`; inline `parent:: [[A]]`; also tags, lists, folders, Dendron names | Breadcrumbs. "Dataview no longer required" since 4.14.0. | 4.22.3, needs Obsidian 1.14+, last commit 2026-11-08. Maintained by michaelpporter since May 2026 ([repo](https://github.com/michaelpporter/breadcrumbs), [docs](https://breadcrumbs-docs.michaelpporter.com/explicit-edge-builders/typed-links/)). | No. Own views: trail, tree, matrix, Mermaid/Markmap code block, Canvas export. |
| **Graph Link Types** | Reads Dataview metadata: frontmatter or `related:: [[X]]` | Graph Link Types + Dataview | 0.3.4, last commit 2026-05-16 ([repo](https://github.com/natefrisch01/Graph-Link-Types)) | **Yes**: draws the key as a text label on core graph edges. Hooks graph internals (PIXI). |
| **Extended Graph** | "A link has a type if it is associated to a property"; also Dataview inline `[lover:: [[X]]]` | Extended Graph. Desktop only. | 2.7.6, last commit 2026-02-13 ([repo](https://github.com/ElsaTam/obsidian-extended-graph), [wiki](https://github.com/ElsaTam/obsidian-extended-graph/wiki/Links-types)) | **Yes**: colours, labels, curved links and per-type filtering on the core graph. README warns "the core graph plugin lacks an API ... many features are experimental". |
| **Juggl** | "Link type support to label edges"; exact syntax **[unverified]** (docs site pages returned 404) | Juggl | 1.5.0, last commit 2025-02-27 ([repo](https://github.com/HEmile/juggl)) | No. Own Cytoscape graph view. |
| **ExcaliBrain** | Dataview fields, e.g. `Author:: [[Isaac Asimov]]`, mapped in settings to parent / child / friend roles; plain links are inferred (forward link = child, backlink = parent) | ExcaliBrain + Dataview + Excalidraw | 0.2.19, last commit 2026-09-29 ([repo](https://github.com/zsviczian/excalibrain)) | No. Own Excalidraw-based view. The settings names for the ontology mapping were not verified. |
| **Wikilink Types** | `[[Target|Display text @supersedes]]`; on save, matching `@type` is copied to a frontmatter field | Wikilink Types | 1.0.1, about 4k downloads ([listing](https://community.obsidian.md/plugins/wikilink-types)) | No (ends up as a frontmatter property). |
| **Canvas edge label** | `"label": "depends on"` on an edge in a `.canvas` file | None | Core | Not in graph view; shown on the canvas itself. |
| Others seen, not evaluated | Typed Graph, Labelled Links, Semantic Canvas, Supercharged Links | — | **[unverified]** | — |

Notes:

- The Graph Link Types README shows `related: [[Research Document]]` unquoted in frontmatter. That is not the form Obsidian documents; use the quoted form.
- In the core graph, frontmatter links and body links to the same target are indistinguishable, and there is no filter for either kind (see the June 2026 request in §1.5).
- Frontmatter properties are the common denominator: core indexes them, and Breadcrumbs, Extended Graph, Graph Link Types (through Dataview) and ExcaliBrain (through Dataview) all read them.

Suggested relation vocabulary (property names are the generator's choice; these are examples that follow R5):

```yaml
depends_on:   # this unit needs the target
used_by:      # reverse of depends_on, generated, never hand-written
part_of:      # containment: function -> class -> module -> package
contains:     # reverse of part_of
implements:   # interface / protocol relation
extends:      # inheritance
tested_by:    # test files
see_also:     # untyped association
```

Emitting both directions costs file size but lets an agent read one note and see all of its edges without a backlink query.

---

## 4. Core features relevant to a docs vault

### 4.1 Graph view

Source: [Graph view](https://obsidian.md/help/plugins/graph).

- Nodes are notes; "Lines represent Internal links between two nodes"; a node grows with the number of notes that reference it.
- **Filters**: "Search files" (full search syntax), "Tags" (show tags as nodes), "Attachments", "Existing files only", "Orphans".
- **Groups**: colour groups, each defined by a search term and a colour. Any search operator works, so groups can be by path (`path:"modules/auth"`), tag (`tag:#kind/class`) or property (`[type:class]`) ([Search](https://obsidian.md/help/plugins/search)).
- **Display**: arrows, text fade threshold, node size, link thickness, time-lapse animation.
- **Forces**: centre, repel, link force, link distance.
- **Local graph**: same settings plus a depth slider.
- "Files matching your Excluded files patterns will not appear in Graph view."
- There is no edge colour, edge label, or filter by link type.

Note that `tag:#work` does not match `#myjob/work`, while `tag:inbox` matches `#inbox/to-read` ([Tags](https://obsidian.md/help/tags)): nested tags match by prefix only.

### 4.2 Bases

Sources: [Bases syntax](https://obsidian.md/help/bases/syntax), [Views](https://obsidian.md/help/bases/views), [Functions](https://obsidian.md/help/bases/functions), and the official-adjacent agent skill [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills/blob/main/plugins/obsidian/skills/obsidian-bases/SKILL.md) (v1.2.0, 2026-11-11).

A base is a `.base` file containing YAML. It can also be written inline in a note as a ` ```base ` code block. "By default a base includes every file in the vault. There is no `from` or `source`".

Layouts and the version that added them: table 1.9, cards 1.9, list 1.10, map 1.10 (needs the Maps plugin), kanban 1.14.

Top-level schema:

```yaml
filters:            # one filter string, or an object with exactly one of: and / or / not
  and:
    - file.inFolder("modules")
    - 'type == "class"'
    - not:
        - file.hasTag("generated/stub")
formulas:           # name -> expression string
  dep_count: 'if(depends_on, list(depends_on).length, 0)'
properties:         # display config per property
  note.type:
    displayName: Kind
  formula.dep_count:
    displayName: "Deps"
summaries:          # custom summary formulas; `values` is the list of column values
  customAverage: 'values.mean().round(3)'
views:
  - type: table     # table | cards | list | map | kanban
    name: "Classes"
    limit: 200
    filters:        # ANDed with the global filters
      and:
        - 'file.ext == "md"'
    groupBy:
      property: note.part_of
      direction: ASC          # ASC | DESC
    sort:
      - property: file.name
        direction: ASC
    order:          # columns, in display order
      - file.name
      - type
      - description
      - depends_on
      - formula.dep_count
    summaries:
      formula.dep_count: Sum
```

Property namespaces:

- `note.x` or bare `x`: frontmatter property.
- `file.*`: `file.name`, `file.basename`, `file.path`, `file.folder`, `file.ext`, `file.size`, `file.ctime`, `file.mtime`, `file.tags`, `file.links` ("including frontmatter"), `file.embeds`, `file.backlinks` ("performance heavy ... Does not automatically refresh"), `file.properties`.
- `formula.x`: defined in `formulas`.

Functions most useful for a docs vault: `file.hasTag("a")` (also matches `a/b`), `file.inFolder("x")` (includes subfolders), `file.hasLink(other)`, `file.hasProperty("name")`, `link("path", "display")`, `list(x)`, `if(c, a, b)`, list `.contains()`, `.length`, `.filter()`, `.map()`.

Operators: `== != > < >= <=`, `&& || !`, `+ - * / %`.

Link semantics: "Wikilinks in frontmatter properties are automatically recognized as Link objects." Links compare equal when they resolve to the same file; "`authors.contains(this)`" and "`author == this`" are the documented forms.

`this`: in a `.base` opened directly it is the base file; in an embed or inline block it is the embedding note; in a sidebar it is the active note. "you can use `file.hasLink(this.file)` to replicate the backlinks pane."

A per-note "depended on by" table, written inline in the note:

````md
```base
filters:
  and:
    - depends_on.contains(this)
views:
  - type: table
    name: "Depended on by"
    order:
      - file.name
      - type
      - description
```
````

Embedding: `![[modules.base]]` shows the first view; `![[modules.base#Classes]]` selects a view by name.

Pitfalls recorded in the `obsidian-skills` reference (not in the help pages):

- In the top-level `properties:` section, a note property needs the `note.` prefix or `displayName` is ignored. The official help example uses a bare key (`status:`), so the two sources disagree. **[unverified]** Using `note.` is safe either way.
- `sort` entries need `property` and an upper-case `ASC`/`DESC`; other forms are "silently ignored". The `sort` key itself is not described on the help syntax page.
- Wrap an expression that contains double quotes in single quotes: `'type == "class"'`.
- Subtracting dates gives a Duration; use `.days` before number functions.

### 4.3 Canvas

Sources: [Canvas](https://obsidian.md/help/plugins/canvas), [JSON Canvas spec 1.0](https://jsoncanvas.org/spec/1.0/) (2024-03-11; the spec repository was last updated 2026-07-24 and 1.0 is still the only version).

A `.canvas` file is one JSON object with two optional arrays.

```json
{
  "nodes": [
    {
      "id": "6f0ad84f44ce9c17",
      "type": "group",
      "x": -40, "y": -40, "width": 900, "height": 400,
      "label": "auth",
      "color": "5"
    },
    {
      "id": "a1b2c3d4e5f67890",
      "type": "file",
      "file": "modules/auth/session.md",
      "x": 0, "y": 0, "width": 360, "height": 240
    },
    {
      "id": "c3d4e5f678901234",
      "type": "file",
      "file": "modules/auth/token-signer.md",
      "subpath": "#Public API",
      "x": 460, "y": 0, "width": 360, "height": 240
    },
    {
      "id": "d4e5f6789012345a",
      "type": "text",
      "text": "# Auth subsystem\nGenerated map.",
      "x": 0, "y": 280, "width": 360, "height": 80
    },
    {
      "id": "e5f6789012345ab1",
      "type": "link",
      "url": "https://example.com/adr/12",
      "x": 460, "y": 280, "width": 360, "height": 80
    }
  ],
  "edges": [
    {
      "id": "0123456789abcdef",
      "fromNode": "a1b2c3d4e5f67890",
      "fromSide": "right",
      "toNode": "c3d4e5f678901234",
      "toSide": "left",
      "toEnd": "arrow",
      "label": "depends on",
      "color": "1"
    }
  ]
}
```

Field reference:

| Object | Required | Optional |
|---|---|---|
| Any node | `id` (string), `type` (`text` / `file` / `link` / `group`), `x`, `y`, `width`, `height` (integers, pixels) | `color` |
| `text` node | `text` (Markdown) | |
| `file` node | `file` (path) | `subpath` (starts with `#`) |
| `link` node | `url` | |
| `group` node | | `label`, `background`, `backgroundStyle` (`cover` / `ratio` / `repeat`) |
| Edge | `id`, `fromNode`, `toNode` | `fromSide`, `toSide` (`top` / `right` / `bottom` / `left`), `fromEnd` (default `none`), `toEnd` (default `arrow`), both `none` or `arrow`, `color`, `label` |

- Node order is z-order: first is at the bottom. Put groups first.
- `color` is a hex string (`"#FF0000"`) or a preset `"1"` red, `"2"` orange, `"3"` yellow, `"4"` green, `"5"` cyan, `"6"` purple.
- The spec only requires ids to be unique strings. Obsidian's own files use 16-character lower-case hex ids ([obsidian-skills json-canvas](https://github.com/kepano/obsidian-skills/blob/main/plugins/obsidian/skills/json-canvas/SKILL.md)).
- In Obsidian the `file` path is relative to the vault root. The spec only says "the path to the file within the system". **[unverified against Obsidian docs]**
- The spec has no auto-layout: the generator must compute `x`, `y`, sizes and avoid overlap.
- "Text-only cards don't appear in Backlinks." Whether canvas `file` nodes and edges add edges to the graph view was not verified. **[unverified]**

### 4.4 Obsidian CLI (official)

Source: [Obsidian CLI](https://obsidian.md/help/cli).

- Exists since the 1.12 installer; needs installer 1.12.7+ and "Settings → General → Command line interface" turned on.
- "Obsidian CLI requires the Obsidian app to be running. If Obsidian is not running, the first command you run launches Obsidian." It is a remote control for the desktop app, not a headless parser.
- Syntax: `obsidian <command> param=value flag`. `vault=<name>` must come first. If the working directory is a vault, that vault is used. `file=<name>` resolves like a wikilink; `path=<path>` is exact from the vault root.

Commands useful to a generator or to an agent reading the vault:

```shell
obsidian unresolved total                 # count of unresolved links
obsidian unresolved verbose format=json   # unresolved links with source files
obsidian orphans                          # files with no incoming links
obsidian deadends                         # files with no outgoing links
obsidian links path="modules/auth/session.md"
obsidian backlinks path="modules/auth/session.md" counts format=json
obsidian properties counts format=json    # every property name in the vault
obsidian property:read name=depends_on path="modules/auth/session.md"
obsidian tags counts format=json
obsidian outline path="modules/auth/session.md" format=json
obsidian search query="[type:class]" format=json
obsidian search:context query="SessionStore"
obsidian bases
obsidian base:query path="indexes/modules.base" view="Classes" format=json
obsidian files folder=modules ext=md total
obsidian move path="a.md" to="b/a.md"     # updates links if the vault setting is on
obsidian eval code="app.vault.getFiles().length"
```

`base:query` output formats: `json|csv|tsv|md|paths`. `eval` runs JavaScript inside the app, and `dev:screenshot` captures the app window; a documentation generator needs neither.

Related, and easy to confuse:

- **Obsidian Headless** (`npm install -g obsidian-headless`, command `ob`, "open beta", Node.js 22+) is a client for Obsidian Sync and Publish only. It does not parse or query a vault ([Headless](https://obsidian.md/help/headless)).
- **`Yakitrak/obsidian-cli`** is an older, unrelated community CLI (v0.3.8, last commit 2026-10-13). Its features were not reviewed.

### 4.5 Obsidian URI

Source: [Obsidian URI](https://obsidian.md/help/uri).

```
obsidian://open?vault=my%20vault&file=path%2Fto%2Fnote
obsidian://open?path=%2Fabs%2Fpath%2Fto%2Fvault%2Fnote
obsidian://search?vault=my%20vault&query=%5Btype%3Aclass%5D
obsidian://new?vault=my%20vault&file=path%2Fto%2Fnote&content=...
```

Actions: `open`, `new`, `daily`, `unique`, `search`, `choose-vault`. Values must be percent-encoded, including `/` as `%2F`. `file` may omit `.md`. A heading is `Note%23Heading`, a block `Note%23%5EBlock`. `vault` is the vault name or id, both of which are per-user, so a generated URI that names a vault is not portable; the `path=` form is absolute and not portable either. Useful for local tooling only.

### 4.6 Publish

- Paid hosted service. Publish-specific properties: `publish`, `permalink`, `description`, `image`, `cover` ([Properties](https://obsidian.md/help/properties)).
- "a plugin that requires a plugin codeblock to render, such as Dataview ... will not work by default in Publish"; embedded search results are not supported; the published graph "does not support the comprehensive sorting and viewing options" ([Publish limitations](https://obsidian.md/help/publish/limitations)).
- Whether Bases render on Publish was not checked. **[unverified]**

### 4.7 Web viewer

Core plugin that opens external links in a tab inside Obsidian on desktop; 1.15.1 added it on mobile ([Web viewer](https://obsidian.md/help/plugins/web-viewer), [changelog](https://obsidian.md/changelog/)). It has no file format and nothing for a generator to produce. Its only relevance: `https://` links to the code host open in-app.

---

## 5. The `.obsidian/` config folder

What is officially documented:

- `.obsidian` holds "preferences specific to that vault, such as hotkeys, themes, and community plugins" ([How Obsidian stores data](https://obsidian.md/help/data-storage)).
- "The `.obsidian/workspace.json` and `.obsidian/workspaces.json` files store the current workspace layout and update whenever you open a new file. If you use Git to manage your vault, you might want to add these files to `.gitignore`." (same page)
- `workspace-mobile.json` holds the mobile layout ([Ribbon](https://github.com/obsidianmd/obsidian-help/blob/master/en/User%20interface/Ribbon.md)).
- Plugins live in `.obsidian/plugins`, themes in `.obsidian/themes`, CSS snippets in `.obsidian/snippets`. For teams: "We recommend creating a standardized template of the configuration folder" ([Deploy Obsidian across your team](https://obsidian.md/help/teams/deploy)).
- The folder name can be changed per device ("Override config folder", must start with a dot) ([Configuration folder](https://obsidian.md/help/configuration-folder)).
- Deleted files may go to a `.trash` folder in the vault, depending on the setting ([Settings](https://github.com/obsidianmd/obsidian-help/blob/master/en/User%20interface/Settings.md)).
- The official help vault itself gitignores the whole `.obsidian` folder ([.gitignore](https://github.com/obsidianmd/obsidian-help/blob/master/.gitignore)).

The JSON schemas of the files are **[undocumented]**. The table below combines official names with community knowledge; verify against a real vault before generating.

| File | Content | Commit? |
|---|---|---|
| `app.json` | Editor and "Files and links" settings | Yes, minimal |
| `appearance.json` | Theme, fonts, enabled snippets | No (personal) |
| `core-plugins.json` | Enabled core plugins | Optional |
| `community-plugins.json` | Enabled community plugin ids | No |
| `graph.json` | Global graph settings, including colour groups | Optional, see below |
| `types.json` | Property name → type assignments **[unverified file name]** | Optional |
| `hotkeys.json` | Custom hotkeys | No |
| `bookmarks.json` | Bookmarks **[unverified]** | No |
| `workspace.json`, `workspace-mobile.json`, `workspaces.json` | Window layout, open files | **Gitignore** (official advice) |
| `cache` | Cache **[unverified]** | Gitignore |
| `plugins/`, `themes/`, `snippets/` | Third-party code and CSS | No |

Suggested `.gitignore` inside the vault folder:

```gitignore
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.obsidian/workspaces.json
.obsidian/cache
.trash/
```

### 5.1 `app.json` seed **[undocumented keys]**

Key names below come from community sources ([forum](https://forum.obsidian.md/t/ideal-settings-from-markdown-interoperability-perspective/22139)) and were not confirmed against an official schema.

```json
{
  "useMarkdownLinks": true,
  "newLinkFormat": "relative",
  "alwaysUpdateLinks": true
}
```

- `useMarkdownLinks`: the "Use Wikilinks" toggle, inverted.
- `newLinkFormat`: `"shortest"` (default), `"relative"`, or `"absolute"`.
- `alwaysUpdateLinks`: the "Automatically update internal links" toggle.

The key for "Excluded files" is believed to be `userIgnoreFilters`. **[unverified]**

### 5.2 `graph.json` colour groups **[undocumented format]**

```json
{
  "colorGroups": [
    { "query": "path:\"modules/auth\"", "color": { "a": 1, "rgb": 4886745 } },
    { "query": "[type:class]",          "color": { "a": 1, "rgb": 14701138 } },
    { "query": "tag:#kind/test",        "color": { "a": 1, "rgb": 5025616 } }
  ]
}
```

- `rgb` is the decimal value of the hex colour: `#4A90D9` → `0x4A90D9` → `4886745`.
- Groups are reported to be evaluated top to bottom with the first match winning ([article](https://dev.to/whoffagents/the-obsidian-color-group-query-syntax-that-turned-my-vault-into-a-brain-40id)). **[unverified]**
- Obsidian rewrites this file when the user changes any graph setting, so a committed `graph.json` will show up as modified in `git status`. The Extended Graph README also warns that graph settings in `.obsidian/graph.json` can be lost if the app closes badly ([repo](https://github.com/ElsaTam/obsidian-extended-graph)).
- The other keys of the file (filters, forces, display) were not verified; a seed file that contains only `colorGroups` relies on Obsidian filling in defaults. **[unverified]**

---

## 6. Filenames, folder notes, indexes, tags

### 6.1 Filename constraints

Official guidance for vaults used across operating systems ([Sync status messages](https://github.com/obsidianmd/obsidian-help/blob/master/en/Obsidian%20Sync/Status%20icon%20and%20messages.md)) is to avoid:

- "Characters commonly reserved by file systems, such as `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, and `|`"
- "A space or period at the end of the name"
- "Windows reserved device names, such as `CON`, `PRN`, `AUX`, `NUL`, `COM1` through `COM9`, or `LPT1` through `LPT9`"

Characters that are legal in a filename but break links: `# | ^ : %% [[ ]]` ([Internal links](https://obsidian.md/help/links)).

Case:

- macOS and Windows file systems are case-insensitive by default; Linux is case-sensitive. `Foo.md` and `foo.md` cannot coexist on the first two, and git checkouts collide. A generator must detect names that differ only by case and disambiguate them.
- Tags are case-insensitive ("#tag and #TAG will be treated as identical").
- Whether link resolution is case-insensitive is **[unverified]**.

Code identifiers regularly violate these rules (`operator<`, `a::b`, `<init>`, `Foo` next to `foo`, `utils` in ten folders). A generator needs a deterministic sanitiser plus the real name in `aliases` / `title`.

Graph nodes and tabs are labelled with the file's basename; a `title` property does not change the label in core Obsidian. **[unverified, from common knowledge]** Ten notes called `index` therefore give ten nodes labelled `index`.

### 6.2 Folder notes

Core Obsidian has no folder-note feature: a folder cannot be a link target or a graph node. Conventions:

- **Same name inside the folder** (`auth/auth.md`): the layout used by the Folder Notes community plugin, which lets a click on the folder open the note ([repo](https://github.com/LostPaul/obsidian-folder-notes), last commit 2026-10-31). That this is the plugin's default storage location was not confirmed from its docs. **[unverified]**
- **`README.md` in each folder**: GitHub renders it under the directory listing. In Obsidian every such note has the basename `README`, so graph labels and quick switcher entries are all identical.
- **`index.md`**: common for static site generators; same duplicate-name problem.

Breadcrumbs can also derive hierarchy from "Folders (folder notes)" and from Dendron-style names (`parent.child.md`) ([repo](https://github.com/michaelpporter/breadcrumbs)).

### 6.3 MOC / index notes

"Map of content" is a community convention, not a feature: a note whose purpose is to link to other notes. For a generated vault:

- One root note linking to each top-level area and to the `.base` indexes.
- One folder note per package or module, listing its children with one-line descriptions.
- Dynamic lists (all classes, orphans, most-depended-on) as Bases, so they never go stale between generator runs.
- Every note links up to its parent (`part_of`), so no note is an orphan and the local graph at depth 1 always shows the container.

### 6.4 Tags

Source: [Tags](https://obsidian.md/help/tags).

- Allowed: letters, numbers, `_`, `-`, `/` (nesting), and "Commonly accepted Unicode characters, including emojis".
- "Tags must contain at least one non-numerical character." `#1984` is not a tag; `#y1984` is.
- No spaces.
- Case-insensitive; displayed "with the casing they are first created with".
- Nested tags: `#inbox/to-read`. `tag:inbox` in Search matches the parent and all children; `file.hasTag("a")` in Bases matches `a` and `a/b`.
- In YAML: a list, without `#`.

```yaml
tags:
  - kind/class
  - lang/python
  - layer/domain
```

Tags can be shown as nodes in the graph ("Tags" filter). Tags suit a few low-cardinality facets; relations between notes belong in link properties.

---

## 7. Tools that parse or validate vaults outside Obsidian

Status is the last commit on the default branch, read 2026-11-15.

| Tool | What it does | Wikilinks | Status |
|---|---|---|---|
| [Obsidian CLI](https://obsidian.md/help/cli) (official) | Queries the real index: `unresolved`, `orphans`, `deadends`, `backlinks`, `properties`, `base:query` | Native | Current (1.12+). Needs the desktop app running. |
| [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) | Agent skills for Obsidian Markdown, Bases, JSON Canvas, CLI, Headless. Reference for exact syntax and pitfalls; close prior art for this project. | n/a | v1.2.0, 2026-11-11. Active. |
| [obsidiantools](https://github.com/mfarragher/obsidiantools) (Python) | Builds a NetworkX graph; indexes wikilinks, Markdown links, embeds, backlinks, front matter, nested tags; `nonexistent_notes`, `isolated_notes`; reads canvas files | Yes. "built to support the 'shortest path when possible' option", so path-qualified links may graph differently | 0.11.0; last commit 2025-07-08. Slow-moving. |
| [obsidian-export](https://github.com/zoni/obsidian-export) (Rust CLI and library) | Exports a vault to CommonMark, resolving `[[note]]` and `![[note]]` | Yes | v25.3.0; last commit 2025-08-25 (dependency maintenance). "not officially endorsed". |
| [lychee](https://github.com/lycheeverse/lychee) (Rust) | Fast link checker for Markdown and HTML | Opt-in: `--include-wikilinks --base-url <vault> --fallback-extensions md` ([recipe](https://lychee.cli.rs/recipes/md-wikilinks/)). Bare-basename wikilinks may not resolve. **[untested]** | Active, 2026-11-12. |
| [markdown-link-check](https://github.com/tcort/markdown-link-check) (Node) | Checks standard Markdown links, including relative file links | No **[unverified]** | v3.15.0; active, 2026-10-22. |
| [markdownlint](https://github.com/DavidAnson/markdownlint) (Node) | Style linting | No | Active, 2026-11-06. |
| [remark-wiki-link](https://github.com/landakram/remark-wiki-link) | remark plugin that parses `[[Page]]` and `[[Page:Alias]]`-style links for unified pipelines | Yes, but not Obsidian's full syntax (headings, blocks, embeds) **[unverified detail]** | Last commit 2023-10-10. Stale. Forks exist (`@portaljs/remark-wiki-link`, `@braindb/mdast-util-wiki-link`), not evaluated. |
| [obsidian-linter](https://github.com/platers/obsidian-linter) | Obsidian plugin: YAML and Markdown formatting rules (`format-yaml-array`, `yaml-key-sort`, `move-tags-to-yaml`, ...) | n/a | Active, 2026-10-31. Runs inside Obsidian only; no standalone CLI was found. **[unverified]** |
| [Quartz](https://github.com/jackyzha0/quartz) | Static site generator that reads an Obsidian vault (wikilinks, graph, backlinks) | Yes | v5.1.0; active, 2026-11-10. |
| [Datacore](https://github.com/blacksmithgu/datacore) / [Dataview](https://github.com/blacksmithgu/obsidian-dataview) | In-app query engines | n/a | Datacore: work in progress, 2026-06-22. Dataview: no commits since 2025-04-08. |

Because the generator controls the output format (path-qualified links, flat YAML, known property names), a small purpose-built validator is more reliable than any general tool. Minimum checks:

1. Frontmatter parses as YAML, is a mapping, has no nested mappings, and every key has a consistent type across the vault.
2. Every wikilink in frontmatter and every relative Markdown link in the body resolves to exactly one existing file.
3. Reverse relations agree (`A depends_on B` ⇔ `B used_by A`).
4. Filenames pass §6.1, with no case-only collisions.
5. Each `.base` file parses as YAML and each `formula.x` it references is defined.
6. Each `.canvas` file parses as JSON, node ids are unique, and edges reference existing ids.
7. No note is an orphan except the root.

---

## Open questions / things I could not verify

Link behaviour (best settled with a scratch vault and `obsidian unresolved` / `obsidian links`):

1. No official statement that frontmatter links are drawn in graph view. Evidence is indirect (June 2026 feature request to hide them).
2. Rename auto-update of frontmatter links: confirmed in principle by a staff reply about a 1.5.6 regression; current reliability for list properties and for links with display text (`"[[x|y]]"`) is unconfirmed. The dotted-key bug is still open as of 1.15.
3. Tie-break rule when a bare `[[name]]` matches several files; order of relative versus suffix matching; case sensitivity of resolution.
4. Whether `"[[Note#Heading]]"` and `"[[Note#^block]]"` work in properties.
5. Whether links inside nested YAML objects are indexed.
6. How Obsidian treats a Markdown link whose relative path leaves the vault (`../../src/x.py`): ignored, unresolved node, or opened externally.
7. Whether `./x.md` (explicit current-directory prefix) resolves in Obsidian.
8. Whether `![text](note.md)` embeds a note the way `![[note]]` does.
9. Whether path-qualified wikilinks still resolve when the repository root, rather than `docs/`, is opened as the vault (inferred from the API example, not tested).
10. Whether core graph node labels can use a property instead of the basename (believed not).

Config files:

11. Exact keys and defaults of `app.json` (`useMarkdownLinks`, `newLinkFormat`, `alwaysUpdateLinks`, `userIgnoreFilters`): community-sourced only.
12. Full schema of `graph.json`, first-match-wins ordering of `colorGroups`, and whether a partial file is accepted and completed by Obsidian.
13. Name and schema of the property-types file (`types.json`), and of `bookmarks.json` and the cache folder.
14. Whether Obsidian tolerates a pre-seeded `.obsidian/` on the first open of a folder as a vault without resetting files.

Bases and Canvas:

15. `properties:` section in `.base`: is the `note.` prefix required for `displayName` (obsidian-skills says yes, the help example omits it).
16. The view-level `sort` key is documented in obsidian-skills, not on the help syntax page.
17. Whether Bases render on Obsidian Publish, and whether ` ```base ` blocks degrade acceptably elsewhere (on GitHub they are plain code blocks).
18. Whether canvas `file` nodes or edges create edges in the graph view or entries in backlinks.
19. Canvas `file` path base (vault root) is Obsidian behaviour not stated in the spec.

Plugins and tools:

20. "Archived" status and star counts of all repositories (GitHub API was rate-limited); status here is last-commit date only.
21. Juggl's typed-link syntax (docs pages returned 404) and ExcaliBrain's ontology setting names.
22. Whether Graph Link Types and Extended Graph still work on 1.15, which changed how the graph loads PIXI ("Graph view loads PIXI on first open").
23. Folder Notes plugin default storage location.
24. Typed Graph, Labelled Links, Semantic Canvas and Supercharged Links were seen in search results but not evaluated.
25. `markdown-link-check` and `remark-wiki-link` wikilink coverage; whether `obsidian-linter` has any CLI mode; lychee behaviour on a real vault.
26. Licensing of the Obsidian CLI (the help page lists no licence requirement; early 1.12 builds were Catalyst-only).

Rendering elsewhere:

27. GitHub's rendering of YAML frontmatter as a table is from secondary sources, not GitHub docs. Long list properties full of `[[...]]` text may look noisy there.
28. GitLab callout/alert support and wikilink behaviour in repository files (GitLab documents `[[Home]]` as a wiki page reference).
