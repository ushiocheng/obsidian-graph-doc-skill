# Skill authoring and distribution: research notes

Research date: 2026-11-14. Every claim cites the official page it was checked against. Items marked **[UNVERIFIED]** could not be confirmed from the pages I read and need a test or a follow-up fetch.

Scope: a Claude skill that generates an Obsidian-style `docs/` vault (frontmatter, typed links) for any codebase, published on GitHub. It may survey a repo, fan out subagents, run bundled helper scripts (a link/frontmatter validator, a dependency extractor), and support first-time generation and incremental updates.

## Recommended repository layout

Repo root is the plugin root, and the repo also carries a marketplace file so it can be installed with `/plugin marketplace add`. The skill sits in `skills/<name>/`, so the same tree also works as a plain copy into `~/.claude/skills/`.

```
obsidian-graph-doc/
├── .claude-plugin/
│   ├── plugin.json                  # manifest: name, description, version policy
│   └── marketplace.json             # optional: makes the repo installable via /plugin marketplace add
├── skills/
│   └── docs/                        # directory name == SKILL.md name
│       ├── SKILL.md                 # under 500 lines: modes, procedure, pointers to references/
│       ├── references/
│       │   ├── frontmatter-schema.md
│       │   ├── link-conventions.md  # wikilinks, typed links, index/MOC rules
│       │   ├── mode-init.md         # loaded only when $0 == init
│       │   ├── mode-update.md       # loaded only when $0 == update
│       │   └── mode-validate.md
│       ├── scripts/
│       │   ├── extract_deps.py      # emits JSON; run via ${CLAUDE_SKILL_DIR}/scripts/...
│       │   └── validate_vault.py    # frontmatter + link checker; exit 0 or 1
│       └── assets/
│           └── templates/           # note templates copied into the target docs/
├── agents/                          # OPTIONAL plugin-only subagents (not copied with a plain skill copy)
│   └── module-mapper.md
├── hooks/
│   └── hooks.json                   # OPTIONAL plugin-only, e.g. PostToolUse stale-note flag
├── evals/
│   └── <case>/prompt.md + graders/  # claude plugin eval suite
├── README.md
├── CHANGELOG.md
└── LICENSE
```

Why this shape:
- `skills/<name>/` is the unit that Claude Code, the Agent SDK, and other Agent Skills clients all read. The plugin wrapper adds `agents/`, `hooks/`, and `evals/` only when the plugin is installed.
- `${CLAUDE_SKILL_DIR}` resolves for personal, project, and plugin installs, so scripts keep working in every install location ([skills](https://code.claude.com/docs/en/skills.md#available-string-substitutions), [skills, install levels](https://code.claude.com/docs/en/skills.md#share-skills)).
- `claude plugin eval` needs a plugin directory with a manifest, so the manifest is required for the eval suite ([plugin-evals, requirements](https://code.claude.com/docs/en/plugin-evals.md#requirements)).

---

## 1. SKILL.md format

### 1.1 Frontmatter fields (Claude Code)

Source: [skills, frontmatter reference](https://code.claude.com/docs/en/skills.md#frontmatter-reference). Field names are lowercase with hyphens, except `when_to_use`. Every field is optional, and only `description` is recommended. Unknown fields are ignored without error. Boolean fields accept true/false, yes/no, on/off, 1/0.

| Field | Meaning |
| :- | :- |
| `name` | Command name in the `/` menu. Defaults to the directory name. |
| `description` | What the skill does and when to use it. Claude uses it to decide when to load the skill. Falls back to the first non-empty body line if omitted. |
| `when_to_use` | Extra trigger context (phrases, example requests). Appended to `description`; counts toward the same 1,536-character cap. |
| `argument-hint` | Autocomplete hint for arguments, e.g. `[init\|update\|validate]`. |
| `arguments` | Named positional arguments for `$name` substitution. Space-separated string or YAML list. |
| `disable-model-invocation` | `true` stops Claude from loading the skill automatically. Also keeps it out of subagent preloading. Default `false`. |
| `user-invocable` | `false` hides the skill from the `/` menu so only Claude can invoke it. Default `true`. |
| `allowed-tools` | Tools usable without a permission prompt during the turn that invokes the skill. String or YAML list. Does not restrict other tools. Cleared on the next user message. |
| `disallowed-tools` | Tools removed from Claude's pool while the skill is active. Cleared on the next user message. |
| `model` | Model override for the current turn (`/model` values or `inherit`). With `context: fork`, sets the subagent model. |
| `effort` | `low`, `medium`, `high`, `xhigh`, or `max` for the current turn. With `context: fork`, sets the subagent effort. |
| `context` | `fork` runs the skill in a forked subagent context. |
| `agent` | Subagent type used with `context: fork`: `Explore`, `Plan`, `general-purpose` (default), or a custom agent. |
| `background` | Only with `context: fork`. `false` waits for the subagent result in the invoking turn. Default `true`. |
| `hooks` | Hooks registered on invocation and kept for the rest of the session. |
| `paths` | Glob patterns limiting automatic loading to matching files (relative to cwd). |
| `shell` | Shell for `` !`command` `` blocks: `bash` (default) or `powershell`. |
| `metadata` | Free-form YAML map for your own tooling. Claude Code ignores it. |
| `license` | Spec field. Accepted, not acted on by Claude Code. |
| `compatibility` | Spec field, up to 500 characters. Accepted, not acted on by Claude Code. |

Source for the table: [skills, frontmatter reference](https://code.claude.com/docs/en/skills.md#frontmatter-reference).

Example from the same page:

```yaml
---
name: fix-issue
description: Fix a GitHub issue
argument-hint: [issue-number]
disable-model-invocation: true
allowed-tools: Bash(gh *) Read Edit
---
```

### 1.2 Name and description limits

- **Claude Code `name`:** the frontmatter page does not state a maximum length. It lists disallowed characters (control characters, `<`, `>`, and others) ([skills, frontmatter reference](https://code.claude.com/docs/en/skills.md#frontmatter-reference)). **[UNVERIFIED]** exact Claude Code length cap.
- **Agent Skills spec `name`:** 1 to 64 characters; lowercase letters, digits, hyphens; must not start or end with a hyphen or contain `--`; must match the parent directory name ([agentskills spec](https://agentskills.io/specification)).
- **Claude API / claude.ai upload `name`:** max 64 characters; lowercase letters, numbers, hyphens; no XML tags; reserved words `anthropic` and `claude` are not allowed ([API skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)).
- **`description`:** the Claude Code listing truncates `description` plus `when_to_use` at 1,536 characters; put the key use case first ([skills, frontmatter reference](https://code.claude.com/docs/en/skills.md#frontmatter-reference)). The spec allows 1 to 1,024 characters ([agentskills spec](https://agentskills.io/specification)). The API allows 1,024 characters and no XML tags ([API skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)). Plan for the 1,024 limit so the description is portable.
- **`compatibility`:** 1 to 500 characters ([agentskills spec](https://agentskills.io/specification)).
- Angle brackets in `description` display as `&lt;` and `&gt;`; use `[branch]` or `argument-hint` instead ([skills, troubleshooting](https://code.claude.com/docs/en/skills.md#troubleshooting)).

### 1.3 How the description drives triggering

Claude reads `description` and `when_to_use` to decide whether to load the skill. Invocation depends on frontmatter ([skills](https://code.claude.com/docs/en/skills.md#how-the-description-drives-triggering)):

| Frontmatter | User can invoke | Claude can invoke | Description in context |
| :- | :- | :- | :- |
| (default) | Yes | Yes | Yes |
| `disable-model-invocation: true` | Yes | No | No |
| `user-invocable: false` | No | Yes | Yes |

Listing budget: the skill listing scales at 1% of the model context window. When it overflows, Claude Code drops descriptions starting with the least-used skills. Tune with `skillListingBudgetFraction`, `skillListingMaxDescChars`, or `skillOverrides` ([skills, descriptions are cut short](https://code.claude.com/docs/en/skills.md#skill-descriptions-are-cut-short)).

Guidance from the docs:
- Include keywords users would naturally say ([skills, troubleshooting](https://code.claude.com/docs/en/skills.md#troubleshooting)).
- Make the description specific if the skill triggers too often; add `disable-model-invocation: true` if only manual use is wanted ([skills, troubleshooting](https://code.claude.com/docs/en/skills.md#troubleshooting)).
- Spec: say both what the skill does and when to use it ([agentskills spec](https://agentskills.io/specification)).

For a vault generator that writes many files, `disable-model-invocation: true` is a reasonable default for `init` and `update`, so the skill does not start unprompted. This is a recommendation, not something the docs require. The docs' own `fix-issue` example uses this setting for a side-effecting task.

### 1.4 Body length

- Keep `SKILL.md` under 500 lines and move detailed reference material into supporting files ([skills, body length](https://code.claude.com/docs/en/skills.md#body-length)).
- The rendered body stays in context across turns, so every line is a recurring cost ([skills, body length](https://code.claude.com/docs/en/skills.md#body-length)).
- Spec: instructions under 5,000 tokens recommended ([agentskills spec](https://agentskills.io/specification)).
- Compaction can keep only the start of an invoked skill, so put the most important instructions first ([skills, troubleshooting](https://code.claude.com/docs/en/skills.md#troubleshooting)).

### 1.5 Portable frontmatter subset

Outside Claude Code (claude.ai uploads, the Skills API, packaging), only `name`, `description`, `license`, `compatibility`, `metadata`, and `allowed-tools` are accepted. Other fields cause a hard error at packaging or upload ([skills, portability](https://code.claude.com/docs/en/skills.md#portability)).

The spec defines `allowed-tools` as a space-separated string and labels it experimental ([agentskills spec](https://agentskills.io/specification)). Use the string form to match the spec, since Claude Code also accepts a YAML list.

---

## 2. Progressive disclosure

### 2.1 Layout and loading

- Spec layout: `SKILL.md`, plus optional `scripts/`, `references/`, `assets/`, and any other files ([agentskills spec](https://agentskills.io/specification)).
- Loading levels: metadata (~100 tokens) at startup; the `SKILL.md` body when triggered; resources only when needed ([agentskills spec](https://agentskills.io/specification), [API skills overview, levels](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)).
- Reference links: use relative paths from the skill root, one level deep from `SKILL.md`. Avoid nested reference chains ([agentskills spec, file references](https://agentskills.io/specification)).
- Reference files: keep them focused, since agents load them on demand ([agentskills spec](https://agentskills.io/specification)).

### 2.2 Scripts: executed vs read

- Scripts are run through the shell tool. Only their output enters context, not the script source ([API skills overview, how Skills work](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)).
- Reference files are read into context only when the instructions point at them ([API skills overview, Level 3](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)).
- Claude Code example that runs a bundled script via the skill directory variable, with the script path fixed in the body ([skills, visual output example](https://code.claude.com/docs/en/skills.md#generate-visual-output)):

```markdown
python3 ${CLAUDE_SKILL_DIR}/scripts/visualize.py .
```

- Pre-approve a script so it runs without a prompt, using the same variable in `allowed-tools` ([skills, string substitutions](https://code.claude.com/docs/en/skills.md#available-string-substitutions)):

```yaml
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/validate_vault.py *)
```

- Scripts should be self-contained or document dependencies, print helpful errors, and handle edge cases ([agentskills spec, scripts](https://agentskills.io/specification)). The Claude Code example uses only the Python standard library so nothing needs installing ([skills, visual output example](https://code.claude.com/docs/en/skills.md#generate-visual-output)).

### 2.3 Path variables

From [skills, string substitutions](https://code.claude.com/docs/en/skills.md#available-string-substitutions):

| Variable | Expands to |
| :- | :- |
| `${CLAUDE_SKILL_DIR}` | Directory containing `SKILL.md`. Works in body and `allowed-tools`. |
| `${CLAUDE_PROJECT_DIR}` | Project root. |
| `${CLAUDE_PLUGIN_ROOT}` | Plugin install directory (plugin skills only). |
| `${CLAUDE_PLUGIN_DATA}` | Persistent plugin data directory (plugin skills only). |
| `${CLAUDE_SESSION_ID}`, `${CLAUDE_EFFORT}` | Session ID and effort level. |

Note on portability: `${CLAUDE_SKILL_DIR}` is a Claude Code substitution. Spec-style relative paths are the portable alternative ([agentskills spec, file references](https://agentskills.io/specification)). **[UNVERIFIED]** whether Codex or Gemini CLI expand `${CLAUDE_SKILL_DIR}`; they probably do not.

Claude Code also documents `${CLAUDE_PLUGIN_ROOT}` as available to hook commands, MCP servers, LSP servers, and skill/agent Markdown content ([plugin manifest, environment variables](https://code.claude.com/docs/en/plugins/manifest-reference.md#environment-variables)).

### 2.4 Validation tools

- Spec validator: `skills-ref validate ./my-skill` ([agentskills spec, validation](https://agentskills.io/specification)).
- Claude Code: `claude plugin validate <path>`; for skills directories, `claude plugin validate ~/.claude/skills` also works; requires v2.1.233 or later ([skills, troubleshooting](https://code.claude.com/docs/en/skills.md#troubleshooting)). `--strict` fails on warnings too ([plugin manifest, validate](https://code.claude.com/docs/en/plugins/manifest-reference.md#validate-the-manifest)).

---

## 3. Arguments and sub-commands (`init`, `update`, `validate`)

### 3.1 Mechanisms

- `$ARGUMENTS` (all arguments as typed), `$ARGUMENTS[N]` or `$N` (0-based), and `$name` mapped from `arguments` ([skills, string substitutions](https://code.claude.com/docs/en/skills.md#available-string-substitutions)).
- Indexed arguments use shell-style quoting, so `/my-skill "hello world" second` sets `$0` to `hello world` ([skills, string substitutions](https://code.claude.com/docs/en/skills.md#available-string-substitutions)).
- If no placeholder receives arguments, Claude Code appends `ARGUMENTS: <value>` ([skills](https://code.claude.com/docs/en/skills.md#available-string-substitutions)).
- Plugin skills are namespaced: a skill named `init` in plugin `obsidian-graph-doc` runs as `/obsidian-graph-doc:init` ([plugin create, plugin skills](https://code.claude.com/docs/en/plugins/create.md#plugin-layout)).

### 3.2 Two options

**Option A (recommended): one entry skill with a mode argument.**

```yaml
---
name: docs
description: Generate or update an Obsidian-style docs/ vault for a codebase ...
argument-hint: [init|update|validate]
disable-model-invocation: true
---

Mode: $0. Read the matching file from ${CLAUDE_SKILL_DIR}/references/ and follow it:
- init -> references/mode-init.md
- update -> references/mode-update.md
- validate -> references/mode-validate.md
```

Why:
- One description means one listing entry and one trigger surface. Separate skills each add their own description to the listing budget ([skills, listing budget](https://code.claude.com/docs/en/skills.md#skill-descriptions-are-cut-short)).
- Each mode's procedure is a reference file loaded only for that mode, which fits progressive disclosure ([agentskills spec](https://agentskills.io/specification)).
- Invocation becomes `/obsidian-graph-doc:docs init`, `... update`, `... validate`.

This is a design recommendation. The docs do not prescribe a pattern for multi-mode skills.

**Option B: one skill per mode** (`skills/init/`, `skills/update/`, `skills/validate/`). Each is discoverable and has its own description, which helps tuning. It costs more listing budget and duplicates shared instructions. Use it if each mode needs different `allowed-tools` or `context` settings; `allowed-tools`, `context`, and `model` are per-skill fields ([skills, frontmatter reference](https://code.claude.com/docs/en/skills.md#frontmatter-reference)).

### 3.3 Per-mode settings

Per-skill fields that could differ by mode: `allowed-tools`, `context`, `agent`, `model`, `effort`, `disable-model-invocation` ([skills, frontmatter reference](https://code.claude.com/docs/en/skills.md#frontmatter-reference)). If `init` and `validate` need different settings, Option B is the only way to set them independently.

---

## 4. Subagents from a skill

### 4.1 Forked skill

`context: fork` makes the skill body the task prompt for a new subagent of the type in `agent`. The subagent does not see conversation history, so the body must be self-contained. Use it only for skills with an explicit task. `background: false` waits for the result ([skills, execution fields](https://code.claude.com/docs/en/skills.md#execution-fields)).

```yaml
---
name: docs-init
context: fork
agent: general-purpose
---
```

### 4.2 Fan-out from the main skill

The skill body can instruct Claude to spawn several subagents, each with a self-contained brief. Custom agents shipped in a plugin's `agents/` directory can be used by name (plugin agents are namespaced, e.g. `plugin:name`) ([sub-agents, file locations](https://code.claude.com/docs/en/sub-agents.md#file-locations-and-precedence)).

Subagent frontmatter (from [sub-agents, frontmatter reference](https://code.claude.com/docs/en/sub-agents.md#frontmatter-fields)): only `name` and `description` are required. Fields: `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `autoCompactWindow`, `skills`, `mcpServers`, `hooks`, `memory`, `background`, `omitClaudeMd`, `effort`, `isolation` (`worktree`), `color`, `initialPrompt`, `experimental`. Names are camelCase. `name` up to 256 characters; cannot contain `:` or start with `-`.

Plugin subagents ignore `hooks`, `mcpServers`, and `permissionMode`. Those must ship in `hooks/hooks.json` and `.mcp.json` instead ([sub-agents, plugin subagent restrictions](https://code.claude.com/docs/en/sub-agents.md#plugin-subagent-restrictions)). `tools` is not on the ignored list.

Built-in subagent types: `Explore` (read-only), `Plan` (read-only), `general-purpose` (all tools), `statusline-setup`, `claude-code-guide`, and `claude` ([sub-agents, built-in subagents](https://code.claude.com/docs/en/sub-agents.md#built-in-subagents)).

### 4.3 Limits

- Nesting: the docs say subagents can spawn their own subagents by default, up to three layers below the main conversation. Set `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` to `1` to turn nesting off. Remove `Agent` from a subagent's `tools`, or add it to `disallowedTools`, to stop one subagent from spawning ([sub-agents, nesting](https://code.claude.com/docs/en/sub-agents.md)). Note: this contradicts a common assumption that subagents cannot spawn subagents. For this skill, design for at most two levels: the main skill fans out, and workers do not fan out again.
- Concurrency: the sub-agents page links a "concurrent subagent limit" section. **[UNVERIFIED]** its value; I did not read that section.
- Dynamic workflows: a JavaScript script orchestrates many subagents with `agent()`, `pipeline()`, and `parallel()`. Limits from [workflows, behavior and limits](https://code.claude.com/docs/en/workflows.md#behavior-and-limits):
  - Up to 16 concurrent agents by default (1 to 256 via `CLAUDE_CODE_WORKFLOW_MAX_CONCURRENT_AGENTS`, v2.1.269+).
  - Up to 4,096 items per `parallel()` or `pipeline()` call.
  - 1,000 agents total per run.
  - No direct filesystem or shell access from the script itself; agents do the work.
  - No `import()` in the script.
  - Available on paid plans, with API access, and on Bedrock, Vertex, and Foundry. On Pro, enable it from `/config` ([workflows, intro](https://code.claude.com/docs/en/workflows.md)).
  - Saved workflows live in `.claude/workflows/` or `~/.claude/workflows/`. Plugin workflows live in `workflows/` and run as `/<plugin>:<name>` ([workflows, distribute](https://code.claude.com/docs/en/workflows.md#distribute-a-workflow-in-a-plugin)).
  - **[UNVERIFIED]** whether a skill body can launch a workflow directly. The docs describe Claude writing or running one from a prompt or a saved command.
- Workflows are useful for large audits (one agent per module), but they cost more tokens, and the docs warn that runs count toward plan usage ([workflows, cost](https://code.claude.com/docs/en/workflows.md#cost)).

### 4.4 Subagent results and handoff

Pass subagents a self-contained brief and have them write large raw output to a file, returning the path and a short summary. This keeps the main context small. It also needs a rule for what a subagent must return (exact paths, line numbers, verbatim values). That is a general delegation practice rather than a Claude Code feature, so no citation.

---

## 5. Distribution

### 5.1 Plugin structure

Source: [plugins, create](https://code.claude.com/docs/en/plugins/create.md#plugin-layout), [plugin manifest, standard layout](https://code.claude.com/docs/en/plugins/manifest-reference.md#standard-layout).

| Path | Contents |
| :- | :- |
| `.claude-plugin/plugin.json` | Manifest. Only this file goes in `.claude-plugin/`. |
| `skills/<name>/SKILL.md` | One directory per skill. |
| `agents/*.md` | Subagent definitions. Subfolder names become part of the agent name. |
| `hooks/hooks.json` | Hook config, top-level `"hooks"` key. |
| `commands/*.md` | Legacy flat command files. Use `skills/` for new plugins. |
| `.mcp.json` | MCP server definitions. |
| `.lsp.json` | LSP servers. |
| `output-styles/`, `themes/`, `workflows/`, `monitors/monitors.json` | Other component types. |
| `bin/` | Executables added to the Bash tool's `PATH` while enabled. Cannot be installed on claude.ai chat or Cowork ([platform support](https://claude.com/docs/plugins/platform-support#compare-component-support-by-app)). |

Plugin root skill: a plugin with `SKILL.md` at its root, no `skills/`, and no `skills` key loads as a single skill ([manifest, standard layout](https://code.claude.com/docs/en/plugins/manifest-reference.md#standard-layout)).

### 5.2 Manifest fields (`.claude-plugin/plugin.json`)

Source: [plugin manifest, fields](https://code.claude.com/docs/en/plugins/manifest-reference.md#fields).

| Field | Type / notes |
| :- | :- |
| `name` | **Required.** Kebab-case. Namespaces every component. No spaces, `@`, or `:`. |
| `displayName` | UI label only. Not used for namespacing. |
| `version` | String, not semver-checked. Setting it pins users until you change it. |
| `description` | Short description shown in `/plugin`. |
| `author` | Object; `name` required, `email` and `url` optional. |
| `homepage`, `repository`, `license` | URL, URL, SPDX identifier. |
| `keywords` | Array of strings. |
| `metadata` | Free-form. Claude Code does not read it. |
| `defaultEnabled` | Boolean, default `true`. |
| `dependencies` | Plugins that must be enabled. |
| `userConfig` | Values prompted at enable time; `sensitive: true` stores in secure storage. |
| `skills` | Path or array. Adds to the default `skills/` scan. `"."` is the plugin root. |
| `commands`, `agents`, `outputStyles`, `workflows` | Replace the default directory scan. |
| `hooks` | Path, inline object, or array. Merges with `hooks/hooks.json`. |
| `mcpServers`, `lspServers` | Merges with `.mcp.json` / `.lsp.json`. |
| `experimental.evals` | Eval directory if not `evals/`. |

Paths must start with `./` and resolve inside the plugin root ([manifest, path rules](https://code.claude.com/docs/en/plugins/manifest-reference.md#path-rules)). Unknown top-level keys are stripped with a warning. Unknown keys inside `userConfig` are errors ([manifest, unrecognized fields](https://code.claude.com/docs/en/plugins/manifest-reference.md#unrecognized-fields)).

Minimal example:

```json
{
  "name": "obsidian-graph-doc",
  "description": "Generate an Obsidian-style docs/ vault for any codebase",
  "version": "0.1.0",
  "author": { "name": "<your name>" }
}
```

### 5.3 Marketplaces (`.claude-plugin/marketplace.json`)

Source: [create a marketplace](https://code.claude.com/docs/en/plugins/create-marketplace.md), [marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference.md).

- Required top-level keys: `name`, `owner`, `plugins` ([create a marketplace, step 2](https://code.claude.com/docs/en/plugins/create-marketplace.md)).
- Each plugin entry needs `name` and `source` ([create a marketplace](https://code.claude.com/docs/en/plugins/create-marketplace.md#add-plugin-entries)).
- Source types: relative path (inside the marketplace directory), `github`, `git-subdir`, `url`, `archive`, `npm`, `command` ([create a marketplace, choose a source](https://code.claude.com/docs/en/plugins/create-marketplace.md#choose-a-plugin-source)).
- Relative paths are written from the marketplace root, and must not contain `..` ([create a marketplace, rules](https://code.claude.com/docs/en/plugins/create-marketplace.md#rules-for-plugin-entries)).
- Keep the entry `name` and the manifest `name` identical ([create a marketplace](https://code.claude.com/docs/en/plugins/create-marketplace.md#keep-the-entry-name-and-the-manifest-name-the-same)).
- `renames` maps old names to new names, or to `null` to remove, so users migrate instead of breaking ([host a marketplace, renames](https://code.claude.com/docs/en/plugins/host-marketplace.md#migrate-users-with-a-renames-map)).
- Reserved names: official marketplace names (for example `claude-plugins-official`) are refused for third-party marketplaces ([plugin security, marketplace tiers](https://code.claude.com/docs/en/plugins/security.md#identify-anthropics-marketplaces-by-name)).
- **[UNVERIFIED]** whether one repo can be both plugin root and marketplace root, with `plugin.json` and `marketplace.json` both in `.claude-plugin/`. The marketplace docs describe a plugin at the marketplace root, and say `.claude-plugin/` holding `marketplace.json` without `plugin.json` still loads its plugin folders. Test with `claude plugin validate .`.

Example entry for a root-level plugin (**[UNVERIFIED]** until tested):

```json
{
  "name": "obsidian-graph-doc",
  "owner": { "name": "<your name>" },
  "plugins": [
    { "name": "obsidian-graph-doc", "source": "./", "description": "Generate an Obsidian-style docs/ vault" }
  ]
}
```

### 5.4 Install commands

From [create a marketplace, step 4](https://code.claude.com/docs/en/plugins/create-marketplace.md) and [host a marketplace](https://code.claude.com/docs/en/plugins/host-marketplace.md#host-your-marketplace):

```
/plugin marketplace add <owner>/<repo>
/plugin install obsidian-graph-doc@<marketplace-name>
claude plugin marketplace add <owner>/<repo>
claude plugin install obsidian-graph-doc@<marketplace-name>
claude plugin update obsidian-graph-doc@<marketplace-name>
claude --plugin-dir ./                  # load this checkout for one session
```

Skills directory plugins load every session with no install step. A folder under `~/.claude/skills/` with `.claude-plugin/plugin.json` is treated as one ([plugin create, make a plugin load in every session](https://code.claude.com/docs/en/plugins/create.md#make-a-plugin-load-in-every-session)). Admins can block this ([plugin loading](https://code.claude.com/docs/en/plugins/loading.md#skills-directory-plugins-blocked-by-managed-settings)).

Personal and project skill locations ([skills, share skills](https://code.claude.com/docs/en/skills.md#share-skills) and [Agent SDK skills](https://code.claude.com/docs/en/agent-sdk/skills.md)):
- `~/.claude/skills/<name>/SKILL.md` (personal)
- `.claude/skills/<name>/SKILL.md` (project, commit to git)

### 5.5 Versioning

- Setting `version` pins users to that version until you change it ([manifest, version](https://code.claude.com/docs/en/plugins/manifest-reference.md#version)).
- Options: bump `version` on every release, or omit it so users track commits ([host a marketplace, release a new version](https://code.claude.com/docs/en/plugins/host-marketplace.md#release-a-new-version)).
- Do not set `version` in both `plugin.json` and the marketplace entry. `plugin.json` wins without warning, and validation reports the mismatch ([host a marketplace](https://code.claude.com/docs/en/plugins/host-marketplace.md#release-a-new-version)).
- If you bump, users who have not updated keep the old copy until they run `claude plugin update` or enable auto-update ([host a marketplace, keep users up to date](https://code.claude.com/docs/en/plugins/host-marketplace.md#keep-users-up-to-date)).
- Recommendation: semver in `plugin.json`, bumped on each release, and no `version` in the marketplace entry. The docs do not prescribe semver; this is a choice.

### 5.6 One repo, both plugin and plain skill

The Claude Code docs support three install paths for the same content. Verified:

1. **Marketplace or `--plugin-dir`:** the whole plugin: skill, subagents, hooks, evals.
2. **Skills directory:** clone or copy the whole repo to `~/.claude/skills/obsidian-graph-doc/`. Its `.claude-plugin/plugin.json` makes it a skills-directory plugin, so agents and hooks come along ([plugin create](https://code.claude.com/docs/en/plugins/create.md#make-a-plugin-load-in-every-session)).
3. **Plain skill copy:** copy only `skills/docs/` to `~/.claude/skills/docs/` or `.claude/skills/docs/`. Only the skill arrives. `agents/`, `hooks/`, and `evals/` do not.

Design consequences:
- Put anything the skill must have in `skills/docs/`. Keep `agents/` and `hooks/` as optional enhancements.
- Use `${CLAUDE_SKILL_DIR}` for script paths so they resolve in all three paths.
- If the skill needs a subagent in path 3, use `general-purpose` with a self-contained prompt. This avoids a dependency on a plugin-only agent name.
- **[UNVERIFIED]** whether a skill's `agent:` field accepts a plugin-namespaced name such as `obsidian-graph-doc:module-mapper`. Test before relying on it.

### 5.7 Surfaces: claude.ai, Desktop, Agent SDK, API

| Surface | What loads | Notes |
| :- | :- | :- |
| Claude Code (terminal, IDE, desktop Code tab) | Skills, plugins: skills, agents, hooks, MCP, commands, `bin/` | Full harness. Skill scripts run with the user's permissions and full network access ([API skills overview, runtime constraints](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview#runtime-environment-constraints)). |
| claude.ai chat and Claude desktop chat | Skills (zip upload on paid plans with code execution). Plugin skills and commands load. Agents and hooks are ignored. Local MCP servers ignored. | Skill upload accepts only the portable frontmatter subset ([platform support](https://claude.com/docs/plugins/platform-support#compare-component-support-by-app), [API skills overview, claude.ai](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview#claude-ai)). Network access depends on user and admin settings. |
| Cowork | Skills, agents, hooks, remote MCP. Local MCP only when the session runs on the user's computer. | [platform support](https://claude.com/docs/plugins/platform-support#compare-component-support-by-app) |
| Agent SDK (`claude-agent-sdk`, `@anthropic-ai/claude-agent-sdk`) | Skills loaded from the filesystem via `setting_sources` / `settingSources` (must include `"user"` and `"project"`), or from a plugin path. Control with `skills="all"` or a list of names. `skills` option needs the Skill tool in `allowed_tools` if you also set `tools`. | [Agent SDK, skills](https://code.claude.com/docs/en/agent-sdk/skills.md). The Agent SDK is the Claude Code harness you host yourself. It is not Managed Agents. |
| Claude API (Messages API) | Pre-built `pptx`, `xlsx`, `docx`, `pdf`, or custom skills uploaded via `/v1/skills`, referenced by `skill_ids` in `container`. Requires the code execution tool. | No network access. No runtime package install. Only pre-installed packages ([API skills overview, API](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview#claude-api)). Custom skills are workspace-wide. |
| Managed Agents | Skills in the agent's `skills` array, or loaded from a GitHub repo mounted on the session. | [API skills overview, support table](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview#api-support) |

Key differences for this skill:
- **No subagents** on claude.ai or Chat, since agents are ignored there. On the API, there is no harness with subagents unless you build one. The Agent SDK does have subagents. **[UNVERIFIED]** whether subagents are offered in claude.ai's code-execution environment.
- **No network** on the API. Claude.ai depends on settings. Claude Code and the Agent SDK have full network access.
- **No script installs** on the API. Helper scripts must use only pre-installed packages, so the Python-standard-library rule matters most there.
- **Custom skills do not sync across surfaces.** Upload separately to claude.ai and the API ([API skills overview, cross-surface](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview#cross-surface-availability)).

---

## 6. Portability beyond Claude

### 6.1 The open standard

- The Agent Skills format was developed by Anthropic and released as an open standard. The spec lives at [agentskills.io/specification](https://agentskills.io/specification), with development on [GitHub](https://github.com/agentskills/agentskills) ([agentskills overview](https://agentskills.io/)).
- The Agent Skills reference validator is `skills-ref` ([agentskills spec, validation](https://agentskills.io/specification)).
- **[UNVERIFIED]** the full list of clients. The [client showcase](https://agentskills.io/clients.md) is rendered client-side and my fetch returned no list.

### 6.2 Other agents I could confirm

- **Gemini CLI.** Based on the open standard. Discovers `.gemini/skills/` and `.agents/skills/` in the workspace, and `~/.gemini/skills/` and `~/.agents/skills/` for user skills. Activates skills with an `activate_skill` tool. The page says Gemini CLI was replaced by Antigravity CLI on June 18, 2026, for unpaid and Google One users ([Gemini CLI skills](https://geminicli.com/docs/cli/skills/)). Check the current name before publishing compatibility claims.
- **OpenAI Codex.** Scans `.agents/skills` in the current directory, each parent up to the repo root, `$REPO_ROOT/.agents/skills`, `~/.agents/skills`, `/etc/codex/skills`, and bundled system skills. Requires `name` and `description`. Optional `agents/openai.yaml` for UI metadata, implicit-invocation policy, and MCP dependencies. Follows symlinked skill folders ([Codex skills](https://learn.chatgpt.com/docs/build-skills); the old `developers.openai.com/codex/skills` URL redirects here). Codex plugin manifest format **[UNVERIFIED]**.
- **obsidianmd/obsidian-skills** (a real multi-tool example). The README lists `claude plugin marketplace add obsidianmd/obsidian-skills`, `codex plugin marketplace add obsidianmd/obsidian-skills`, `npx skills add https://github.com/obsidianmd/obsidian-skills`, and a manual clone into `~/.opencode/skills/obsidian-skills` ([obsidian-skills](https://github.com/obsidianmd/obsidian-skills)). The search index lists it as `kepano/obsidian-skills`. I did not confirm the redirect.
- **Cursor.** The obsidian-skills repo has a `.cursor-plugin/` directory and installs from the Cursor marketplace. I did not verify Cursor's skill-discovery paths.
- **Copilot.** **[UNVERIFIED]**. Not checked.

### 6.3 Writing portably

Portable core (spec-only):
- `SKILL.md` with `name` (matching the directory), `description`, and optionally `license`, `compatibility`, `metadata`, and `allowed-tools` as a space-separated string.
- Scripts and references referenced by relative path from the skill root.
- Body written as plain instructions, not as Claude-only directives.

Claude-specific (keep but mark, or confine to the Claude-only layer):
- Frontmatter: `context`, `agent`, `hooks`, `disable-model-invocation`, `user-invocable`, `arguments`, `argument-hint`, `model`, `effort`, `paths`, `shell`, `when_to_use`, `disallowed-tools`, `background`.
- Substitutions: `$ARGUMENTS`, `$N`, `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`, `` !`command` `` injection.
- Plugin machinery: `plugin.json`, `marketplace.json`, `agents/`, `hooks/hooks.json`, `workflows/`, `evals/`, `claude plugin eval`.
- Subagent names and tools (`Agent`, `Explore`, `general-purpose`).
- `/skill-doctor`, `/doctor`, `/workflows`.

Practical rule: a standards-only `SKILL.md` plus `scripts/` and `references/` works in Claude Code and other clients. The Claude-specific layer (`agents/`, `hooks/`, `evals/`, `context: fork`) is an enhancement, not a requirement.

---

## 7. Testing and evaluating a skill

### 7.1 skill-creator

- Anthropic publishes `skill-creator` in `anthropics/skills` ([repo](https://github.com/anthropics/skills/tree/main/skills/skill-creator)). Its directory contains `agents/`, `assets/`, `eval-viewer/`, `references/`, `scripts/`, `LICENSE.txt`, and `SKILL.md` ([directory listing](https://github.com/anthropics/skills/tree/main/skills/skill-creator)).
- Claude Code docs: the skill-creator plugin writes `evals/evals.json`, spawns one subagent per case, grades assertions into `grading.json`, aggregates into `benchmark.json`, runs blind A/B between two skill versions, and generates should-trigger and should-not-trigger prompts to tune the description ([skills, run evals with skill-creator](https://code.claude.com/docs/en/skills.md#run-evals-with-skill-creator)).
- Its format is separate from `claude plugin eval`. The two do not read each other's case files ([plugin evals, intro](https://code.claude.com/docs/en/plugin-evals.md)).
- Background: [skill-creator announcement](https://claude.com/blog/improving-skill-creator-test-measure-and-refine-agent-skills); eval format: [agentskills evaluating skills](https://agentskills.io/skill-creation/evaluating-skills).

### 7.2 `claude plugin eval`

Source: [plugin evals](https://code.claude.com/docs/en/plugin-evals.md). Version requirement: Claude Code v2.1.269 or later ([requirements](https://code.claude.com/docs/en/plugin-evals.md#requirements)).

- Suite layout: `evals/<case>/prompt.md` (frontmatter: `name`, `tags`, `plugins`, `runs` (default 3), `max_turns` (default 10), `timeout_seconds` (default 300), `allowed_tools`, `model`, `append_system_prompt`, `env` with `EVAL_*` keys) plus `evals/<case>/graders/<name>.md` ([prompt.md fields](https://code.claude.com/docs/en/plugin-evals.md#prompt-md-fields)). Optional `case.yaml` (needs `schema_version: "1.1"` and `name`) for `context.scaffold_script`, `context.history_file`, `context.add_dirs`.
- Graders: `regex`, `tool_used`, `tool_order`, `file_exists`, `llm`, `baseline` ([grader types](https://code.claude.com/docs/en/plugin-evals.md#grader-types)).
- Trigger testing: `tool_used` with `tool: Skill` and an `input_match` for the skill name. This checks that Claude chose the skill on natural phrasing ([create your first suite](https://code.claude.com/docs/en/plugin-evals.md#create-your-first-eval-suite)). Such graders are excluded from the score in two-arm runs unless `arm: both` ([score against baseline](https://code.claude.com/docs/en/plugin-evals.md#compare-against-a-no-plugin-baseline)).
- Commands: `claude plugin eval init` (interview by default), `claude plugin eval init --bare <name>` (blank template), `claude plugin eval .` (run every case), `--case <glob>`, `--tag`, `--runs`, `--ablation none|with-without`, `--threshold` (default 1.0), `--json`, `--trust-plugin`, `--allow-tools`, `--mocks`, `--max-cost-usd` ([command options](https://code.claude.com/docs/en/plugin-evals.md#command-options)).
- CI: exit 0 on pass, 1 below threshold or on load error, 2 partial or auth failure, 130 interrupted, 143 terminated. Pass `--trust-plugin` in CI ([run evals in CI](https://code.claude.com/docs/en/plugin-evals.md#run-evals-in-ci)).
- Sandbox: each run is a `claude -p` child with a temporary home and workspace, and only the plugin under test loaded. Bash, Write, Edit, WebFetch, and WebSearch are denied unless granted. The Artifact tool is off in runs ([what a run can access](https://code.claude.com/docs/en/plugin-evals.md#what-a-run-can-access)).
- Results: `results/<timestamp>/aggregate-result.json` (`schemaVersion: 1`) and `report.html` ([read the results](https://code.claude.com/docs/en/plugin-evals.md#read-the-results)).
- Every run and judge grader is a real model call on the user's account ([requirements](https://code.claude.com/docs/en/plugin-evals.md#requirements)). Budget before running a large suite.

Suggested cases for this skill: a fresh-repo init on a small fixture; an update after one file changes; a validate run on a deliberately broken link; a trigger case (`tool_used: Skill`); and a negative trigger case where the request is unrelated.

### 7.3 `/skill-doctor`

- Shows skill usage and context-cost reporting. Interactively it opens the plugin manager's Stats tab; in `-p` and background sessions it prints text ([skills, find unused skills](https://code.claude.com/docs/en/skills.md#skill-descriptions-are-cut-short) links to `/skill-doctor`; the command's behavior is from the embedded plugin-eval reference supplied with this session).
- It is not a linter. Use `claude plugin validate` for structure and `claude plugin eval` for behavior ([plugin manifest, validate](https://code.claude.com/docs/en/plugins/manifest-reference.md#validate-the-manifest)).
- `/doctor` shows the skill listing's estimated context cost and largest contributors ([skills, descriptions are cut short](https://code.claude.com/docs/en/skills.md#skill-descriptions-are-cut-short)).

### 7.4 Trigger accuracy

- Trigger accuracy can be measured with `tool_used: Skill` graders over many prompts, rerun after each description change ([skills, troubleshooting](https://code.claude.com/docs/en/skills.md#troubleshooting)).
- Use skill-creator's description tuning for generating should-trigger and should-not-trigger sets ([skills, run evals with skill-creator](https://code.claude.com/docs/en/skills.md#run-evals-with-skill-creator)).

---

## 8. Hooks a docs skill could ship, and security

### 8.1 Hook mechanics

Source: [hooks reference](https://code.claude.com/docs/en/hooks.md), [hooks guide](https://code.claude.com/docs/en/hooks-guide.md).

- Plugin hooks go in `hooks/hooks.json` with a top-level `"hooks"` key ([plugin create, layout](https://code.claude.com/docs/en/plugins/create.md#plugin-layout)).
- Skill and subagent hooks go in frontmatter. A skill's hooks are registered on invocation and kept for the rest of the session. `once: true` removes a skill hook after its first successful run ([hooks, hooks in skill and agent frontmatter](https://code.claude.com/docs/en/hooks.md#hooks-in-skill-and-agent-frontmatter)).
- Subagent hooks run only while the subagent runs. Plugin subagents ignore `hooks` ([sub-agents, plugin restrictions](https://code.claude.com/docs/en/sub-agents.md#plugin-subagent-restrictions)).
- Events relevant here: `PostToolUse`, `PostToolUseFailure`, `PreToolUse`, `Stop`, `SubagentStop`, `SessionStart`, `SessionEnd`, `PreCompact`, `PostCompact`, `FileChanged`, `CwdChanged`, `InstructionsLoaded`, and others. The full list is in the [hooks reference](https://code.claude.com/docs/en/hooks.md).
- There is no git-commit event. A pre-commit-style check is a `PreToolUse` hook on `Bash` with an `if` filter such as `Bash(git commit *)` ([hooks reference, matcher and if](https://code.claude.com/docs/en/hooks.md#matcher-syntax-for-tool-events)). **[UNVERIFIED]** exact behavior of `if` on a `git commit` command in practice.
- Matchers: `"Write|Edit"` (exact list), `"mcp__server__.*"` (regex), `"*"` (all). Tool events match on `tool_name` ([hooks reference](https://code.claude.com/docs/en/hooks.md#matcher-syntax-for-tool-events)).
- Command hook fields: `type`, `command`, `args` (exec form, no shell), `timeout` (default 600 for command), `async`, `shell`, `if`, `statusMessage`, `once`, `onFailure` ([hooks reference, command hook fields](https://code.claude.com/docs/en/hooks.md#command-hook-fields)).
- Exit codes: 0 success; 2 blocks on blocking events (`PreToolUse`) and feeds stderr back; on `PostToolUse` exit 2 only shows stderr to Claude; other non-zero codes are non-blocking errors ([hooks reference, exit codes](https://code.claude.com/docs/en/hooks.md#exit-code-semantics)).
- Input arrives as JSON on stdin. The plugin docs example reads `.tool_input.file_path` with `jq` ([plugin create, convert](https://code.claude.com/docs/en/plugins/create.md#convert-an-existing-claude-setup)).

Example for a stale-note flag (illustrative, not tested). It is a `PostToolUse` hook that runs the validator on any edited `docs/*.md`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "args": ["${CLAUDE_PLUGIN_ROOT}/skills/docs/scripts/validate_vault.py", "--changed-only"],
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

Use exec form (`args`) so the plugin path is one argument without quoting ([plugin manifest, quoting](https://code.claude.com/docs/en/plugins/manifest-reference.md#quoting-and-path-separators)). **[UNVERIFIED]** that `validate_vault.py` accepts `--changed-only` and reads the file path from stdin. Both need writing.

To avoid blocking edits, use `PostToolUse` (exit 2 only informs Claude) rather than `PreToolUse`. Use `async: true` to run it in the background. Claude Code does not enforce `timeout` on async hooks ([hooks reference](https://code.claude.com/docs/en/hooks.md#command-hook-fields)).

### 8.2 Trust and security

- A plugin can run code on the user's machine with their privileges. Hooks, monitors, MCP servers, and LSP servers run outside the sandbox. Skills, commands, and agents enter Claude's context as instructions ([plugin security, what a plugin can do](https://code.claude.com/docs/en/plugins/security.md#understand-what-a-plugin-can-do)).
- Claude Code's permission rules and sandbox cover Claude's tool calls, not code a plugin runs by itself ([plugin security](https://code.claude.com/docs/en/plugins/security.md#understand-what-a-plugin-can-do)).
- Auto-update can change files after review, when auto-update is on for the marketplace ([plugin security](https://code.claude.com/docs/en/plugins/security.md#understand-what-a-plugin-can-do)).
- Review before install: check the details pane in `/plugin`, read `hooks/hooks.json`, `.mcp.json`, and everything in `bin/`, and run `claude plugin details <name>` ([plugin security, review before install](https://code.claude.com/docs/en/plugins/security.md#review-a-plugin-before-you-install)).
- Anthropic's API skills docs say the same for skills: use only trusted sources; audit scripts for unexpected network calls, file access, or operations outside the stated purpose; treat installing a skill like installing software ([API skills overview, security](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview#security-considerations)).
- Enterprise governance: Skill content scanning exists for custom skills uploaded in claude.ai and Cowork, not via the API ([API skills overview, security](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview#security-considerations)).
- Managed settings can disable `--plugin-dir`, restrict marketplaces, and block hooks outside managed settings ([plugin security, enforce](https://code.claude.com/docs/en/plugins/security.md#enforce-plugin-controls-for-your-organization)).

Expectations for a public skill that bundles scripts:
- Scripts should be read-only with respect to the user's source; the skill should write only into `docs/` and state that in SKILL.md.
- Narrow `allowed-tools` to specific script paths, such as `Bash(${CLAUDE_SKILL_DIR}/scripts/validate_vault.py *)`, not `Bash`. `allowed-tools` only pre-approves; it does not sandbox ([skills, frontmatter reference](https://code.claude.com/docs/en/skills.md#frontmatter-reference)).
- No network calls in scripts unless documented. Keep dependencies to the standard library so there is nothing to install and nothing to audit beyond the script.
- Document each script's inputs, outputs, exit codes, and what it writes.
- Ship a `LICENSE` and a `SECURITY.md` with a contact.
- Test with `claude plugin eval` and `--trust-plugin` only on code you have read. The eval docs say a passing suite is not a security vetting ([plugin evals, what a run can access](https://code.claude.com/docs/en/plugin-evals.md#what-a-run-can-access)).
- Avoid `` !`command` `` injection in the body unless necessary. It runs shell at load time ([skills, inject dynamic context](https://code.claude.com/docs/en/skills.md#inject-dynamic-context) via the Agent SDK page's link).

---

## 9. Public examples with a similar shape

1. **`skill-creator` in `anthropics/skills`**: [skills/skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator). Layout: `SKILL.md`, `LICENSE.txt`, plus `agents/`, `assets/`, `eval-viewer/`, `references/`, and `scripts/`. Why it matters: it bundles subagent definitions, a review viewer, and reference docs beside one skill. Its eval loop is the closest public model for "generate, then measure".

2. **`docx` in `anthropics/skills`**: [skills/docx](https://github.com/anthropics/skills/tree/main/skills/docx). Layout: `SKILL.md`, `LICENSE.txt`, `scripts/`. Why it matters: a document-generation skill with bundled scripts, a multi-step procedure, and Apache-2.0 licensing per the README ([anthropics/skills](https://github.com/anthropics/skills)). The other document skills (`pdf`, `pptx`, `xlsx`) follow the same top-level shape ([anthropics/skills, skill list](https://github.com/anthropics/skills/tree/main/skills)).

3. **`obsidian-skills` (`obsidianmd/obsidian-skills`)**: [repo](https://github.com/obsidianmd/obsidian-skills). Layout: `.claude-plugin/`, `.cursor-plugin/`, `.agents/plugins`, `plugins/obsidian/skills/<name>/` (7 skills: `obsidian-markdown`, `obsidian-bases`, `json-canvas`, `obsidian-cli`, `obsidian-headless`, `defuddle`, `knap`), `scripts/bump.sh`, `LICENSE`, `README.md`. Why it matters: it is the closest domain match (Obsidian Flavored Markdown, wikilinks, properties, canvas). It ships one plugin with several skills and installs into Claude Code, Codex, and generic `npx skills` clients from one repo. Mirrors this skill's plan to have one plugin root with a `skills/` directory.

4. **`claude-plugins-official`**: [plugins directory](https://github.com/anthropics/claude-plugins-official/tree/main/plugins). Includes `plugin-dev`, `feature-dev`, `skill-creator`, `agent-sdk-dev`, `hookify`, and `mcp-server-dev`. Why it matters: these are official examples of plugins that combine skills, agents, and hooks. I saw only the directory names, so their internal layout is **[UNVERIFIED]**. Read `plugins/plugin-dev` before copying its structure.

5. **Official plugin docs example layout**: the `deploy-tools/` tree in the manifest reference shows `skills/`, `commands/`, `agents/`, `hooks/`, `monitors/`, `output-styles/`, `themes/`, `workflows/`, `bin/`, `scripts/`, `.mcp.json`, `.lsp.json` in one plugin ([manifest reference, standard layout](https://code.claude.com/docs/en/plugins/manifest-reference.md#standard-layout)). A reference for a full plugin, not a published project.

---

## Open questions and unverified items

1. Claude Code maximum length for `name`. Docs do not state it. Spec and API both use 64.
2. Whether `agent:` in a skill accepts a plugin-namespaced agent name, and whether it resolves when the skill is copied without the plugin.
3. Whether one repo can hold `plugin.json` and `marketplace.json` together in `.claude-plugin/`, with the plugin at the marketplace root (`"source": "./"`). Test with `claude plugin validate .`.
4. Supporting-files section of the Claude Code skills page was not in the portion I read. Confirm the exact convention and whether Claude Code resolves relative script paths against the skill directory.
5. Whether non-Claude clients (Codex, Gemini CLI) expand `${CLAUDE_SKILL_DIR}`. Assume no.
6. Full client list from agentskills.io. The page did not render it.
7. Codex plugin manifest format and `$CODEX_HOME` as a discovery location. The Codex page did not confirm either.
8. Claude API skills upload endpoint details and beta header names. I read the overview only, not the skills guide.
9. Agent SDK plugins option (`plugins` path loading). Not read; the skills page mentions it.
10. Whether claude.ai's code-execution environment offers subagents. Not documented on the pages read.
11. Concurrent subagent limit value, in the sub-agents page section I did not read.
12. Whether a skill can launch a dynamic workflow directly, as opposed to a prompt asking Claude to write one.
13. Exact PostToolUse stdin fields beyond `tool_input.file_path`. Read the full hooks reference before writing the stale-note hook.
14. `if` filter behavior on `git commit` in a PreToolUse hook. Test.
15. Whether claude.ai's skill upload limits (size, file count) are documented. Not checked.
16. Whether `skill-creator`'s `eval-viewer/` and `agents/` directories are reusable without the Anthropic plugin. Read its SKILL.md and README.
17. Whether Gemini CLI's rename to Antigravity CLI changes its skill paths. The page said the CLI was replaced; check current docs before claiming compatibility.
18. `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` default of 3 was taken from the sub-agents page summary; confirm on the live page.
19. The embedded `/skill-doctor` and `claude plugin eval` reference was supplied with this session. The public plugin-evals page covers the eval command; confirm `/skill-doctor` on the public skills page before citing it as documented.
20. Version policy: this report recommends semver in `plugin.json`. That is a choice, not something the docs require.
