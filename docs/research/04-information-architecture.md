# 04 - Information architecture: notes, links, grounding, and freshness

Research date: 2026-11-14/15. Every external claim carries a URL. Claims I could only confirm through secondary sources are marked **(unverified)**. Sections separate **Evidence** from **Opinion**; the recommendations are my opinion unless a source is cited next to them.

## Summary of recommendations

1. **Write what the code cannot say.** The strongest controlled study found that LLM-generated repository context files did not improve agent success, raised cost by about 20%, and that generated overviews did not help agents find files faster. They helped only when the repository's other documentation was removed ([Gloaguen et al., ICLR 2026](https://arxiv.org/html/2602.11988)). This is a direct risk to the project's agent-facing goal. The design below answers it in three ways: notes are read on demand instead of loaded up front, structural facts are extracted by tooling instead of written by an LLM, and prose is limited to purpose, invariants, non-obvious behaviour and rationale.
2. **Default note-type set: 10 types.** Always: `index`, `overview`, `module`. When detected in the code: `interface`, `data-model`, `external`, `flow`, `concept`. Human-led, generated only from existing evidence: `decision`, `guide`. Opt-in: `symbol`, `config`, `test-suite`.
3. **The `module` note is the backbone**, one per package/directory-level unit, nested with `part_of`. Stop at module level by default. C4 itself recommends against long-lived code-level documentation ([c4model.com](https://c4model.com/diagrams/code)).
4. **Eight typed links, stored one way, inverses derived**: `part_of`, `depends_on`, `implements`, `reads`, `writes`, `about`, `supersedes`, `see_also`. Plain body wikilinks count as an untyped ninth kind, `mentions`. Four are derivable from code; four are judgement calls and are labelled as such in the graph export.
5. **Flat frontmatter only.** Obsidian does not support nested properties or Markdown in properties, and links in properties must be quoted ([Obsidian help](https://obsidian.md/help/properties)).
6. **Ground every note with `sources` globs plus a content hash**, with `verified_commit` kept as audit data. Staleness is decided by content hash, not by git history, as Codocia does ([Codocia README](https://docs.rs/crate/codocia/0.1.3/source/README.md)).
7. **Two-phase update.** Phase A is deterministic and uses no LLM: re-extract facts, rewrite machine regions, rebuild `graph.json`, mark stale notes. Phase B uses the LLM only on notes whose sources changed in a way that matters, plus a bounded set of neighbours.
8. **Protect human text** with marker-delimited generated regions (the terraform-docs pattern), a per-note `owner` field, and region hashes that detect human edits inside generated regions.
9. **Entry points**: a short `docs/index.md`, a machine-readable `docs/_graph/graph.json`, and a pointer of under 15 lines in `AGENTS.md`/`CLAUDE.md` that includes a "code wins over docs" sentence. A study found agents followed a stale instruction file over the code in 90.1% of choices, and one added sentence reversed that ([Xu and Wu, 2026](https://arxiv.org/abs/2610.30571)).
10. **Measure before claiming benefit.** No benchmark I found tests agents traversing a wikilinked Markdown vault. The project should ship with a small eval (with vault vs without) before promising token or accuracy gains.

---

## 1. Note granularity and taxonomy

### Evidence

**C4** defines five nested abstractions: person, software system, container (application or data store), component, and code ([c4model.com/abstractions](https://c4model.com/abstractions)). On the code level it says: "This level of detail is not recommended for anything but the most important or complex components", and "Recommended? No, particularly for long-lived documentation because most IDEs can generate this level of detail on demand" ([c4model.com/diagrams/code](https://c4model.com/diagrams/code)).

**arc42** has 12 sections: introduction and goals, constraints, context and scope, solution strategy, building block view, runtime view, deployment view, crosscutting concepts, architecture decisions, quality requirements, risks and technical debt, glossary ([docs.arc42.org](https://docs.arc42.org/home/)).

**Diataxis** sorts documentation on two axes, action vs cognition and acquisition vs application, giving tutorial, how-to guide, reference, and explanation ([diataxis.fr/compass](https://diataxis.fr/compass/)).

**MADR 4.0.0** (released 2024-09-17) has required sections "Context and Problem Statement", "Considered Options", "Decision Outcome", optional "Decision Drivers", "Consequences", "Confirmation", "Pros and Cons of the Options", "More Information", and optional YAML front matter `status`, `date`, `decision-makers`, `consulted`, `informed` ([adr.github.io/madr](https://adr.github.io/madr/)).

**Zettelkasten atomicity** aims for "one knowledge building block per note" and is described as "not a rigid law, but a guiding compass" ([zettelkasten.de/atomicity/guide](https://zettelkasten.de/atomicity/guide/)).

**Existing LLM documentation tools:**

| Tool | Unit of documentation | Source |
|---|---|---|
| RepoAgent | One doc per class/function, in a project tree (repo, directories, files, classes/functions). Sections: Functionality, Parameters, Code Description, Notes, Examples | [arXiv 2402.16667](https://arxiv.org/html/2402.16667v1) |
| CodeWiki | Feature-oriented module tree. Leaf modules are documented by agents, parents synthesized bottom-up from child docs. Leaf threshold 32,768 tokens, max delegation depth 3 (Appendix G.2) | [arXiv 2510.24428](https://arxiv.org/html/2510.24428v5) |
| DeepWiki (Devin) | Page-level wiki. Max 30 pages, 80 on enterprise; steerable through `.devin/wiki.json` | [docs.devin.ai](https://docs.devin.ai/work-with-devin/deepwiki) |
| Karpathy "LLM Wiki" | Summary, entity, concept, comparison and overview pages, plus `index.md` and `log.md` | [gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) |
| Meta tribal-knowledge files | 59 files for 4,100+ source files. Each is 25-35 lines (~1,000 tokens) with four sections: Quick Commands, Key Files, Non-Obvious patterns, See Also | [engineering.fb.com](https://engineering.fb.com/2026/04/06/developer-tools/how-meta-used-ai-to-map-tribal-knowledge-in-large-scale-data-pipelines/) |
| Graphify | Graph nodes from AST and LLM extraction; exports `graph.json`, a report, an Obsidian vault and a wiki with `index.md` | [README](https://raw.githubusercontent.com/Graphify-Labs/graphify/main/README.md) |

**What developers put in agent context files:** in 2,303 files from 1,925 repositories, implementation details appeared in 69.9%, architecture in 67.7%, build and run commands in 62.3%, while security and performance requirements appeared in 14.5% each ([Agent READMEs, arXiv 2511.12884](https://arxiv.org/html/2511.12884v1)).

### Opinion: which units get a note

The test for a note type is: does it hold knowledge that (a) cannot be read cheaply from one file of code, and (b) has an identifiable set of source files that can prove it stale? Units that fail (a) should be machine-generated tables inside another note, not notes of their own. Units that fail (b) should be human-owned.

| Candidate unit | Verdict | Reason |
|---|---|---|
| Repo overview | `overview` note, always | arc42 sections 1, 3, 4. One note |
| Index / MOC | `index` note, always | Agent entry point (section 6) |
| Subsystem / package / directory | `module` note, always | The backbone. Maps to C4 container and component, arc42 building block view |
| File | Not a note by default | Listed in the owning module's "Key files" table. Promote to a `module` note with `level: file` only for large or central files |
| Class / function | `symbol` note, opt-in | C4 advises against it; RepoAgent-style per-symbol docs restate code. Use only for hot spots chosen by centrality or by the user |
| Data model / schema | `data-model` note, when detected | Shared by many modules, so it belongs to none of them |
| API endpoint, CLI command, event, public library API | `interface` note with a `kind` field, when detected | One note per coherent group (a router, a command group), not per endpoint |
| External dependency | `external` note, when significant | Only dependencies that shape the design (framework, database, queue, paid API). The rest stay in the manifest file |
| Concept / domain term | `concept` note, when detected | arc42 sections 8 and 12. Small repos can use one glossary note instead |
| Flow / sequence | `flow` note, when detected | arc42 runtime view. The main cross-module knowledge that code search does not give |
| Decision | `decision` note, human-led | MADR-compatible. Never invented by the LLM; imported from existing ADRs, or drafted from commit and PR evidence and marked `status: proposed` |
| How-to / runbook | `guide` note, human-led | Diataxis how-to. Generated only where commands are verifiable (build, test, release scripts) |
| Config / env var | `config` note, opt-in | Default is a machine-generated table in the owning module note |
| Test suite | `test-suite` note, opt-in | Default is a `tests` glob field on the module note |
| Tutorial | Out of scope | Needs a human teaching intent; not derivable |
| Risks / tech debt, quality requirements | Out of scope for generation | Sections in `overview` if the humans supply them |

### Common frontmatter (all types)

All keys are flat because Obsidian does not support nested properties ([Obsidian help](https://obsidian.md/help/properties)). Link values are quoted wikilinks for the same reason. `tags` and `aliases` are Obsidian's own default properties ([Obsidian help](https://obsidian.md/help/properties)).

```yaml
---
id: mod-auth-session            # stable; equals the file basename; never reused
type: module                    # one of the closed type set
title: Session management
summary: Issues, refreshes and revokes login sessions backed by Redis.   # one sentence; reused in index and graph.json
status: current                 # current | stale | needs-review | proposed | deprecated
owner: generated                # generated | mixed | human
tags: [auth]
aliases: [sessions]
# grounding (section 4)
sources: ["src/auth/session/**", "src/auth/tokens.py"]
source_hash: "sha256:9f2c..."   # hash over the sorted (path, git blob id) list matched by sources
verified_commit: "4be1f0a"      # audit only; staleness is decided by source_hash
verified_at: 2026-11-14
generator: "skill-name@0.3.0"
confidence: high                # high | medium | low; applies to the prose, not to extracted facts
# typed links (section 2); each is a list of quoted wikilinks
part_of: ["[[mod-auth]]"]
depends_on: ["[[mod-db-redis]]", "[[ext-pyjwt]]"]
implements: ["[[if-auth-http-api]]"]
reads: ["[[dm-user]]"]
writes: ["[[dm-session]]"]
see_also: ["[[flow-login]]"]
---
```

### Per-type templates

Body sections marked **(M)** are machine-written from extracted facts and sit inside generated-region markers (section 5). Sections marked **(P)** are LLM prose. Sections marked **(H)** are human-owned.

**`index`** (one; for very large repos, one per area)

```yaml
type: index
scope: "/"                      # path prefix this index covers
note_count: 84
graph: "_graph/graph.json"
```
Body: how to use this vault (5 lines) · notes grouped by type, each as `[[id]] - summary` **(M)** · stale-note list **(M)**.

**`overview`** (one)

```yaml
type: overview
languages: [python, typescript]
entry_points: ["src/cli/main.py", "src/server/app.py"]
build_commands: ["make build"]
test_commands: ["make test"]
```
Body: Purpose **(P)** · System context: users and external systems **(P)** · Top-level modules table **(M)** · Solution strategy, 3-6 bullets **(P)** · How to build, test, run **(M, taken from scripts and CI config)** · Constraints and quality goals **(H, optional)**.

**`module`**

```yaml
type: module
level: component                # system | container | component | file
language: python
entry_points: ["src/auth/session/__init__.py"]
tests: ["tests/auth/test_session*.py"]
owners: ["@team-identity"]      # copied from CODEOWNERS if present; a string, not a link
loc: 1840                       # machine-derived size, used for scaling decisions
```
Body: Purpose, 2-4 sentences **(P)** · Responsibilities and non-responsibilities **(P)** · Key files, 3-7 rows of path and role **(M)** · Public surface: exported symbols with signatures **(M)** · Dependencies table: target, kind, evidence path **(M)** · Invariants and non-obvious behaviour, each with a source reference **(P)** · Configuration table **(M)** · Human notes **(H)**.

**`interface`**

```yaml
type: interface
kind: http                      # http | cli | event | library | rpc | file-format
stability: public               # public | internal | experimental
spec: "openapi/auth.yaml"       # machine-readable spec if one exists
```
Body: Purpose **(P)** · Operations table: name, inputs, outputs, handler path **(M)** · Auth, errors, versioning rules **(P)** · Consumers **(M, derived inverse of `depends_on`)**.

**`data-model`**

```yaml
type: data-model
kind: table                     # table | document | message | struct | file
store: postgres
schema_source: "migrations/0042_sessions.sql"
```
Body: Meaning **(P)** · Fields table **(M)** · Invariants and lifecycle **(P)** · Readers and writers **(M, derived from `reads` and `writes`)** · Migration notes **(H)**.

**`external`**

```yaml
type: external
package: "pkg:pypi/pyjwt@2.9.0" # Package URL where available
scope: runtime                  # runtime | build | dev | test | optional
license: MIT
homepage: "https://example.org"
```
Body: What we use it for **(P)** · Where it is wrapped or isolated **(M)** · Version constraints and upgrade hazards **(P/H)**. No summary of the library's own documentation.

**`flow`**

```yaml
type: flow
trigger: "POST /login"
about: ["[[mod-auth-session]]", "[[if-auth-http-api]]", "[[dm-session]]"]
```
Body: Outcome in one sentence **(P)** · Numbered steps, each naming a note and a source reference **(P, grounded)** · Failure paths **(P)** · Optional Mermaid sequence diagram **(P)**.

**`concept`**

```yaml
type: concept
kind: domain-term               # domain-term | pattern | crosscutting
about: ["[[mod-auth-session]]"]
```
Body: Definition, 1-3 sentences **(P)** · How it appears in the code: names, types, where enforced **(P, grounded)** · Not to be confused with **(P)**.

**`decision`** (MADR-compatible)

```yaml
type: decision
status: accepted                # proposed | accepted | rejected | deprecated | superseded
date: 2025-03-02
decision-makers: ["@alice"]     # MADR field names kept as-is
owner: human
about: ["[[mod-auth-session]]"]
supersedes: ["[[adr-0007-cookie-sessions]]"]
```
Body uses the MADR headings unchanged ([adr.github.io/madr](https://adr.github.io/madr/)): Context and Problem Statement · Considered Options · Decision Outcome · Consequences.

**`guide`**

```yaml
type: guide
kind: how-to                    # how-to | runbook
owner: mixed
about: ["[[mod-auth-session]]"]
commands_verified: true         # the commands exist in scripts or CI at verified_commit
```
Body: Goal · Preconditions · Steps with exact commands · Verification · Rollback (runbooks).

**Opt-in types**

```yaml
type: symbol                    # class or function hot spot
symbol: "src/auth/session/store.py#SessionStore.rotate"
kind: method
signature: "rotate(self, sid: str) -> Session"
part_of: ["[[mod-auth-session]]"]
```
```yaml
type: config
keys: ["SESSION_TTL", "REDIS_URL"]
defined_in: ["src/config/settings.py"]
```
```yaml
type: test-suite
runner: pytest
command: "pytest tests/auth"
about: ["[[mod-auth-session]]"]
```

### Opinion: note size

Target 150 to 400 words of prose per note and roughly 60 lines in total. Split a note that passes about 150 lines. Supporting evidence is indirect: Meta's files are 25-35 lines and about 1,000 tokens ([Meta](https://engineering.fb.com/2026/04/06/developer-tools/how-meta-used-ai-to-map-tribal-knowledge-in-large-scale-data-pipelines/)); Claude Code's documentation says to "target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence" ([Claude Code memory docs](https://code.claude.com/docs/en/memory)); Chroma's report finds model performance degrades as input length grows and that topically related distractors make it worse ([Chroma, Context Rot](https://trychroma.com/research/context-rot)). None of these measured optimal length for code documentation notes.

---

## 2. Relationship vocabulary

### Evidence: what existing ontologies distinguish

| Ontology | Relationships | Notes | Source |
|---|---|---|---|
| Backstage catalog | `ownedBy`/`ownerOf`, `providesApi`/`apiProvidedBy`, `consumesApi`/`apiConsumedBy`, `dependsOn`/`dependencyOf`, `parentOf`/`childOf`, `memberOf`/`hasMember`, `partOf`/`hasPart` | Seven pairs. Declared on one side in `spec.*`; both directions are generated. The list is stated to be non-exhaustive | [backstage.io](https://backstage.io/docs/features/software-catalog/well-known-relations) |
| C4 | Containment hierarchy plus free-text labelled relationships between elements | No fixed relationship vocabulary | [c4model.com](https://c4model.com/abstractions) |
| UML dependencies | Usage («use», «call», «create», «instantiate», «send»); abstraction («derive», «refine», «trace»); realization («realize») | Definitions vary by tool vendor | [IBM docs](https://www.ibm.com/docs/SS8PJ7_9.7.0/com.ibm.xtools.modeler.doc/topics/cdepend.html), [Microsoft docs](https://learn.microsoft.com/en-Us/visualstudio/modeling/standard-stereotypes-for-uml-models?view=vs-2015) (via search summaries, **partly unverified**) |
| SCIP | Symbol relationships `is_reference`, `is_implementation`, `is_type_definition`, `is_definition`; occurrence roles Definition, Import, WriteAccess, ReadAccess, Generated, Test, ForwardDefinition | Symbol string grammar: `<scheme> ' ' <package> ' ' (<descriptor>)+`, where package is manager, name, version | [scip.proto](https://raw.githubusercontent.com/sourcegraph/scip/main/scip.proto) |
| Kythe | Edge kinds such as `childof`, `defines`, `defines/binding`, `extends`, `satisfies`, `ref`, `ref/call`, `ref/imports`; reverse edges written with a `%` prefix | Fine-grained, symbol level | [kythe.io/docs/schema](https://kythe.io/docs/schema/) |
| SPDX 2.3 | 45 relationship types, nine about dependencies: `DEPENDS_ON`, `DEPENDENCY_OF`, `DEPENDENCY_MANIFEST_OF`, `BUILD_DEPENDENCY_OF`, `DEV_DEPENDENCY_OF`, `OPTIONAL_DEPENDENCY_OF`, `PROVIDED_DEPENDENCY_OF`, `TEST_DEPENDENCY_OF`, `RUNTIME_DEPENDENCY_OF` | Scope is encoded in the relationship type | [SPDX 2.3.1](https://spdx.github.io/spdx-spec/v2.3.1/relationships-between-SPDX-elements/) |
| CycloneDX | `dependencies[].ref` with a `dependsOn` list; recommends Package URL for `bom-ref`; scope is a component attribute | Scope is an attribute of the node, not a relationship type | [cyclonedx.org](https://cyclonedx.org/use-cases/software-dependencies) (scope and `provides` details from secondary sources, **unverified**) |
| schema.org | `SoftwareSourceCode`: `codeRepository`, `programmingLanguage`, `runtimePlatform`, `targetProduct`; inherited `isPartOf`/`hasPart`, `isBasedOn`, `about`, `mentions` | Document-level, not code-level | [schema.org](https://schema.org/SoftwareSourceCode) |
| SKOS | `broader`/`narrower` are inverses; `related` is symmetric | For concept schemes | [W3C SKOS Reference](https://www.w3.org/TR/2009/PR-skos-reference-20090615/skos.html) |
| LSIF, CodeQL | Symbol-level reference and definition graphs, and relational code databases | Not checked in this research; **unverified**, listed for completeness | [LSIF spec](https://microsoft.github.io/language-server-protocol/specifications/lsif/0.6.0/specification/), [CodeQL docs](https://codeql.github.com/docs/) |

Two findings from documentation tools matter for the size of the set:

- CodeWiki extracts function calls, class inheritance, attribute access and module imports, then maps them all to a single `depends_on` relation so the scheme works across languages ([arXiv 2510.24428](https://arxiv.org/html/2510.24428v5)).
- Graphify tags every edge `EXTRACTED`, `INFERRED`, or `AMBIGUOUS` so "you always know what was found vs guessed" ([README](https://raw.githubusercontent.com/Graphify-Labs/graphify/main/README.md)).

### Opinion: recommended closed set

Design rules: (1) each link type is stored on one side only, on the note whose `sources` prove it; (2) every inverse is derived into `graph.json` and shown by Obsidian backlinks; (3) scope and kind are attributes, as in CycloneDX, not separate link types, as in SPDX; (4) symbol-level distinctions (call, import, inherit) collapse into `depends_on`, as in CodeWiki, and survive as an edge attribute in `graph.json`.

| Link | Definition | Direction (stored on) | Derived inverse | Derivable from code? | Borrowed from |
|---|---|---|---|---|---|
| `part_of` | Source is contained in, or owned by, the target. Forms a tree; one parent per note | child → parent (child) | `has_part` | **Objective** for directory and package nesting. Judgement when the generator regroups files into feature modules | Backstage `partOf`, schema.org `isPartOf`, C4 containment |
| `depends_on` | Source needs the target to build or run: import, call, inheritance, spawned process, network call | dependent → dependency (dependent) | `used_by` | **Objective** for static imports, calls, and manifest entries. **Judgement** for runtime coupling that is not visible statically (HTTP between services, queues, reflection, config-driven wiring) | Backstage `dependsOn`, SPDX `DEPENDS_ON`, CycloneDX `dependsOn`, UML usage |
| `implements` | Source provides the behaviour that the target specifies. Target is an `interface` or `concept` note | implementer → specification (module) | `implemented_by` | **Mostly objective**: route registrations, interface or trait implementations, CLI registrations. Judgement for concepts | Backstage `providesApi`, UML realization, SCIP `is_implementation` |
| `reads` | Source reads instances of the target data model | module or flow → data-model | `read_by` | **Semi-objective**: ORM and query analysis finds most; raw SQL and dynamic access need judgement | SCIP `ReadAccess` |
| `writes` | Source creates, updates or deletes instances of the target data model | module or flow → data-model | `written_by` | **Semi-objective**, as for `reads` | SCIP `WriteAccess` |
| `about` | Source note exists to explain, constrain or operate the target. Used by `flow`, `concept`, `decision`, `guide`, `test-suite` | explanatory note → subject | `described_by` | **Judgement**. Partly checkable: the two notes' `sources` should overlap | schema.org `about`, Backstage `consumesApi` for the "documents" role |
| `supersedes` | Source replaces the target, which should be `deprecated` or `superseded` | new → old | `superseded_by` | **Judgement** (human for decisions) | ADR practice, MADR status |
| `see_also` | Non-hierarchical association not covered above. Symmetric. Maximum five per note | either side | itself | **Judgement** | SKOS `related`, Meta's "See Also" section |
| `mentions` (untyped) | Any plain `[[wikilink]]` in the body | from body text | backlink | Derived from the note text, not from code | schema.org `mentions` |

Deliberately left out:

- `owned_by`: ownership points at people or teams, which are not notes. It is a string field `owners`, copied from CODEOWNERS.
- `tested_by`: a `tests` glob field on the module note unless `test-suite` notes are enabled, in which case the suite uses `about`.
- `consumes_api`: a `depends_on` link whose target is an `interface` note says the same thing.
- `calls`, `imports`, `extends`: edge attribute `kind` in `graph.json`.
- `broader`/`narrower` for concepts: `part_of` between concept notes covers it.

### Storing typed links in Obsidian

Evidence:

- Internal links in properties "must be surrounded with quotes"; nested properties and Markdown in properties are unsupported ([Obsidian help](https://obsidian.md/help/properties)).
- Since desktop 1.4.5, "properties with links" show in backlinks ([changelog 1.4.5](https://obsidian.md/changelog/2023-08-31-desktop-v1.4.5), via search snippet).
- Desktop 1.11.4 (2026-01-12): "Markdown links are now supported in text and list properties" and "Internal links are automatically updated when the destination file is moved or renamed" ([changelog 1.11.4](https://obsidian.md/changelog/2026-01-12-desktop-v1.11.4/)).
- Whether the core graph view draws edges for links that exist only in properties is **unverified**. Forum threads disagree, and a recent one asks for a way to hide frontmatter links from the graph, which suggests they now appear ([forum thread](https://forum.obsidian.md/t/an-option-to-disable-frontmatter-links-to-show-up-in-graph-view/114940)).
- The core graph view has no edge types. Typed edges need a community plugin such as Breadcrumbs, which reads both frontmatter links and Dataview-style `key:: [[note]]` inline fields ([Breadcrumbs docs](https://publish.obsidian.md/breadcrumbs-docs/Explicit+Edge+Builders/Typed+Links)).
- Bases is a core plugin that gives filterable table views over file properties, stored as `.base` YAML files ([Obsidian help](https://help.obsidian.md/bases)).

Opinion: frontmatter list properties are the canonical store, because they are trivially machine-readable (any YAML parser, `grep`, Bases, Dataview) and need no plugin. The machine-written "Dependencies" table in the body repeats the same targets as plain wikilinks, which guarantees the core graph view shows them whatever the answer to the unverified point above. Use unique basenames equal to `id` (`mod-`, `if-`, `dm-`, `ext-`, `flow-`, `con-`, `adr-`, `guide-` prefixes) so that `[[id]]` resolves without paths.

---

## 3. What actually helps coding agents

### Evidence table

| Finding | Source | Strength |
|---|---|---|
| LLM-generated context files lowered resolution rate by 0.5% (SWE-bench Lite, p = 0.87) and 2% (AGENTbench, p = 0.37); developer-written ones raised it 2.4% (p = 0.21). Developer-written beat LLM-generated by 7% (p = 0.038). LLM-generated files raised cost 20-23% and added 2.5 to 3.9 steps | [Gloaguen et al., arXiv 2602.11988, ICLR 2026](https://arxiv.org/html/2602.11988) | **Strong** for its setting: peer-reviewed, four agents, controlled. Limits: Python only, issue-fixing only, success differences mostly not significant |
| Codebase overviews in context files did not reduce the steps needed to reach the files the fix touched; "context files are not effective at providing a repository overview" | same | Strong for its setting |
| With all other documentation removed, LLM-generated files improved performance by 2.7% on average. The authors read this as redundancy with existing docs | same | Moderate (one ablation, Claude Code excluded for cost) |
| Authors' advice: omit LLM-generated context files for now; human-written ones should "only include instructions required for coding agents that are not already present in the README" | same | Author recommendation |
| An AGENTS.md file was associated with 28.64% lower median runtime and 16.58% fewer median output tokens over 124 PRs in 10 repositories | [Lulla et al., arXiv 2601.20404](https://arxiv.org/abs/2601.20404) | **Weak to moderate**: short workshop paper, association not causation, measures efficiency not correctness |
| A compressed 8 KB docs index in AGENTS.md reached 100% on Next.js 16 API evals; baseline 53%; an on-demand skill 53%, or 79% with explicit instructions. The skill was never invoked in 56% of cases | [Vercel blog](https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals) | **Moderate**: vendor eval on APIs absent from training data; clear effect size |
| 59 context files of about 1,000 tokens each for a 4,100-file pipeline gave "roughly 40% fewer tool calls and tokens per task" in preliminary tests on six tasks. "Context that decays is worse than no context at all." Files are re-validated every few weeks | [Meta Engineering](https://engineering.fb.com/2026/04/06/developer-tools/how-meta-used-ai-to-map-tribal-knowledge-in-large-scale-data-pipelines/) | **Weak**: six tasks, internal, uncontrolled. Useful as a design example for proprietary code |
| Curated skills raised pass rate by 16.2 points on average; self-generated skills gave no reliable benefit (-1.3 points); 16 of 84 tasks got worse with curated skills | [SkillsBench, arXiv 2602.12670](https://arxiv.org/html/2602.12670v1) | **Moderate to strong** benchmark; about procedural skills, not codebase docs |
| When an instruction file conflicted with the code, 90.1% of agent choices followed the stale file. Claude Code noted the conflict in 79 of 80 runs and still followed the file. One added sentence raised code-following from 4.2% to 91.4% | [Xu and Wu, arXiv 2610.30571](https://arxiv.org/abs/2610.30571) | **Moderate**: preprint, 40 synthetic Python projects, 320 runs |
| Misleading comments degrade LLM code reasoning (CodeCrash, NeurIPS 2025) and fault localization (ICST 2026) | [arXiv 2504.14119](https://arxiv.org/html/2504.14119v3), [arXiv 2504.04372](https://www.alphaxiv.org/abs/2504.04372.md) | Moderate; seen through search summaries, **details unverified** |
| Code changes that leave comments inconsistent are about 1.5 times more likely to introduce bugs (human developers, Apache Java projects) | [arXiv 2409.10781](https://arxiv.org/html/2409.10781v1) | Moderate; about humans, not agents |
| Repository graphs help localization: RepoGraph "substantially boosts the performance of all systems" when plugged into four SWE-bench methods | [RepoGraph, arXiv 2410.14684](https://arxiv.org/abs/2410.14684) | Moderate. The reported 32.8% average relative gain is from a secondary summary, **unverified**. These are symbol-level code graphs, not documentation graphs |
| Claude Code dropped an early RAG and local vector database design because "agentic search generally works better" | Attributed to Boris Cherny in secondary write-ups, e.g. [smartscope.blog](https://smartscope.blog/en/ai-development/practices/rag-debate-agentic-search-code-exploration/) | **Weak (unverified)**: anecdote, no published numbers |
| On a 511,959-document enterprise corpus, a file-system agent was best at small sizes; BM25 overtook it at about 10 million tokens, and the agent used about 39 times more query tokens | [arXiv 2607.26497](https://www.alphaxiv.org/abs/2607.26497.md) | Moderate; read through a summary, **unverified against the paper**; enterprise QA, not code |
| Agentic search narrows the gap to GraphRAG; GraphRAG keeps an edge on multi-hop questions | [arXiv 2604.09666](https://www.alphaxiv.org/abs/2604.09666.md) | Moderate; Wikipedia-style QA, **unverified against the paper** |
| Just-in-time context: agents "maintain lightweight identifiers (file paths, stored queries, web links, etc.)"; "Folder hierarchies, naming conventions, and timestamps all provide important signals"; aim for "the smallest set of high-signal tokens" | [Anthropic engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | Vendor guidance, no numbers |
| Aider sends a repo map of files and key symbol signatures, ranked with a graph algorithm, defaulting to a 1k-token budget | [aider.chat](https://aider.chat/docs/repomap.html) | Tool documentation; shows a working design, not a measured comparison |
| The Karpathy wiki pattern: the LLM reads `index.md` first; this "works surprisingly well at moderate scale (~100 sources, ~hundreds of pages)" | [gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) | Anecdote |
| OpenAI's harness-engineering post reportedly keeps AGENTS.md to about 100 lines as a table of contents into a structured `docs/` directory, with CI checks and a recurring doc-gardening agent | [openai.com](https://openai.com/index/harness-engineering/) | **Unverified**: the page returned HTTP 403; details are from secondary summaries |
| llms.txt: of roughly 38,000 sites with a valid file, 97% received zero requests for it in the month studied | Ahrefs study as reported by [ppc.land](https://ppc.land/llms-txt-adoption-rises-8-8x-but-97-of-files-get-zero-ai-requests/) | Weak (SEO industry data, **secondary**). It is about web crawlers, not about agents working in a repo |
| Claude Code's own documentation site tells agents to "Fetch the complete documentation index at: https://code.claude.com/docs/llms.txt" before exploring | [code.claude.com](https://code.claude.com/docs/en/memory) | Observation: an index-first entry point is used in practice for agent-facing docs |
| Hierarchical documentation (function to file) used for fault localization gave RepoRepair a 45.7% repair rate on SWE-bench Lite | [arXiv 2603.01048](https://arxiv.org/pdf/2603.01048) | Moderate; from search summary, **unverified** |

### What the evidence does and does not show

1. **"Why beats what" is supported only indirectly.** No study I found compares rationale content with descriptive content head to head. The indirect support: generated context files are redundant with what agents can already read ([Gloaguen et al.](https://arxiv.org/html/2602.11988)); the gains reported by Vercel and Meta come from knowledge missing from both training data and code ([Vercel](https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals), [Meta](https://engineering.fb.com/2026/04/06/developer-tools/how-meta-used-ai-to-map-tribal-knowledge-in-large-scale-data-pipelines/)); and models are poor authors of the procedural knowledge they benefit from ([SkillsBench](https://arxiv.org/html/2602.12670v1)).
2. **Always-loaded versus on-demand is a real tension.** Vercel found a passive index beat an on-demand skill because the skill often was not invoked. Gloaguen et al. found always-loaded files add cost without benefit. The two fit together if the always-loaded part is a very small pointer and index, and the detail is on demand.
3. **Stale docs are actively harmful to agents**, more than to humans, because agents rank instruction-like text above tool output ([Xu and Wu](https://arxiv.org/abs/2610.30571)).
4. **No vector index is needed at vault scale.** The vault is far below the roughly 10-million-token size at which keyword retrieval overtook a file-system agent in the one scale study above. `grep` over flat frontmatter plus `graph.json` should be enough. This is my inference, not a tested result.
5. **Nothing tests this project's exact shape**: an agent following typed wikilinks through a Markdown vault. Treat every benefit claim as a hypothesis.

### Opinion: content rules that follow

- A module note must not narrate the code. Its prose is limited to purpose, boundaries, invariants, failure modes, and things that surprised the generator. If the LLM has nothing non-obvious to say, the prose is two sentences and the note is mostly machine tables.
- Dependency lists come from extraction, never from the LLM's reading.
- The pointer in `AGENTS.md` stays tiny and is not an overview.
- Ship an eval harness (a handful of tasks per repo, with vault and without) as part of the skill.

---

## 4. Grounding and anti-hallucination

### Evidence

- **Swimm** couples docs to code through snippets, "smart tokens" and "smart paths", verifies them in CI, auto-syncs mechanical changes, and fails the check when a change needs a human ([Swimm docs](https://docs.swimm.io/new-to-swimm/benefits-of-code-coupled-documentation), [Swimm blog](https://swimm.io/blog/continuous-documentation-through-continuous-integration-with-swimm)).
- **Codocia** binds each page to code with `covers` globs in frontmatter, snapshots a content hash per matched file into `docs/.codocia-snapshot.json`, stores the commit as audit metadata only, and treats a pattern that matches no files as an error ("broken covers"). Its README warns that a passing check means the snapshot is current, not that the prose is correct ([Codocia README](https://docs.rs/crate/codocia/0.1.3/source/README.md)).
- **Graphify** labels edges `EXTRACTED`, `INFERRED` or `AMBIGUOUS` ([README](https://raw.githubusercontent.com/Graphify-Labs/graphify/main/README.md)).
- **Meta** runs automated jobs that "validate file paths, find coverage gaps, re-run quality critics, and auto-fix stale references" ([Meta](https://engineering.fb.com/2026/04/06/developer-tools/how-meta-used-ai-to-map-tribal-knowledge-in-large-scale-data-pipelines/)).
- **SCIP** gives a language-neutral symbol identifier: scheme, package (manager, name, version), descriptors ([scip.proto](https://raw.githubusercontent.com/sourcegraph/scip/main/scip.proto)).
- A study reportedly found about 20% of comments from a leading LLM contained factual errors (Kang, Milliken, Yoo, 2024). **Unverified**: known only through a secondary summary ([PromptLayer](https://www.promptlayer.com/research-papers/identifying-inaccurate-descriptions-in-llm-generated-code-comments-via-test-execution)).

### Opinion: grounding layers, from cheapest to strictest

| Layer | Mechanism | Checkable without an LLM? |
|---|---|---|
| 1. Note to files | `sources` globs. A glob that matches nothing is an error | Yes |
| 2. Note to content | `source_hash` over the sorted list of (path, git blob id) for matched files. `git ls-files -s` gives blob ids without reading file contents | Yes |
| 3. Note to time | `verified_commit` and `verified_at`. Audit only. Commits vanish under squash and rebase, so they cannot be the staleness test | Yes |
| 4. Fact to location | Inline references in prose and in machine tables, in the form `path#Symbol` (preferred) or `path:L10-L24` | Path and symbol existence: yes. Line ranges: only at `verified_commit` |
| 5. Fact to permalink | Optional: rendered links to the forge at `verified_commit`, so a line range stays correct for ever | Yes |
| 6. Machine vs prose | Machine-derived sections sit inside generated-region markers. LLM prose is outside them or in separately marked regions | Yes |
| 7. Edge provenance | Each edge in `graph.json` has `origin: extracted | inferred | human` and an `evidence` list | Extracted edges can be re-derived and diffed |
| 8. Note confidence | `confidence: high | medium | low`, set by the generator from how much prose is tied to references | No, heuristic |

Rules I recommend:

- **Prefer symbol anchors to line numbers.** Line ranges go stale on any edit above them. `path#Symbol` survives until the symbol is renamed, and a rename is exactly the event that should mark the note stale.
- **Every claim in an "Invariants and non-obvious behaviour" section carries a reference.** A lint pass rejects a bullet without one. This will not prove a claim true, but it gives a reviewer and a later verification pass something to check.
- **Never let the LLM write a dependency or a signature.** Those sections are produced by the extractor. If no extractor exists for a language, the fallback is LLM extraction with `origin: inferred` on every edge.
- **A verification pass**: after writing a note, a second pass (ideally a fresh context) receives only the note and the cited snippets and marks each claim supported, unsupported or unverifiable. Unsupported claims are removed. This is my suggestion; I found no measurement of how much it helps for documentation.

Example of grounded prose inside a module note:

```markdown
## Invariants and non-obvious behaviour
- A refresh rotates the session id; the old id is valid for a 10 s grace window so that
  parallel requests do not fail. (`src/auth/session/store.py#SessionStore.rotate`)
- Revocation is write-through to Redis and is **not** transactional with the user table.
  (`src/auth/session/revoke.py#revoke_all`, `src/auth/session/store.py#SessionStore.delete`)
```

---

## 5. Staleness and incremental update

### Evidence: how existing tools do it

| Tool | Detection | Update scope | Source |
|---|---|---|---|
| RepoAgent | Git pre-commit hook detects changed code objects | An object's doc is updated when its source changes, when a referrer stops referencing it, or when it gains a reference. Changes inside what it references do **not** trigger an update | [arXiv 2402.16667](https://arxiv.org/html/2402.16667v1) |
| CodeWiki 2.0 | `--update` diffs the saved dependency graph against the current code and repairs the module tree; `--compare-to` sets the base commit for CI and squashed merges | One agent per affected module patches its page. Falls back to a full build if too much changed | Project README via [mirror](https://gitee.com/shadowedge/CodeWiki), **unverified against the primary repo**. The paper itself lists version-aware docs as future work ([arXiv 2510.24428](https://arxiv.org/html/2510.24428v5)) |
| Codocia | `check --base main` compares stored content hashes with current files. Fails on stale pages, broken covers, missing covered files, changed code no page covers, and uncovered files | The agent reads each stale page with the matching diff, edits prose only if documented behaviour changed, then refreshes the snapshot. Formatting-only, test-only and comment-only diffs just refresh the snapshot | [Codocia README](https://docs.rs/crate/codocia/0.1.3/source/README.md) |
| Swimm | CI check compares coupled snippets, tokens and paths with the code | Auto-sync for mechanical changes; fail and flag for the rest | [Swimm blog](https://swimm.io/blog/continuous-documentation-through-continuous-integration-with-swimm) |
| Graphify | SHA256 cache of processed files; `--update`; `--watch` (AST only, no LLM); optional post-commit hook | Re-extracts changed files and merges them into the graph | [README](https://raw.githubusercontent.com/Graphify-Labs/graphify/main/README.md) |
| Karpathy wiki | A periodic `lint` operation: contradictions, stale claims, orphan pages, missing concept pages, missing cross-references; an append-only `log.md` | LLM-driven, periodic | [gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) |
| Meta | Automated jobs every few weeks validate file paths, find coverage gaps, re-run critics, fix stale references | Periodic refresh | [Meta](https://engineering.fb.com/2026/04/06/developer-tools/how-meta-used-ai-to-map-tribal-knowledge-in-large-scale-data-pipelines/) |
| Google Code Wiki | Reported to regenerate docs after each change; mechanism not published | Unknown | [InfoQ](https://infoq.com/news/2025/11/google-code-wiki/), **unverified** |
| Claude Code | `/doctor prompt-audit` checks instruction files for references to files or commands that do not exist and for contradictions | Proposes edits; changes nothing until asked | [Claude Code memory docs](https://code.claude.com/docs/en/memory) |
| terraform-docs | Writes only between `<!-- BEGIN_TF_DOCS -->` and `<!-- END_TF_DOCS -->`; `--output-check` verifies generated content is current | Region only; the rest of the file is human-owned | [terraform-docs README](https://cdn.jsdelivr.net/gh/terraform-docs/terraform-docs@master/README.md) (details via tutorials, **partly unverified**) |

### Opinion: recommended mechanism

**Phase A: deterministic check (no LLM, safe for pre-commit and CI)**

1. For each note, expand `sources`, compute `source_hash`, compare with the stored value. A mismatch puts the note in the *changed* set.
2. Re-run the extractor on changed files. Rewrite machine regions (key files, public surface, dependency tables) and the machine-owned link fields (`depends_on`, `part_of`, `implements`, `reads`, `writes` where extracted). Rebuild `graph.json`.
3. Report: stale notes; globs that match nothing; source files covered by no note; wikilinks to missing notes; notes whose `part_of` chain does not reach the root; edges present in frontmatter but missing from extraction, and the reverse.
4. Classify each changed note by diffing the *extracted facts* before and after:
   - **No fact change** (formatting, comments, internals only): re-stamp `source_hash` and `verified_commit` only if a cheap LLM or human review of the diff agrees that no documented behaviour changed. Otherwise set `status: needs-review`.
   - **Surface change** (exports, signatures, dependency edges, schema fields changed): the note goes to Phase B, and its neighbours are selected by the rules below.
5. In CI, exit non-zero if any note is stale and not updated in the same change. Provide a `--warn-only` mode for adoption.

**Phase B: LLM update (on demand through the skill, or a scheduled or PR job)**

For each note needing prose work, give the model the current note, the diff of its sources since `verified_commit` (or the full sources when that commit is unreachable), and the before and after extracted facts. Ask for the smallest edit to the prose regions. Then run the reference lint and re-stamp.

**Neighbour propagation rules** (adapted from RepoAgent's rule that a change inside a dependency does not by itself make dependents stale):

| What changed in note N | Who else is touched | How |
|---|---|---|
| Only internals (no fact change) | Nobody | - |
| N's `summary` or public surface | Notes with `depends_on`, `reads`, `writes` or `implements` → N (one hop inbound) | Machine: refresh their tables. LLM: only if they cite a symbol of N that changed or vanished |
| N's `summary` | N's `part_of` ancestors, and the index | Machine: refresh the child table. LLM: re-synthesize the parent prose only if the child's purpose changed |
| N's set of outbound edges | The targets' derived inverse lists | Machine only |
| N renamed, split, merged or deleted | Every note linking to N | Machine: rewrite links, keep the old id in `aliases`. LLM: only for `flow` notes that step through N |
| Sources of the subject of an `about` link changed at surface level | The `flow`, `concept`, `guide` and `decision` notes that are `about` it | `generated` and `mixed` notes go to Phase B; `human` notes get `status: needs-review` and are never rewritten |

Cap propagation at one hop for LLM work. Machine refreshes can go as far as they need to because they are cheap and deterministic.

**Where the hash lives.** Two workable choices:

- In each note's frontmatter (`source_hash`). The note is self-describing and parallel branches do not conflict on one shared file. The cost is frontmatter churn in diffs.
- In one lock file, as Codocia does. Notes stay clean, at the cost of a merge-conflict hot spot.

I lean to frontmatter for `source_hash` and `verified_commit`, with `graph.json` as a rebuildable derived file. See the open questions.

**Hooks.** A pre-commit hook should run Phase A's checks only, never an LLM, for speed and cost. RepoAgent does run generation in pre-commit ([arXiv 2402.16667](https://arxiv.org/html/2402.16667v1)); I think that is too slow and too expensive as a default. A scheduled "gardening" run of the lint, as Meta and the Karpathy pattern use, catches drift that hashes cannot: contradictions between notes and orphaned concepts.

**What hashes cannot catch.** A note can be wrong while its hash is current: the prose was wrong from the start, or it depends on behaviour outside its `sources`. Hence the uncovered-file report, the `about` propagation rule, and the periodic lint. Codocia's README makes the same point ([Codocia README](https://docs.rs/crate/codocia/0.1.3/source/README.md)).

### Preserving human edits

Recommended combination, in my opinion:

1. **Ownership per note.** `owner: generated` means the tool may rewrite everything. `owner: mixed` means the tool rewrites only inside generated regions. `owner: human` means the tool never changes the body and may only set `status: needs-review` and refresh machine-owned frontmatter fields. `decision` notes default to `human`, `guide` to `mixed`.
2. **Generated regions**, the terraform-docs pattern:

   ```markdown
   <!-- gen:begin deps sha256:1c7e... -->
   | Target | Kind | Evidence |
   |---|---|---|
   | [[mod-db-redis]] | import | `src/auth/session/store.py` |
   <!-- gen:end deps -->

   ## Human notes
   Anything here is never touched by the generator.
   ```
3. **Edit detection inside regions.** The hash in the opening marker is the hash of the region's content as the tool last wrote it. If the current content hashes differently, a human edited it. The tool must then not overwrite: it writes its new version next to it as a proposal, or flips the note to `owner: mixed` and moves the human text to "Human notes", and reports it.
4. **A reserved "Human notes" section** at the end of every generated note, so the obvious place to add knowledge is also the safe place.
5. **Frontmatter split.** Machine-owned keys: `sources` (unless hand-edited, see open questions), `source_hash`, `verified_*`, `generator`, extracted link lists, `loc`. Human-owned keys: `tags`, `aliases`, `owners`, `see_also`, and `status` when set to `deprecated`. The tool merges at key level and never rewrites the whole block.
6. **A log.** An append-only `docs/_graph/log.md` with one line per run (what was updated and why), following the Karpathy pattern, gives reviewers a way to audit generator behaviour.

How HTML comment markers display in each Obsidian view mode was not checked (**unverified**); test it before fixing the marker syntax. Obsidian's own `%% comment %%` syntax is an alternative.

---

## 6. Entry points and navigation for agents

### Evidence

- A passive index that is always in context outperformed a retrieval skill the agent had to choose to invoke ([Vercel](https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals)).
- Large always-loaded files cost tokens and reduce adherence. Claude Code's `@path` imports "help you organize a long file but don't reduce its context cost, because imported files load together with" the importing file. Path-scoped rules "load only when Claude works with matching files". Subdirectory `CLAUDE.md` files load on demand. Claude Code reads `AGENTS.md` when no `CLAUDE.md` exists (v2.1.277 or later) ([Claude Code memory docs](https://code.claude.com/docs/en/memory)).
- The Karpathy pattern has the LLM read `index.md` first; each entry is a link with a one-line summary ([gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)).
- Graphify writes a section into `CLAUDE.md` telling the agent to read its report before answering architecture questions, and can install a PreToolUse hook that fires before Glob and Grep calls ([augmentcode.com write-up](https://www.augmentcode.com/learn/graphify-knowledge-graph-codebase-skill), **secondary**).
- RepoGraph retrieves a k-hop ego graph around the symbols of interest and notes that a larger neighbourhood costs more tokens ([ICLR 2025 slides](https://www.iclr.cc/media/iclr-2025/Slides/28957.pdf), via search summary, **unverified**).
- One sentence telling the agent that the code is the truth when it conflicts with the instruction file moved code-following from 4.2% to 91.4% ([Xu and Wu](https://arxiv.org/abs/2610.30571)).

### Opinion: three entry points

**(a) Pointer in `AGENTS.md` / `CLAUDE.md`** (under 15 lines; do not `@import` the vault):

```markdown
## Codebase documentation
- `docs/` is an Obsidian vault of small notes about this codebase. Start at `docs/index.md`.
- To find the notes for a file: look the path up in `docs/_graph/graph.json` under `path_index`,
  or grep the `sources:` lines of the notes.
- Before changing a module, read its note and the one-line summaries of its `depends_on`
  and `used_by` neighbours. Read `decision` notes that are `about` it.
- Notes can be out of date. If a note disagrees with the code, the code is correct:
  follow the code and report the note as stale.
- Do not treat notes with `status: stale` or `status: needs-review` as reliable.
```

**(b) `docs/index.md`**: under about 150 lines. One line per note (`[[id]] - summary`), grouped by type. Past roughly 150 notes, the root index lists only top-level modules and per-area indexes.

**(c) `docs/_graph/graph.json`**: derived, rebuildable, never hand-edited.

```json
{
  "schema": 1,
  "generated_at_commit": "4be1f0a",
  "nodes": [
    {
      "id": "mod-auth-session",
      "type": "module",
      "path": "docs/modules/mod-auth-session.md",
      "title": "Session management",
      "summary": "Issues, refreshes and revokes login sessions backed by Redis.",
      "status": "current",
      "sources": ["src/auth/session/**", "src/auth/tokens.py"],
      "tokens": 640
    }
  ],
  "edges": [
    {
      "from": "mod-auth-session",
      "to": "mod-db-redis",
      "type": "depends_on",
      "kind": "import",
      "origin": "extracted",
      "evidence": ["src/auth/session/store.py#SessionStore"]
    }
  ],
  "path_index": {
    "src/auth/session/store.py": ["mod-auth-session"]
  }
}
```

The `tokens` field lets an agent or a helper script budget a read set before opening anything.

**Optional (d): path-scoped rules.** For Claude Code, the generator could emit `.claude/rules/` files with `paths:` frontmatter pointing at the matching module note, so the pointer loads only when the agent touches those files ([Claude Code memory docs](https://code.claude.com/docs/en/memory)). This is tool-specific and writes outside `docs/`, so it should be opt-in.

### Recommended traversal procedure

1. **Seed.** Map the task to notes: by file path through `path_index`, otherwise by scanning `index.md` summaries, otherwise by grep over the vault.
2. **Read seeds in full.** Usually one to three notes.
3. **Expand one hop, summaries only.** For each seed, read from `graph.json` the `summary` of every `depends_on` target (outbound), every `used_by` source (inbound, needed when changing a public surface), every `reads`/`writes` data model, and every note that is `about` the seed. This keeps "every dependency visible" at the price of one sentence each.
4. **Open neighbours selectively.** Open a neighbour's full note only if its summary bears on the task. Always open `decision` notes `about` a seed.
5. **Go up for context.** Follow `part_of` to the parent only if the seed's purpose is unclear.
6. **Go to a second hop** only along `depends_on`, and only when changing an interface or data model that others consume.
7. **Check trust.** For each note used, check `status`. If cheap, compare `source_hash` with the working tree.
8. **Then read the code** that the notes cite. Notes locate and explain; the code decides.

A small helper script (`context <path-or-id> [--hops N] [--budget TOKENS]`) that prints the seed notes and the neighbour summaries would make steps 1 to 4 one tool call. That is my suggestion, in line with the Vercel result that agents skip optional retrieval steps unless they are cheap and obvious.

---

## 7. Scaling

### Evidence

- Index-first navigation "works surprisingly well at moderate scale (~100 sources, ~hundreds of pages)"; a search tool becomes worthwhile beyond that ([Karpathy gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)).
- CodeWiki was evaluated on repositories from 86K to 1.4M lines. It decomposes recursively with a 32,768-token leaf threshold and a maximum depth of 3, and scored worse on C and C++ (53.24%) than on scripting languages (79.14%) ([arXiv 2510.24428](https://arxiv.org/html/2510.24428v5)).
- DeepWiki caps a wiki at 30 pages, 80 for enterprise ([docs.devin.ai](https://docs.devin.ai/work-with-devin/deepwiki)).
- Meta: 59 notes for 4,100+ files, about 70 files per note, taking less than 0.1% of a context window in total ([Meta](https://engineering.fb.com/2026/04/06/developer-tools/how-meta-used-ai-to-map-tribal-knowledge-in-large-scale-data-pipelines/)).
- Graphify reports token reduction that "scales with corpus size": 71.5x on 52 files, 5.4x on 4 files, about 1x on 6 files; small corpora fit in a context window anyway ([README](https://raw.githubusercontent.com/Graphify-Labs/graphify/main/README.md)). These are the vendor's own figures.
- Aider's ranked repo map defaults to a 1k-token budget for the whole repository ([aider.chat](https://aider.chat/docs/repomap.html)).

### Opinion: behaviour by size

The figures below are my rough estimates, not measurements.

| | ~50 files | ~2,000 files | ~50,000-file monorepo |
|---|---|---|---|
| Module notes | 5-10, one per directory | 50-150, two levels | 1,000-2,500 if complete; realistically generated per area on demand |
| Other notes | 5-15 | 50-150 | hundreds |
| Index | One file; `overview` can be merged into it | One root index | Root index of areas plus one index per area |
| Symbol notes | None | Opt-in for hot spots | None by default |
| `graph.json` | One small file | One file | Sharded per area, with a root file holding area-level nodes and cross-area edges |
| Main value | Rationale, flows, decisions. The agent can read all the code anyway | Navigation plus rationale | Navigation and cross-package dependencies. Completeness is not affordable |
| Generation strategy | Full run | Full run, bottom-up | Breadth-first to package level, then deepen where there is churn, centrality, or an explicit request |

**When to stop at module level.** Stop subdividing when a unit's sources fit comfortably in one read. A workable rule is at most about 30k tokens of source or about 40 files per leaf module, in line with CodeWiki's 32,768-token leaf threshold. Go below module level (`level: file` or `symbol`) only when a file is both large and central (high in-degree in the extracted graph) or the user asks. Go no deeper than three or four `part_of` levels.

**Token cost.** Initial generation has to read the source at least once, so input cost is roughly the size of the codebase in tokens times a small factor for re-reads and parent synthesis. At an assumed average of 1,500 tokens per file, 50 files is about 75k tokens, a single session, and 50,000 files is about 75M input tokens before overhead. That is why a monorepo needs lazy, prioritized generation and why file-level notes are not viable there. Update cost is proportional to the number of notes whose sources changed at surface level, plus one hop, provided Phase A filters out no-op changes. Read cost for an agent is the pointer (about 150 tokens, always), the index (1-3k tokens, on demand), seed notes (about 0.5-1k tokens each), and one sentence per neighbour.

**Monorepo specifics.**
- Treat each workspace package as a C4 container with its own sub-vault folder and index. Cross-package `depends_on` edges come from manifest files and are cheap and objective.
- Allow partial coverage and make it visible: the index lists areas with no notes, so an agent knows that absence of a note is not absence of code.
- Rank what to document first by graph centrality (as aider ranks its repo map) and by recent churn.
- CODEOWNERS-style path globs can route `needs-review` notes to owners.

**Small-repo specifics.** Below roughly 30 files the whole scheme may cost more than it returns for agents. Gloaguen et al. suggest generated docs duplicate what the agent reads anyway ([arXiv 2602.11988](https://arxiv.org/html/2602.11988)). A "minimal" profile would be sensible: `index` and `overview` merged, one `module` note per top-level directory, `decision` and `flow` notes only.

---

## Open questions / decisions for the project owner

1. **Primary audience when the two conflict.** Humans want readable narrative; the evidence says agents gain little from narrative that restates code. Should prose be kept minimal for everyone, or should there be a "human-rich" profile?
2. **Default depth.** Is module level (no file or symbol notes) acceptable as the default, with `symbol` notes opt-in?
3. **Link-set size.** Accept the eight typed links plus untyped `mentions`? In particular: merge `reads` and `writes` into one link, or keep both? Keep `about` as one link for flows, concepts, decisions and guides, or split it into `involves`, `affects` and `documents`?
4. **Extracted versus inferred dependencies.** One `depends_on` key with provenance only in `graph.json` and the body table (my recommendation), or two frontmatter keys so the distinction is visible in the note itself?
5. **Extractor technology.** Tree-sitter, SCIP indexers, language servers, or LLM-only extraction as a fallback? This decides how many link types are really "objective" per language, and what the skill has to install.
6. **Where hashes live.** `source_hash` in each note's frontmatter (my recommendation) or one lock file as Codocia does?
7. **Is `graph.json` committed or git-ignored?** Committed means agents can use it without running anything, but it adds diff noise and merge conflicts. Ignored means it must be rebuilt on checkout.
8. **Who runs Phase B and when?** Only on demand through the skill, in a PR bot, or on a schedule? Is an LLM call in CI acceptable to target users?
9. **CI strictness.** Should a stale note fail the build, warn, or be configurable with warn as the default?
10. **Human-edit policy inside generated regions.** When a human edits a generated region: keep the human text and stop generating that region, or write a proposal next to it?
11. **Who owns `sources` globs?** Generator-assigned and rewritten on every run, or editable by humans, in which case the generator must respect manual changes?
12. **Decision notes.** May the tool draft ADRs from commit and PR history (marked `proposed`), or must it only import existing ADRs? Invented rationale is the highest hallucination risk in the whole scheme.
13. **Guides.** Generate how-to notes at all, or leave them wholly to humans apart from verified build and test commands?
14. **File naming.** Type-prefixed unique basenames (`mod-auth-session.md`) so wikilinks resolve without paths, or folder paths with friendlier names plus `aliases`?
15. **Vault location and neighbours.** Does the vault own all of `docs/`, or a subfolder such as `docs/vault/`, so that existing hand-written docs and this `docs/research/` folder are left alone? Should existing docs be linked in as `human` notes?
16. **Obsidian plugin dependence.** Core features only (properties, backlinks, Bases), or assume Dataview and Breadcrumbs for typed-edge views? Needs a quick test of whether the core graph view draws links that exist only in properties, and of how HTML comment markers display.
17. **Minimum Obsidian version.** Rename-safe links in properties are documented for desktop 1.11.4. Is requiring that version acceptable?
18. **Writing outside `docs/`.** May the skill add the pointer to `AGENTS.md`/`CLAUDE.md`, and optionally emit `.claude/rules/` path-scoped pointers, or must it only print the snippet for the user to paste?
19. **Monorepo policy.** Is partial, lazily generated coverage acceptable, and what is the ranking signal (centrality, churn, user selection)?
20. **Small-repo policy.** Offer a "minimal" profile, or tell users below a size threshold that the vault mainly serves humans?
21. **Evaluation.** Will the project ship an eval (tasks run with and without the vault, measuring success, tool calls and tokens) and publish results before making agent-benefit claims? Without it, the claim rests on indirect evidence.
22. **Privacy of generated content.** Notes copy signatures, config key names and paths into `docs/`. Is a redaction or exclusion list (for example secrets directories, vendored code) part of the first version?
23. **Log file.** Keep an append-only `log.md` of generator runs in the repo, or rely on git history?
