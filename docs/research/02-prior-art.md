# 02 — Prior art and competitors

Research date: 2026-11-14/15. All facts below were fetched from the web on those dates; nothing is taken from memory. Star counts and "last push" dates come from the public GitHub REST API (`api.github.com/repos/<owner>/<repo>`) where marked **[API]**, otherwise from the rendered repository page (**[page]**). GitHub timestamps are UTC.

Verification labels used in this report:

- no label: read directly on the project's own repo, docs, or paper.
- **(secondary)**: taken from a third-party article or a search-result summary, not confirmed on the primary source.
- **(vendor claim)**: stated by the project about itself, with no independent measurement found.
- **(unverified)**: could not be confirmed at all.

## 1. Summary

1. No project found is an exact duplicate of "a Claude skill that writes an in-repo `docs/` folder that is also an Obsidian vault, one note per code unit, YAML frontmatter, typed links, incrementally maintained".
2. The idea is surrounded on four sides by active, well-funded or highly starred projects, each of which has one or two of the properties but not all:
   - **In-repo linked Markdown wiki, agent-written, incrementally updated, with per-claim evidence:** LangChain OpenWiki (18k stars, MIT).
   - **Static-analysis code graph exported to an Obsidian vault with relation-tagged wikilinks:** Graphify (148k stars), code-review-graph (33k stars).
   - **Claude skill that writes an Obsidian vault from source code:** blur3hq/codebase-vault-docs (1 star), bevibing/tutor-skills (1.4k stars).
   - **Claude skill that writes an in-repo Markdown wiki with citations and incremental sync:** natsu1211/deepwiki-skill (46 stars), FSoft-AI4Code/CodeWiki (1.9k stars, ACL 2026 Findings).
3. The open gap is the combination: explanatory notes at a unit granularity chosen for humans, with machine-readable typed dependency links in frontmatter, deterministic structure plus LLM prose, per-note staleness tracking, and plain files that work in Obsidian with no server, database or MCP process.
4. The field shows consistent failure modes that the design must address: confident wrong prose, no way for a reader to tell what is stale, one-note-per-symbol noise, agents that never open the generated artefact, and generated context that raises agent cost without raising success.

## 2. Inventory

### 2.1 LLM-generated codebase wikis

#### DeepWiki (Cognition) — hosted, proprietary

- URL: <https://deepwiki.com>, docs <https://docs.devin.ai/work-with-devin/deepwiki>
- Licence: proprietary hosted service. Public repos free; private repos need a Devin account (secondary: <https://repowise.dev/blog/comparisons/openwiki-alternatives>).
- Output: hosted wiki pages with architecture diagrams, source links and summaries, plus an "Ask Devin" chat (<https://docs.devin.ai/work-with-devin/deepwiki>). MCP server for public repos with `read_wiki_structure`, `read_wiki_contents`, `ask_question` (secondary, same repowise article).
- Structure extraction: not published in detail. Docs describe default "cluster-based planning" that a `.devin/wiki.json` file replaces (<https://docs.devin.ai/work-with-devin/deepwiki>).
- Steering: `.devin/wiki.json` with `repo_notes` and `pages` (`title`, `purpose`, `parent`, `page_notes`). Limits: 30 pages (80 on enterprise), 100 notes total, 10,000 characters per note (same docs page).
- Large repos: docs state that large repos hit built-in limits so folders can go undocumented; the remedy is to list a page per folder (same docs page).
- Updates: docs say to commit the config and regenerate; no automatic trigger is documented (same docs page). The OpenWrt forum states that a generated page "does not get regenerated if the repo is updated and it cannot be removed" (<https://forum.openwrt.org/t/important-consideration-deepwiki-ai-generated-docs-may-contain-inaccuracies/249471>). A third-party comparison says each wiki shows a "Last indexed" date (secondary, repowise article above).
- Cost: low effort free, medium about 5–10 ACUs, high about 20–40 ACUs per wiki (<https://docs.devin.ai/work-with-devin/deepwiki>).
- Complaints (HN thread, <https://hn.svelte.dev/item/45002092>):
  - Maintainers of LLVM-adjacent projects, LibreOffice, PureLB and niche libraries reported wrong content: an incorrect pipeline diagram that omitted major subsystems, a build-system page naming a build tool the project never used, and an AI-generated bug report built on DeepWiki content that cost a maintainer about an hour.
  - "It goes into way too much depth on some trivial details, and glosses over more important stuff."
  - Fixates on very large files and misses subsystems spread across many files.
  - Diagrams "too handwavy to be useful".
  - Pages are created without maintainer consent and there is no clear takedown path.
- OpenWrt maintainers report users acting on wrong configuration and dependency information (<https://forum.openwrt.org/t/important-consideration-deepwiki-ai-generated-docs-may-contain-inaccuracies/249471>).

#### deepwiki-open (AsyncFuncAI)

- URL: <https://github.com/AsyncFuncAI/deepwiki-open>
- Licence MIT, 18,424 stars, last push 2026-11-15, created 2025-04-30 **[API]**.
- Output: self-hosted web app (Next.js) that renders a generated wiki with diagrams and a chat; README lists "Generate codemap for code-centric guided tours" (<https://github.com/AsyncFuncAI/deepwiki-open>).
- Structure extraction: README describes the steps only at a high level ("Analyze the code structure", "Generate comprehensive documentation", "Create visual diagrams"). The Helm section persists `~/.adalflow`, which implies the AdalFlow framework for local state. RAG/embedding internals were **not verified** from the README.
- Updates: no scheduled refresh found in its docs; regenerate manually (secondary: <https://repowise.dev/blog/comparisons/openwiki-alternatives>).
- Note: README announces "Deepwiki-Open 2.0 (Grok Wiki is now live)" pointing to a separate product (<https://github.com/AsyncFuncAI/deepwiki-open>).
- Output is not written into the documented repo as files. Not Obsidian-related.

#### Google Code Wiki — hosted, proprietary

- URL: <https://codewiki.google>, announcement <https://developers.googleblog.com/en/introducing-code-wiki-accelerating-your-code-understanding/> (2025-11-13).
- Output: hosted wiki per public repo, with architecture, class and sequence diagrams and a Gemini chat. "Every wiki section and chat answer is hyper-linked directly to the relevant code files and definitions." (announcement).
- Updates: "scans the full codebase and regenerates the documentation after each change" (announcement). One third-party measurement on 2026-10-12 found it 0–1 commits behind HEAD on three repos (secondary: <https://repowise.dev/blog/comparisons/openwiki-alternatives>).
- Private repos: a Gemini CLI extension was announced as "coming soon" with a waitlist (announcement); still described as waitlisted in October 2026 (secondary, repowise article).
- Lineage: The Register reports an HN comment from Mutable.ai's founder saying Code Wiki rebuilds Auto Wiki (<https://www.theregister.com/2025/11/17/google_previews_code_wiki/>).
- Complaints (The Register, same URL): a factually "half right" answer about PostgreSQL support; Vue output described as "an 'educated guess' kind of documentation" with "LLM-isms", alternately too vague and too specific, and verbose; the end-of-life status of `vuejs/vue` was not flagged; a commenter objected that docs which change wholesale overnight waste readers' time; it is not a wiki in the collaborative sense.
- Broader critique: "Code wikis are documentation theater as a service" — output is "byproducts of an LLM digestion process", diagrams exist because "docs must have diagrams", and nobody who understands the system takes responsibility for the text (<https://passo.uno/ai-wikis-docs-teather-as-a-service/>).

#### Mutable.ai Auto Wiki — discontinued

- YC listing: status "Acquired"; Auto Wiki "turns code into wikipedia style articles with citations to the code" (<https://www.ycombinator.com/companies/mutableai>).
- Alphabet reported the acquisition to EU regulators (<https://www.mlex.com/mlex/artificial-intelligence/articles/2309742/alphabet-reports-takeover-of-mutableai-to-eu-regulators>).
- Acquisition date (November vs December 2024) and "discontinued" status are **secondary and inconsistent** between sources.

#### CodeWiki (FSoft-AI4Code) — research framework

- URL: <https://github.com/FSoft-AI4Code/CodeWiki>, paper <https://arxiv.org/abs/2510.24428>
- Licence MIT, 1,864 stars, last push 2026-11-14 **[API]**. README labels it Findings of ACL 2026; version badge 2.0.0.
- Output: Markdown. `overview.md` entry point, one page per module, sub-module pages in folders that mirror the module tree, `module_tree.json`, `metadata.json`, optional `index.html` viewer, optional Backstage TechDocs export. A `--flat` option exists because relative links are hard for smaller models (README).
- Structure extraction: builds a dependency graph from the code (README: "written by AI agents from the dependency graph"), 11 languages. 2.0 notes say call resolution for C, C++, Java, C# is scope-, namespace-, include- and import-aware and library calls are filtered by an external symbol table. The parser library is not named on the README; **tree-sitter use is unverified**.
- Large repos: graph is clustered recursively into a module tree; "One agent per leaf module reads the code through tools and writes the page"; parent pages are written from child pages; diagrams are validated before saving (README).
- Updates: `codewiki generate --update` "diffs the saved graph against the current code, repairs the module tree" and patches only affected pages, falling back to a full build if too much changed. README reports one update at $0.34 against $21.48 for a full build on svelte **(vendor claim)**.
- Agent integration: `skills/codewiki-wiki-generator` folder in the repo; subscription mode through the `claude` and `codex` CLIs; `codewiki mcp` lets the IDE's model do the writing (README).
- Benchmark **(vendor claim, own benchmark CodeWikiBench)**: DeepWiki 65.06, CodeWiki 1.0 69.79, CodeWiki 2.0 82.23 average rubric score (README).
- Not Obsidian-specific: standard relative Markdown links, no frontmatter described, no typed links.

#### RepoAgent (OpenBMB) — inactive

- URL: <https://github.com/OpenBMB/RepoAgent>, paper <https://arxiv.org/abs/2402.16667>
- Licence Apache-2.0, 1,061 stars, last push 2024-12-23 **[API]**.
- Output: Markdown per code object, written into a folder in the target repo (CLI default `markdown_docs`), plus a JSON hierarchy record (`.project_doc_record`) (<https://raw.githubusercontent.com/OpenBMB/RepoAgent/main/README.md>).
- Structure extraction: Python AST; "Accurate identification of inter-object bidirectional invocation relationships" (README).
- Updates: "Automatically detects changes in Git repositories"; a pre-commit hook regenerates docs for changed files and modifies the staged set; `repoagent diff` previews what would change (README).
- Large repos: multi-threaded generation; XAgent (about 270k lines) documented with gpt-3.5-turbo (README).
- Limits: Python only; multi-language listed as future work and never shipped (README, last push date).

#### Autodoc (context-labs) — inactive

- URL: <https://github.com/context-labs/autodoc>
- Licence MIT, 2,374 stars, last push 2024-08-12 **[API]**.
- Depth-first traversal of the repo, docs stored in a `.autodoc` folder and queried by CLI; incremental/CI update was a stated future plan, not a feature **(secondary: search summary of the README and listings such as <https://awesome.ecosyste.ms/projects/github.com%2Fcontext-labs%2Fautodoc>)**.

#### OpenDeepWiki (AIDotNet, formerly KoalaWiki)

- URL: <https://github.com/AIDotNet/OpenDeepWiki>
- Licence MIT, 3,663 stars, last push 2026-10-23 **[API]**.
- A server product: ASP.NET Core, Next.js, SQLite/PostgreSQL, background workers for scheduled incremental updates, one MCP endpoint per repo at `/api/mcp/{owner}/{repo}` (secondary: <https://repowise.dev/blog/comparisons/openwiki-alternatives>; README mirror <https://openaitx.github.io/projects/AIDotNet/OpenDeepWiki/README-en.html>).
- Output lives in a database behind a web UI, not as files in the repo.

#### OpenWiki (LangChain) — closest general competitor

- URL: <https://github.com/langchain-ai/openwiki>, docs <https://docs.langchain.com/oss/openwiki/overview>
- Licence MIT, 18.0k stars **[page]**. First published June 2026, release 0.7.2 on 2026-10-09 (secondary: <https://repowise.dev/blog/comparisons/openwiki-alternatives>).
- Output: linked Markdown in an `openwiki/` folder at the repo root, with `openwiki/quickstart.md`, `openwiki/.claims/`, `openwiki/INSTRUCTIONS.md`, `openwiki/.run.json`, `openwiki/.page-manifest.json`, `openwiki/.last-update.json` (README).
- Format: Google's Open Knowledge Format (OKF) v0.2. "Every concept document carries YAML front matter with a non-empty `type`"; optional `title`, `description`, `resource`, `tags`, `timestamp`; provenance fields `sources`, `verified`, `status`, `stale_after`; `generated: {by, at}` on new pages; reserved `index.md` and `log.md` (README; <https://www.langchain.com/blog/openwiki-0-2-adds-okf-support>).
- Links: standard Markdown links between pages. No `[[wikilinks]]` and no typed relations are described (README; OKF blog post).
- Evidence model: each fact is a "Grounded Claim" tied to versioned evidence such as `repo://src/server.ts#L40-L82`; "Versioned claim sidecars under `openwiki/.claims/` travel with the Markdown"; the Markdown itself stays clean (README).
- Updates: `openwiki --update` checks repo changes since the last successful run plus the evidence versions behind stored claims. "Clean updates skip model work and leave the wiki content untouched." Stale claims force work on their owning page (README).
- Large repos: "an ordered queue of independently durable page jobs"; each page is a resume unit; page concurrency 1–8 (default 1); concurrency drops by one on a rate limit (README).
- Agent integration: maintains a managed block in `AGENTS.md` (and `CLAUDE.md` if it exists) between `<!-- OPENWIKI:START -->` and `<!-- OPENWIKI:END -->`; read-only `openwiki_search` and `openwiki_read` tools; host-driven generation protocol `openwiki_begin → openwiki_submit_plan → openwiki_next_page → openwiki_submit_page → … → openwiki_finish` (README).
- Runs inside Claude Code, Codex, Cursor and others, or standalone on Deep Agents (secondary, repowise article).
- Stated weaknesses (secondary, repowise article, a competitor): first run on a large repo is a full agent run billed to the user; no hosted reader; "prose reflects what the agent chose to write"; needs Node.js 22.22+.
- Obsidian: not mentioned anywhere on the README. Its own viewer is `openwiki visualize`.

#### repowise

- URL: <https://github.com/repowise-dev/repowise>
- Licence AGPL-3.0, 8.1k stars **[page]**.
- Output: "a wiki for every module and file" that "updates incrementally after each commit", architecture map, C4 views, generated `CLAUDE.md`/`AGENTS.md`, ten default MCP tools (README). Pages per file, public symbol, subsystem, dependency cycle; `repowise export --format markdown` (secondary and vendor-authored: <https://repowise.dev/blog/comparisons/openwiki-alternatives>).
- Structure extraction: parsed graph over 28 languages; also mines git history, ADRs, `# WHY:` comments, PRs and agent transcripts. "Graph, risk, health, tests and dead code make zero LLM calls." Prose is optional (README).
- Updates: `repowise update`, `repowise watch`, post-commit hook; every MCP response carries the indexed commit, index age and a stale warning (README).
- Vendor test: seven repos, 260 pages in 1m 58s with no API key **(vendor claim, same blog)**.

#### Qoder Repo Wiki (Alibaba) — proprietary IDE feature

- Docs: <https://docs.qoder.com/user-guide/repo-wiki>
- Output: Markdown under `<project_root>/.qoder/repowiki/<lang>/content/` with `meta/repowiki-metadata.json`; a `wiki_plan.yaml` steers generation; the folder is committed and shared through Git.
- Updates: detects drift such as changed function signatures; "Update" regenerates only affected parts; incremental update requires a Git repo with at least one commit.
- Manual edits: human edits are marked protected and are not overwritten by later automatic updates.
- Limits: 10,000 files per project; generation consumes credits.

#### PocketFlow Tutorial-Codebase-Knowledge

- URL: <https://github.com/The-Pocket/PocketFlow-Tutorial-Codebase-Knowledge>
- Licence MIT, 12,760 stars, last push 2026-05-31 **[API]**.
- Pure LLM pipeline that identifies "core abstractions and how they interact" and writes a beginner tutorial as Markdown chapters. Caps: 100 KB per file, `--max-abstractions` default 10. No incremental update; only LLM response caching (README).

### 2.2 Code-to-knowledge-graph tools for agents

#### Graphify (Graphify-Labs, formerly safishamsi/graphify)

- URL: <https://github.com/Graphify-Labs/graphify> (the old `safishamsi/graphify` URL redirects), site <https://graphify.com>
- Licence: repo carries both `LICENSE` (Apache-2.0) and `LICENSE-MIT`; 148k stars **[page]**. A hosted "Graphify Cloud" now exists (README banner).
- Form: a Claude Code skill (`/graphify`) plus a Python CLI; also installs for Codex, OpenClaw, Aider and others (README).
- Output: `graphify-out/graph.json`, `graph.html`, `GRAPH_REPORT.md` (god nodes, communities, key paths); `/graphify . --wiki` "build a markdown wiki from the graph" (README).
- **Obsidian export**: `graphify export obsidian --dir <vault>` "writes one note per node, plus a community overview" and a `graph.canvas` that "keeps the 200 highest weight edges so a large graph stays openable"; "Each connection is a wikilink with the relation and an EXTRACTED, INFERRED or AMBIGUOUS tag." The docs example on httpx wrote 2,530 notes (<https://graphify.com/vs/obsidian>).
- Structure extraction: "Code is parsed with tree-sitter AST: deterministic, no LLM, nothing leaves your machine." About 40 languages. Docs, PDFs and images go through an LLM pass. Leiden clustering for communities (README).
- Edge model: relations `calls`, `imports`, `inherits`, `mixes_in` and others; each edge tagged `EXTRACTED` or `INFERRED`; a path's confidence equals its weakest hop (README).
- Updates: `--update` re-extracts only changed files; `graphify hook install` rebuilds on commit and checkout; `graphify watch` (README).
- Large repos: HTML view aggregates above 5,000 nodes; community labelling batched 100 per call (README).
- Agent integration: `graphify claude install` writes a CLAUDE.md section and a PreToolUse hook that fires before Glob/Grep (secondary: PyPI listing summary, <https://pypi.org/project/graphifyy/>).
- Complaints:
  - A 60-session, two-project audit of Claude Code transcripts found about 1,500 hook reminders and **zero** graph invocations; `GRAPH_REPORT.md` was read once. The author concludes that agents treat CLAUDE.md rules and reminder hooks as advisory and that grep wins because it is one step (<https://rentierdigital.xyz/blog/claude-code-knowledge-graph-audit-failed>).
  - Obsidian export bugs: node labels starting with `.` produced notes Obsidian never displays (<https://github.com/Graphify-Labs/graphify/pull/2242>); community labels with `.`, `&`, `(`, `)` produced invalid tags that broke Dataview (<https://newreleases.io/project/github/safishamsi/graphify/release/v0.7.1>).
  - "Cut agent token spend by 80%" is promotional text with no methodology on the README **(vendor claim)**.
- A separate Rust crate `graphify-export` writes one note per node with frontmatter `id`, `type`, `source`, `community`, `community_label` and a `## Connections` list of `- [[neighbour]] (relation)` (<https://docs.rs/crate/graphify-export/0.7.0/source/src/obsidian.rs>). Whether this crate belongs to the same project is **unverified**.

#### Understand-Anything (Egonex-AI, formerly Lum1104)

- URL: <https://github.com/Egonex-AI/Understand-Anything> (old `Lum1104/Understand-Anything` redirects)
- Licence MIT, 92.7k stars **[page]**.
- Form: Claude Code plugin with `/understand`, `/understand-explain`, `/understand-onboard`, `/understand-domain`, `/understand-knowledge`, `/understand-diff`.
- Output: `.ua/knowledge-graph.json` plus an interactive dashboard; layers (API, Service, Data, UI, Utility), domains, flows, guided tours. No Markdown or Obsidian output described (README).
- Structure extraction: tree-sitter for imports, exports, definitions, call sites and inheritance ("Same input → same output, every run"); LLM agents (`project-scanner`, `file-analyzer`, `architecture-analyzer`, `tour-builder`, `graph-reviewer`, `domain-analyzer`, `article-analyzer`) add summaries, tags, layers and tours (README).
- Updates: incremental by default, fingerprint-based on the tree-sitter output; `/understand --auto-update` installs a post-commit hook (README).
- Large repos: "up to 5 concurrent workers and 20–30 files per batch"; subdirectory scoping (README).
- Stated limits: first run "can consume a significant number of tokens"; the LLM layer is not reproducible (README).

#### code-review-graph (tirth8205)

- URL: <https://github.com/tirth8205/code-review-graph>
- Licence MIT, 32,775 stars, last push 2026-11-12 **[API]**.
- Output: one SQLite file in `.code-review-graph/`, served over MCP. Wiki command produces a "Markdown wiki from communities". `visualize --format obsidian` exports an Obsidian vault (README). The export writes one page per node with YAML frontmatter, community pages, a global index, and `[[wikilinks]]` between related entities; field names and edge typing are not documented **(secondary: <https://instagit.com/tirth8205/code-review-graph/how-does-export-functionality-work.md>)**.
- Structure extraction: tree-sitter with fallbacks. Edges carry one of four tiers "EXTRACTED, INFERRED, AMBIGUOUS, UNRESOLVED" with float scores (README).
- Updates: hooks and watch mode; uses git diff, follows import and call edges to dependents, and "re-parses only the files whose SHA-256 hash changed". About 2.5 s for a two-file edit on a 3,000-file repo (README).
- Honest self-reporting worth noting (README): headline 63x median token reduction uses a whole-corpus baseline "an upper bound no real agent pays"; against a realistic agent baseline the median is 6.65x; an agent that then opens the named files "pays the graph on top of its usual reads rather than instead of them"; impact "recall 1.0" is circular; small single-file changes can cost more context than a plain read.

#### GitNexus

- URL: <https://github.com/abhigyanpatwari/GitNexus>
- Licence PolyForm Noncommercial 1.0.0 (commercial licences sold separately), 48,550 stars, last push 2026-11-15 **[API + page]**.
- Output: knowledge graph "of symbols, calls, dependencies and execution flows" in LadybugDB (formerly KuzuDB); MCP tools `query`, `context`, `impact`, `trace`, `detect_changes`, `rename`; `analyze` installs agent skills and writes AGENTS.md and CLAUDE.md (README).
- Wiki: built by clustering the graph into functional communities and having an LLM describe each module (<https://mintlify.com/abhigyanpatwari/GitNexus/cli/wiki>, secondary summary). Auto-updating wikis are an enterprise feature (README).
- Structure extraction: tree-sitter, 18 languages (README).
- Updates: `gitnexus analyze --watch`, `gitnexus status` for freshness, Claude Code hooks (README).
- The non-commercial licence rules it out as a dependency for a permissively licensed skill.

#### code-graph-rag (vitali87)

- URL: <https://github.com/vitali87/code-graph-rag>
- Licence MIT, 5,355 stars, last push 2026-11-14 **[API]**.
- Tree-sitter under "a single language-agnostic schema", with optional compiler-grade front ends (libclang, `go/types`, Roslyn, `javac`, Jedi). Default store is embedded SQLite; Memgraph and Neo4j are opt-in. Queries are natural language translated to Cypher. Runs as an agent or MCP server (README).
- No documentation output.

#### CodeGraphContext

- URL: <https://github.com/CodeGraphContext/CodeGraphContext>
- Licence MIT, 4,424 stars, last push 2026-11-05 **[API]**.
- Tree-sitter baseline over 23 languages with optional SCIP indexers (`SCIP_INDEXER=true`; scip-clang needs `compile_commands.json`, otherwise it "falls back to Tree-sitter"). Pluggable graph DB (FalkorDB Lite, KuzuDB, LadybugDB, Neo4j). `cgc watch` for live updates. MCP server (README).
- README states that tree-sitter call and inheritance data are heuristic.
- No documentation output.

#### Serena (oraios)

- URL: <https://github.com/oraios/serena>
- Licence: per component — SolidLSP MIT, the Serena application GPL-3.0-or-later; 31,388 stars, last push 2026-11-14 **[API + page]**.
- LSP-backed symbol tools for agents (find symbol, find referencing symbols, symbol-level edits) across 40+ languages, plus a memory system for long-lived workflows (README). Memory storage layout and staleness handling are **not described on the README (unverified)**.
- Not a documentation generator; relevant as the LSP alternative to tree-sitter for precise references.

#### Aider repository map

- Docs: <https://aider.chat/docs/repomap.html>; repo <https://github.com/Aider-AI/aider> (Apache-2.0, 50,119 stars, last push 2026-05-22 **[API]**).
- A "concise map of your whole git repository" listing files and key symbols with their critical lines. A graph ranking algorithm runs over a graph where "each source file is a node and edges connect files which have dependencies". Budget set by `--map-tokens`, "which defaults to 1k tokens", and expands when no files are in the chat (docs).
- Tree-sitter tag extraction and personalised PageRank with binary search to fit the budget are described by third-party analyses of the code **(secondary: <https://github.com/NousResearch/hermes-agent/issues/535>)**.
- Ephemeral, computed per request; nothing is written to the repo.

#### Repomix

- URL: <https://github.com/yamadashy/repomix>
- Licence MIT, 29,273 stars, last push 2026-11-15 **[API]**.
- Packs a repo into one file (XML default, Markdown, JSON, plain). `--compress` uses tree-sitter to keep "essential function and class signatures while removing implementation details" and is labelled experimental. Per-file token counts, `--token-budget`, `--split-output`. `--skill-generate` writes a Claude skill directory with `SKILL.md` and `references/{summary,project-structure,files,tech-stacks}.md` (README).
- No relationships, no links, no incremental update. Relevant only as a token-accounting reference and as an example of generating a skill folder from a repo.

#### Sourcegraph SCIP

- <https://sourcegraph.com/blog/announcing-scip>, <https://sourcegraph.com/docs/code-navigation/precise-code-navigation>
- A language-agnostic index format for precise, compiler-accurate definitions and references, including cross-repository. Indexers exist for Go, TypeScript/JavaScript, C/C++, Java/Kotlin/Scala, Python, Ruby, C#. Falls back to search-based navigation when no index exists for a file (docs).
- Needs a working build per language, which is the cost CodeGraphContext documents for its optional SCIP mode (<https://github.com/CodeGraphContext/CodeGraphContext>).

### 2.3 Tools that target Obsidian vaults from code

#### blur3hq/codebase-vault-docs — nearest in form

- URL: <https://github.com/blur3hq/codebase-vault-docs>
- Licence MIT, 1 star, created and last pushed 2026-09-19 **[API]**; 6 commits **[page]**.
- "An agent skill that turns source code into an Obsidian reference vault."
- Output: `index.md`, `progress.md` (module status across sessions), `conventions/style-guide.md`, and one folder per module with `00-overview.md`, mechanism notes (`01-…`, `02-…`), a decisions note and a `.canvas` file. "one Obsidian folder per module, where each file explains a mechanism instead of indexing it." Notes require prose, at least one Mermaid diagram, and decisions only when a recorded reason exists (README).
- Links: plain wikilinks; a Canvas per subsystem. No typed links and no frontmatter schema are documented on the README (the `SKILL.md` path could not be fetched, so the absence is **unverified**).
- Structure extraction: none. "The agent does the reading and writing with whatever tools it has." (README).
- Updates: no mechanism beyond `progress.md` and re-checking citations in touched files (README).
- Validation: three dependency-free Python scripts — `check_wikilinks.py`, `unwrap.py`, `validate_canvas.py` — with fixture vaults under `tests/` (README).

#### bevibing/tutor-skills (codebase mode)

- URL: <https://github.com/bevibing/tutor-skills>
- Licence MIT, 1,408 stars, last push 2026-02-28 **[API]**.
- `/tutor-setup` detects a project marker (`package.json`, `Cargo.toml`, `go.mod`, …) and produces a new-developer onboarding vault: `00-Dashboard/`, `01-Architecture/`, one folder per module, DevOps and Exercises folders. Per-module notes hold "key files, public interfaces, and dependency maps". Tag registry `#arch-*`, `#module-*`, `#pattern-*`. A cross-linking phase links modules and exercises (README).
- Pure LLM reading. No frontmatter schema, typed links or update path is described on the README. Purpose is study and onboarding, not maintained reference docs.

#### Graphify and code-review-graph Obsidian exports

- Covered in 2.2. Both export a static-analysis graph as one note per node. Graphify's wikilinks carry a relation name and a confidence tag in the note body (<https://graphify.com/vs/obsidian>).

#### itsnacho/obsidian-code-graph

- URL: <https://github.com/itsnacho/obsidian-code-graph>
- Licence MIT, 1 star, created 2026-11-07, last push 2026-11-08 **[API]**.
- Python-only. Uses the standard `ast` module; "Every module becomes a note" with docstrings and method outlines; imports become wikilinks; flags circular imports (DFS) and orphan files; ships Obsidian graph colour presets. Works as a plugin or CLI (README).

#### mrjw717/obsidian-code-graph (plugin, visualiser)

- URL: <https://github.com/mrjw717/obsidian-code-graph>
- Licence 0BSD, 10 stars, last push 2026-11-05 **[API]**.
- Does not generate notes. Parses code that already sits in a vault with tree-sitter (TS, TSX, JS, Python fully; imports-only for eight more) and draws typed edges: `imports`, `calls`, `contains`, `inherits`, `implements`, `uses-type` from parsing, plus a documentation protocol — `@tested-by`, `@adr [[ADR-note]]`, `@depends-on` comment tags in code, and `related-code: [[file]]` in note frontmatter that creates a `documents` edge (README).
- The only project found that defines a two-way code↔note link convention.

#### ATLAS-DEV78423/Graphify-Updated-Obsidian

- URL: <https://github.com/ATLAS-DEV78423/Graphify-Updated-Obsidian>
- Licence MIT, 2 stars, 2 commits, last push 2026-05-25 **[API + page]**.
- Claims AST extraction for Python/TS/JS, "wiki-linked markdown notes with YAML frontmatter", watch mode polling git HEAD every 5 seconds, post-commit hook. Frontmatter fields are not shown. Effectively abandoned.

#### obsidianmd/obsidian-skills (formerly kepano/obsidian-skills)

- URL: <https://github.com/obsidianmd/obsidian-skills> (old `kepano/obsidian-skills` redirects)
- Licence MIT, 52.7k stars **[page]**.
- Seven skills: `obsidian-markdown` (wikilinks, embeds, callouts, properties), `obsidian-bases` (`.base` files), `json-canvas`, `obsidian-cli`, `obsidian-headless`, `defuddle`, `knap` (README).
- Teaches agents the file formats. None reads source code or generates documentation. It is a dependency candidate, not a competitor.

#### Karpathy "LLM wiki" pattern and implementations

- Gist: <https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f> (created 2026-04-04).
- Three layers: immutable raw sources, an LLM-owned wiki ("The LLM owns this layer entirely."), and a schema file such as CLAUDE.md or AGENTS.md. Operations: ingest ("A single source might touch 10-15 wiki pages."), query, lint (contradictions, stale claims, orphans, missing cross-references). `index.md` is a catalogue with one line per page that the LLM reads first; `log.md` is append-only. "Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase." Suggests YAML frontmatter for Dataview and `qmd` for search when the index is no longer enough.
- Implementations seen (all for personal or document knowledge, not code):
  - `alirezarezvani/claude-skills` → `llm-wiki` skill with `/wiki-init`, `/wiki-ingest`, `/wiki-query`, `/wiki-lint` (repo MIT, 29,830 stars for the whole collection **[API]**; <https://dev.to/alireza_rezvani/llm-wiki-skill-build-a-second-brain-with-claude-code-and-obsidian-2ljg>).
  - `lewislulu/llm-wiki-skill` — no licence file detected, 657 stars, last push 2026-04-16 **[API]** (<https://github.com/lewislulu/llm-wiki-skill>).
  - `mehmetcakoglu/claude-obsidian-vault-skill` — builds a per-project wiki under `docs/vault/` from session transcripts, not from code; 1 star **[API]** (<https://github.com/mehmetcakoglu/claude-obsidian-vault-skill>).
  - `breferrari/obsidian-mind` — a vault template for agent memory with a `reference/` folder for codebase knowledge (secondary; <https://github.com/breferrari/obsidian-mind>).
- Criticism:
  - After several hundred pages: sections of the same file contradicted each other after a change (changelog appended, reference section left describing the dead system); duplicate entities under two names; orphans; context ceiling at roughly 100k tokens of wiki. Fixes built: a drift linter run pre-commit and on cron, one-fact-one-place entity cards, weekly lint, per-domain sub-schemas, and a vector index used only to find the right page (<https://mpt.solutions/karpathys-llm-wiki-works-heres-what-broke-when-i-ran-it-at-real-scale/>).
  - Once the wiki outgrows context the LLM re-reads the wiki rather than the sources and accumulates second-order errors (HN, <https://hn.svelte.dev/item/47640875>, secondary summary).
  - No provenance or freshness policy (<https://aksel.mataroa.blog/blog/karpathys-llm-wiki-full-analysis-with-comments/>, secondary summary).

### 2.4 Claude skills and plugins for documentation generation

| Skill | URL | Licence / stars | What it writes | Notes |
|---|---|---|---|---|
| natsu1211/deepwiki-skill | <https://github.com/natsu1211/deepwiki-skill> | MIT, 46 stars [page], v1.0.4 | `docs/wiki/` with `toc.yaml`, numbered pages, `_context/context_pack.json`, `_reports/` | Six phases: scan → TOC design → writing → validation → summary → incremental sync. "Every statement traced back to source files with line numbers". Mermaid validated with the Mermaid CLI. Subagents "for faster documentation generation and better context isolation". Change-detection method not documented. |
| FSoft-AI4Code/CodeWiki skill | <https://github.com/FSoft-AI4Code/CodeWiki> | MIT, 1.9k | Module-tree Markdown | `skills/codewiki-wiki-generator` plus `codewiki mcp`; see 2.1. |
| ekuttan/codewiki | <https://github.com/ekuttan/codewiki> | MIT, 10 stars [page] | `codewiki/` with fixed topical files (`architecture.md`, `service-map.md`, `user-flows/`, `data-models.md`, …) and a merged `CLAUDE.md` | Single-file skill. Re-run offers "Fresh scan" or "Rescan & merge" that preserves manual edits. States that 500k+ line monoliths are a poor fit. |
| blur3hq/codebase-vault-docs | <https://github.com/blur3hq/codebase-vault-docs> | MIT, 1 star | Obsidian vault | See 2.3. |
| bevibing/tutor-skills | <https://github.com/bevibing/tutor-skills> | MIT, 1.4k | Obsidian onboarding vault | See 2.3. |
| Graphify | <https://github.com/Graphify-Labs/graphify> | Apache-2.0 + MIT, 148k | Graph + report + optional wiki/Obsidian export | See 2.2. |
| Understand-Anything | <https://github.com/Egonex-AI/Understand-Anything> | MIT, 92.7k | JSON graph + dashboard | See 2.2. |
| Repomix `--skill-generate` | <https://github.com/yamadashy/repomix> | MIT, 29k | A skill folder containing the packed repo | See 2.2. |
| obsidianmd/obsidian-skills | <https://github.com/obsidianmd/obsidian-skills> | MIT, 52.7k | Nothing from code | Format knowledge only. |
| mattpocock `obsidian-vault` | <https://skillselion.com/skills/mattpocock/skills/obsidian-vault> | unverified | Operates on an existing vault | (secondary) Not code-aware. |
| "code-wiki" listing | <https://vibehackers.io/claude-code/skills/code-wiki> | unverified | Wiki docs + Mermaid | (secondary) Listing warns a full wiki for a large monorepo is token-expensive. |

## 3. Synthesis

### (a) Comparison table

Legend — Extraction: **SA** static analysis (tree-sitter / AST / LSP / SCIP), **LLM** model reads the code, **SA+LLM** static structure with LLM prose. Stars are as observed 2026-11-14/15.

| Project | Licence | Stars / last push | Output and location | Page granularity | Links / relationships | Extraction | Update handling | Large-repo handling | Main complaints |
|---|---|---|---|---|---|---|---|---|---|
| DeepWiki | Proprietary | n/a (hosted) | Hosted web wiki + chat + MCP | Up to 30 pages per repo (80 enterprise) | Source links; hierarchy by `parent` | Undisclosed; cluster-based planning | Manual regenerate; no documented trigger | Hard page cap; folders silently dropped | Confident wrong facts, trivial detail over important, no opt-out, pages not regenerated |
| deepwiki-open | MIT | 18.4k / 2026-11-15 | Self-hosted web app | Generated page tree | In-app navigation | LLM (RAG internals unverified) | Manual regenerate (secondary) | Not documented on README | Successor product announced; not files in repo |
| Google Code Wiki | Proprietary | n/a (hosted) | Hosted web wiki + chat | Sections per repo | Hyperlinks to files and definitions | Undisclosed (Gemini) | Full regeneration after each change | Undisclosed | Half-right answers, verbose, EOL repo not flagged, text churns wholesale |
| CodeWiki (FSoft) | MIT | 1.9k / 2026-11-14 | Markdown in output folder + JSON tree | One page per module, mirrors module tree | Relative Markdown links | SA+LLM (dependency graph; parser unverified) | `--update` diffs saved graph, patches affected pages | Recursive clustering, one agent per leaf, parents from children | Benchmark is self-authored |
| RepoAgent | Apache-2.0 | 1.1k / 2024-12-23 | Markdown in repo + JSON record | One doc per code object | Caller/callee references | SA+LLM (Python AST) | Git change detection via pre-commit hook | Multithreading | Python only; inactive |
| Autodoc | MIT | 2.4k / 2024-08-12 | `.autodoc` folder | Per file/folder | None described | LLM | None (planned) | Depth-first traversal | Inactive (secondary) |
| OpenDeepWiki | MIT | 3.7k / 2026-10-23 | DB + web UI + MCP | Generated page tree | In-app | LLM | Scheduled incremental workers | Server-side | Needs DB, workers, hosting |
| OpenWiki (LangChain) | MIT | 18.0k / active | Markdown in `openwiki/` in repo | Concept pages from an agent plan | Standard Markdown links; OKF frontmatter with `type`; claims sidecars | LLM agent, claims tied to source line ranges | `--update` re-does only claims whose evidence changed; clean update makes no model calls | Durable page queue, resume per page, concurrency 1–8 | First run cost; prose is what the agent chose; no typed dependency links |
| repowise | AGPL-3.0 | 8.1k / active | Wiki + MCP; Markdown export | Per file, symbol, subsystem, cycle | Undocumented for pages | SA (28 languages), LLM prose optional | Post-commit incremental; freshness in every response | Zero-LLM render | AGPL; server-oriented; claims are vendor's own |
| Qoder Repo Wiki | Proprietary | n/a | Markdown in `.qoder/repowiki/` in repo | Planned pages (`wiki_plan.yaml`) | Markdown | Undisclosed | Drift detection, regenerate affected parts, protects manual edits | 10,000-file cap | IDE lock-in; credits |
| PocketFlow Tutorial | MIT | 12.8k / 2026-05-31 | Markdown chapters | Up to 10 abstractions by default | Chapter links | LLM | None | 100 KB file cap, abstraction cap | Tutorial, not reference |
| Graphify | Apache-2.0 + MIT | 148k / active | `graph.json`, HTML, report; optional wiki; Obsidian export | One note per node (2,530 for httpx); community overview | Wikilink + relation + EXTRACTED/INFERRED/AMBIGUOUS tag; Canvas capped at 200 edges | SA for code (tree-sitter), LLM for docs/media | `--update` on changed files; git hook; watch | Community aggregation above 5,000 nodes | Agents never invoke it (audit); export filename and tag bugs; marketing token claims |
| Understand-Anything | MIT | 92.7k / active | `.ua/knowledge-graph.json` + dashboard | File / function / class nodes | Graph edges in JSON | SA+LLM (tree-sitter + 7 agents) | Fingerprint-based incremental; post-commit hook | 5 workers, 20–30 files per batch | First-run token cost; LLM layer not reproducible; no Markdown |
| code-review-graph | MIT | 32.8k / 2026-11-12 | SQLite + MCP; wiki from communities; Obsidian export | One page per node in export | Wikilinks (typing undocumented); four confidence tiers in graph | SA (tree-sitter) | Git diff + SHA-256 per file; hooks; watch | Impact caps (500 nodes, depth 2) | Self-reported: weak search ranking, false positives, graph cost added on top of reads |
| GitNexus | PolyForm Noncommercial | 48.6k / 2026-11-15 | Graph DB + MCP; LLM wiki from clusters | Per community/module | Graph edges | SA (tree-sitter), LLM for wiki | Watch, status, hooks; auto-wiki is paid | Not documented | Non-commercial licence |
| code-graph-rag | MIT | 5.4k / 2026-11-14 | Graph (SQLite default) + agent/MCP | Symbols | Cypher-queryable edges | SA (tree-sitter + compiler front ends) | Incremental refresh | Not documented | No docs output |
| CodeGraphContext | MIT | 4.4k / 2026-11-05 | Graph DB + MCP | Symbols | Graph edges | SA (tree-sitter, optional SCIP) | `cgc watch` | 4 GiB buffer pool default | Tree-sitter calls are heuristic; no docs output |
| Serena | MIT (SolidLSP) + GPL-3.0 (app) | 31.4k / 2026-11-14 | Live LSP tools + memories | Symbols on demand | Live references | SA (LSP) | Always live | On-demand | Not a doc generator; GPL |
| Aider repo map | Apache-2.0 | 50.1k / 2026-05-22 | Ephemeral text map in prompt | File + key symbol lines | Ranked dependency graph | SA (tree-sitter, secondary) | Recomputed each request | 1k-token default budget | Nothing persisted |
| Repomix | MIT | 29.3k / 2026-11-15 | One packed file; optional skill folder | Whole repo | None | SA for `--compress` only | Full repack | Token counts, split output | No relationships |
| codebase-vault-docs | MIT | 1 / 2026-09-19 | Obsidian vault folder | One folder per module, one note per mechanism | Plain wikilinks + Canvas | LLM | None (progress file only) | Multi-session via `progress.md` | No structure extraction, no update path, negligible adoption |
| tutor-skills (codebase) | MIT | 1.4k / 2026-02-28 | Obsidian onboarding vault | Per-module note sets + exercises | Cross-links, tag registry | LLM | None described | Phased workflow | Study aid, not maintained docs |
| itsnacho/obsidian-code-graph | MIT | 1 / 2026-11-08 | Obsidian vault | One note per Python module | Wikilinks from imports | SA (Python `ast`) | Rescan | Not documented | Python only |
| mrjw717/obsidian-code-graph | 0BSD | 10 / 2026-11-05 | Graph view only (no notes) | n/a | 12 typed edges incl. `@depends-on`, `@adr`, `related-code` | SA (tree-sitter) | Not documented | Not documented | Does not generate docs |
| deepwiki-skill | MIT | 46 / unknown | Markdown in `docs/wiki/` | Pages from `toc.yaml` | Line-level source citations | LLM over a scanned context pack | "Incremental Sync" phase, `--update` | Subagents | Detection method undocumented |
| ekuttan/codewiki | MIT | 10 / unknown | `codewiki/` + `CLAUDE.md` | Fixed topical files + per-flow pages | None described | LLM | Fresh scan or rescan-and-merge | One repo at a time; scratch summaries | Hits context limits on large repos |
| Karpathy LLM wiki | n/a (gist) | unverified | Markdown vault | Entity/concept pages | Wikilinks, `index.md`, `log.md` | LLM over raw sources | Ingest + periodic lint | Index file, then search tool | Drift, contradictions, second-order errors |

### (b) Is there a direct duplicate?

**No exact duplicate was found.** Five projects overlap enough to matter. Ordered by how close they are:

1. **blur3hq/codebase-vault-docs** — same form (an agent skill), same target (an Obsidian vault from source code). It differs in that it has no static analysis, no documented frontmatter schema, no typed links, no update mechanism, and a module→mechanism layout rather than a per-unit graph. One star and six commits (<https://github.com/blur3hq/codebase-vault-docs>). It is a prompt-and-lint package, not a maintained documentation system.
2. **Graphify `export obsidian`** — the only widely used tool that writes relation-typed, confidence-tagged wikilinks into an Obsidian vault from code (<https://graphify.com/vs/obsidian>). It differs in that the vault is a dump of a symbol graph: one note per node (2,530 notes for httpx), no explanatory prose per unit, typing lives in body text rather than frontmatter properties, and the vault is an export target rather than the repo's `docs/` source of truth.
3. **LangChain OpenWiki** — the strongest competitor for the "agent-maintained Markdown in the repo, read by coding agents" goal, with the best evidence and update model seen (<https://github.com/langchain-ai/openwiki>). It differs in that it uses OKF with standard Markdown links, has no typed dependency relations between pages, lets the agent choose page boundaries rather than mapping to code units, needs a Node CLI, and does not target Obsidian.
4. **natsu1211/deepwiki-skill** and **FSoft-AI4Code/CodeWiki** — Claude-usable generators that write Markdown docs into the repo with incremental updates (<https://github.com/natsu1211/deepwiki-skill>, <https://github.com/FSoft-AI4Code/CodeWiki>). They produce a linear or tree-shaped wiki, not a typed graph, and are not Obsidian vaults.
5. **bevibing/tutor-skills codebase mode** — a Claude skill producing an Obsidian vault from code, but as onboarding study material with exercises and no maintenance path (<https://github.com/bevibing/tutor-skills>).

No project found combines all of: skill-only distribution, in-repo `docs/` that is a valid vault, one explanatory note per unit, YAML frontmatter with typed links, and incremental maintenance.

### (c) The gap this project can fill

1. **Typed relationships in frontmatter, as data.** Nobody stores dependency edges as queryable note properties. Graphify writes the relation as text after a wikilink in the body (<https://graphify.com/vs/obsidian>); OpenWiki and CodeWiki use untyped Markdown links (<https://github.com/langchain-ai/openwiki>, <https://github.com/FSoft-AI4Code/CodeWiki>); the graph tools keep typed edges in a database or JSON that humans do not read. A vault whose frontmatter is the graph serves Obsidian (Properties, Bases, Dataview), grep/`jq`-style tooling and agents from one artefact.
2. **Explanatory notes at a human-chosen unit size.** The field splits into "30 narrative pages for the whole repo" (DeepWiki cap, <https://docs.devin.ai/work-with-devin/deepwiki>) and "one note per symbol" (Graphify's 2,530 notes for httpx). A unit-level note (module, package, service, significant class) that both explains and links sits between them and is unoccupied.
3. **Complete dependency visibility with a small read set.** Agent-facing tools either hand over the whole map (Aider, Repomix) or require a tool call into a graph server (Graphify, GitNexus, code-review-graph). A note that lists every inbound and outbound dependency in its frontmatter lets an agent read one note plus its direct neighbours and still know the full edge set.
4. **No infrastructure.** Every graph tool needs a CLI, database, MCP server or hook process (see 2.2). OpenWiki needs Node 22.22+ (secondary, <https://repowise.dev/blog/comparisons/openwiki-alternatives>). A skill that emits plain files and a few dependency-free scripts has no runtime to keep alive.
5. **Obsidian as a first-class, validated target.** Existing Obsidian exports are afterthoughts with filename and tag bugs (<https://github.com/Graphify-Labs/graphify/pull/2242>, <https://newreleases.io/project/github/safishamsi/graphify/release/v0.7.1>). The only project that validates vault integrity is the one-star codebase-vault-docs (<https://github.com/blur3hq/codebase-vault-docs>).
6. **Per-note freshness the reader can see.** OpenWiki tracks claim evidence in sidecars; repowise reports index age over MCP; DeepWiki shows one date per wiki. None puts "this note describes commit X of files Y, hash Z" in the note a human or agent is reading.
7. **Docs that live with the code under review.** Hosted wikis (DeepWiki, Code Wiki) cannot be corrected by maintainers (<https://hn.svelte.dev/item/45002092>, <https://www.theregister.com/2025/11/17/google_previews_code_wiki/>). In-repo notes go through pull requests, which answers the accountability objection in <https://passo.uno/ai-wikis-docs-teather-as-a-service/>.
8. **Comparable graphs.** A vault whose structure is deterministic frontmatter can be diffed between commits or branches with ordinary tools. No surveyed tool advertises graph comparison over Markdown.

### (d) Design ideas worth stealing

| # | Idea | From | Why it matters here |
|---|---|---|---|
| 1 | Tag every edge with how it was obtained (`EXTRACTED` / `INFERRED` / `AMBIGUOUS` / `UNRESOLVED`); a path is only as trustworthy as its weakest hop | Graphify (<https://github.com/Graphify-Labs/graphify>), code-review-graph (<https://github.com/tirth8205/code-review-graph>) | Separates parsed facts from model guesses in typed links |
| 2 | Deterministic structure first, LLM only for prose ("Same input → same output, every run") | Understand-Anything (<https://github.com/Egonex-AI/Understand-Anything>), Graphify, repowise (<https://github.com/repowise-dev/repowise>) | Makes the graph reproducible and diffable; confines hallucination to prose |
| 3 | Claims tied to versioned source line ranges, kept in sidecars so the Markdown stays clean; update only pages whose evidence changed; a clean update makes zero model calls | OpenWiki (<https://github.com/langchain-ai/openwiki>) | Best incremental-update and provenance model found |
| 4 | Provenance fields in frontmatter: `sources`, `verified`, `status`, `stale_after`, `generated: {by, at}` | OKF v0.2 via OpenWiki (<https://www.langchain.com/blog/openwiki-0-2-adds-okf-support>) | A ready-made, emerging vocabulary; consider OKF-compatible field names |
| 5 | Required `description` in frontmatter so `index.md` can be generated deterministically | OpenWiki / OKF (same post) | Cheap, non-LLM index for agents and humans |
| 6 | `index.md` read first, append-only `log.md`, and a lint operation for contradictions, orphans, stale claims | Karpathy gist (<https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f>) | Standard navigation and maintenance loop for LLM-kept vaults |
| 7 | Git diff to find changed files, then follow import/call edges to dependents, then re-process only files whose SHA-256 changed | code-review-graph (<https://github.com/tirth8205/code-review-graph>) | Concrete, cheap staleness propagation along the dependency graph |
| 8 | Diff the saved graph against current code, patch only affected pages, fall back to full rebuild above a change threshold | CodeWiki (<https://github.com/FSoft-AI4Code/CodeWiki>) | Bounded incremental cost with an escape hatch |
| 9 | Bottom-up generation: one agent per leaf module, parent pages written from child pages, not from raw code | CodeWiki (same) | Fits Claude subagents; keeps each context small |
| 10 | Each page is an independently durable, resumable job; lower concurrency on rate limits | OpenWiki (<https://github.com/langchain-ai/openwiki>) | Long runs survive interruption |
| 11 | Host-driven protocol where a deterministic tool hands the agent one page at a time (`begin → submit_plan → next_page → submit_page → finish`) | OpenWiki (same) | The skill's scripts, not the model, control coverage and ordering |
| 12 | Human steering file with repo notes and an explicit page plan | DeepWiki `.devin/wiki.json` (<https://docs.devin.ai/work-with-devin/deepwiki>), Qoder `wiki_plan.yaml` (<https://docs.qoder.com/user-guide/repo-wiki>) | Lets maintainers fix granularity and emphasis once |
| 13 | Mark and protect manual edits so regeneration never overwrites them | Qoder Repo Wiki (<https://docs.qoder.com/user-guide/repo-wiki>), ekuttan/codewiki "Rescan & merge" (<https://github.com/ekuttan/codewiki>) | Required for docs humans will also edit |
| 14 | Managed block with start/end markers in `AGENTS.md` / `CLAUDE.md`; touch nothing outside it | OpenWiki (<https://github.com/langchain-ai/openwiki>) | Safe way to point agents at the vault |
| 15 | Dependency-free validator scripts with good and bad fixture vaults: wikilinks resolve, Canvas parses | codebase-vault-docs (<https://github.com/blur3hq/codebase-vault-docs>) | Deterministic gate after every generation |
| 16 | Validate Mermaid before saving | CodeWiki, deepwiki-skill (<https://github.com/natsu1211/deepwiki-skill>) | Broken diagrams are a common visible defect |
| 17 | Write **Decision:** entries only when a recorded reason exists | codebase-vault-docs (same) | Stops invented rationale |
| 18 | Two-way code↔note convention: `@depends-on` / `@adr [[note]]` tags in code comments, `related-code:` in note frontmatter | mrjw717/obsidian-code-graph (<https://github.com/mrjw717/obsidian-code-graph>) | Existing vocabulary for typed links that an Obsidian plugin already renders |
| 19 | Rank units by graph centrality and fit a token budget; surface "god nodes" | Aider repo map (<https://aider.chat/docs/repomap.html>), Graphify report | Tells an agent which notes to read first; tells humans where coupling concentrates |
| 20 | Cap the visual layer, keep the data complete (Canvas keeps top 200 edges, notes list every connection) | Graphify (<https://graphify.com/vs/obsidian>) | Keeps the graph view usable on large repos |
| 21 | Sanitise filenames and tags for Obsidian; dedupe collisions; never start a filename with `.` | Graphify fixes (<https://github.com/Graphify-Labs/graphify/pull/2242>, <https://newreleases.io/project/github/safishamsi/graphify/release/v0.7.1>) | Known breakage, already paid for by someone else |
| 22 | Report freshness with every read: indexed commit, age, stale warning | repowise (<https://github.com/repowise-dev/repowise>) | Reader always knows how far to trust a note |
| 23 | Publish benchmarks with the unflattering baseline next to the flattering one | code-review-graph (<https://github.com/tirth8205/code-review-graph>) | The honest framing was what earned trust for a comparable tool (secondary: <https://dev.to/andrew-ooo/codegraph-review-pre-indexed-knowledge-graph-for-ai-agents-af1>) |
| 24 | Optional precise references through SCIP or LSP, with tree-sitter fallback | CodeGraphContext (<https://github.com/CodeGraphContext/CodeGraphContext>), Serena (<https://github.com/oraios/serena>) | Upgrade path for edge accuracy without making a build mandatory |
| 25 | Reuse `obsidian-markdown`, `obsidian-bases`, `json-canvas` skills for format rules instead of restating them | obsidianmd/obsidian-skills (<https://github.com/obsidianmd/obsidian-skills>) | MIT, maintained by Obsidian; avoids format drift |
| 26 | Hierarchical rubric derived from a project's real docs as an evaluation method | CodeWikiBench (<https://github.com/FSoft-AI4Code/CodeWiki>) | A way to measure output quality rather than assert it |

### (e) Failure modes seen in the field that the design must address

1. **Confident, wrong prose.** Wrong build systems, wrong pipeline diagrams, wrong configuration semantics, presented as authoritative (<https://hn.svelte.dev/item/45002092>, <https://forum.openwrt.org/t/important-consideration-deepwiki-ai-generated-docs-may-contain-inaccuracies/249471>). Required response: structure from static analysis; every prose claim cites file and line; provenance label on every edge.
2. **Hallucinations harden and compound.** When the model re-reads its own wiki instead of the source, errors accumulate (<https://hn.svelte.dev/item/47640875>, secondary). Required response: regeneration always reads the source code, never only the previous note.
3. **Invisible staleness.** Pages that are never regenerated, or with one date for the whole wiki (OpenWrt forum above). Required response: per-note source hashes and commit, a deterministic staleness check, and a visible status field.
4. **Partial updates that leave a note contradicting itself.** A changelog entry is appended while the reference section still describes the old system (<https://mpt.solutions/karpathys-llm-wiki-works-heres-what-broke-when-i-ran-it-at-real-scale/>). Required response: regenerate whole sections or whole notes; lint for retired identifiers across the vault.
5. **Whole-document churn.** Full regeneration rewrites everything, so readers and reviewers cannot see what changed (<https://www.theregister.com/2025/11/17/google_previews_code_wiki/>). Required response: stable filenames and ordering, untouched notes stay byte-identical, small diffs.
6. **Wrong emphasis.** Trivial detail in depth, important subsystems glossed over; bias towards very large files; subsystems spread across many files missed (<https://hn.svelte.dev/item/45002092>). Required response: choose units from the dependency graph and centrality, not from file size; let maintainers steer.
7. **Silent coverage gaps on large repos.** Page caps drop folders without telling anyone (<https://docs.devin.ai/work-with-devin/deepwiki>); skills hit context limits before finishing (<https://github.com/ekuttan/codewiki>). Required response: a deterministic unit inventory, a coverage report, and resumable per-note jobs.
8. **Note explosion.** One note per symbol yields thousands of notes (2,530 for httpx, <https://graphify.com/vs/obsidian>); Obsidian's graph view degrades on very large vaults (<https://forum.obsidian.md/t/obsidian-graph-view-doesnt-work-for-a-large-vault/106287.md>). Required response: unit granularity above the symbol; symbols as headings inside notes.
9. **Agents do not use the artefact.** 1,500 reminders, zero graph calls in 60 sessions; text rules and reminder hooks are treated as advisory (<https://rentierdigital.xyz/blog/claude-code-knowledge-graph-audit-failed>). Required response: the vault must be reachable with tools agents already use (Read, Grep, paths that mirror the source tree) and must remove a step rather than add one.
10. **Generated context can cost more than it saves.** Repository context files did not generally improve task success and raised inference cost by over 20%; overviews did not help agents find files faster (<https://arxiv.org/abs/2602.11988>). A graph lookup on a narrow question can cost more than a direct read (<https://github.com/tirth8205/code-review-graph>; secondary: <https://dev.to/harrisonsec/i-tested-codegraph-on-hono-the-tool-call-savings-reproduce-the-cost-savings-dont-389p>). Required response: do not auto-load notes into context; keep notes short; measure agent outcomes with and without the vault before claiming a benefit.
11. **Unverifiable savings claims.** "80% fewer tokens" style numbers come from forced-use benchmarks or whole-corpus baselines (<https://github.com/Graphify-Labs/graphify>, <https://github.com/tirth8205/code-review-graph>). Required response: publish a realistic baseline or make no claim.
12. **First-run cost.** Full builds are a complete agent run: $21.48 for one CodeWiki build of svelte (<https://github.com/FSoft-AI4Code/CodeWiki>), 20–40 ACUs for a high-effort DeepWiki (<https://docs.devin.ai/work-with-devin/deepwiki>), "a significant number of tokens" for Understand-Anything (<https://github.com/Egonex-AI/Understand-Anything>). Required response: a cost estimate before the run, scoping to a subtree, and a structure-only mode with no LLM prose.
13. **Heuristic edges presented as facts.** Tree-sitter call and inheritance resolution is heuristic (<https://github.com/CodeGraphContext/CodeGraphContext>); impact analysis over-reports in large graphs (<https://github.com/tirth8205/code-review-graph>). Required response: confidence on every edge; unresolved references listed, not dropped or guessed.
14. **Language coverage collapses to one language.** RepoAgent stayed Python-only and went inactive (<https://github.com/OpenBMB/RepoAgent>); itsnacho's tool is Python-only (<https://github.com/itsnacho/obsidian-code-graph>). Required response: a language-agnostic fallback path from day one.
15. **Duplicate entities and name collisions.** The same thing documented under two names, both internally consistent (<https://mpt.solutions/karpathys-llm-wiki-works-heres-what-broke-when-i-ran-it-at-real-scale/>); filename collisions and invalid characters in exports (<https://docs.rs/crate/graphify-export/0.7.0/source/src/obsidian.rs>). Required response: stable unit IDs derived from source paths; one note per ID; `aliases` for alternate names.
16. **Vault-specific breakage.** Hidden dot-prefixed notes, invalid tags that break Dataview, unresolved wikilinks (<https://github.com/Graphify-Labs/graphify/pull/2242>, <https://newreleases.io/project/github/safishamsi/graphify/release/v0.7.1>). Required response: a vault validator as a mandatory final step.
17. **Overwriting human edits.** Regeneration destroys manual corrections unless they are protected (<https://docs.qoder.com/user-guide/repo-wiki>). Required response: marked human-owned regions that the generator never rewrites.
18. **"Documentation theatre".** Verbose LLM-style prose, diagrams added for appearance, no accountable author, and the label "docs" lowering expectations for real documentation (<https://passo.uno/ai-wikis-docs-teather-as-a-service/>, <https://www.theregister.com/2025/11/17/google_previews_code_wiki/>). Required response: label notes as generated reference material; keep prose terse and sourced; require human review through normal pull requests; include diagrams only where they carry structure.
19. **Missing project-level facts.** An end-of-life repository was documented as if current (<https://www.theregister.com/2025/11/17/google_previews_code_wiki/>). Required response: read README, changelog and deprecation notices; surface status in the index note.
20. **Licence traps in the neighbourhood.** GitNexus is PolyForm Noncommercial, repowise AGPL-3.0, Serena's application GPL-3.0 (<https://github.com/abhigyanpatwari/GitNexus>, <https://github.com/repowise-dev/repowise>, <https://github.com/oraios/serena>). Required response: depend only on permissively licensed components (tree-sitter grammars, obsidian-skills, Graphify's MIT/Apache code if reused).

## 4. Unverified or weakly sourced items

- **GitHub API coverage.** The unauthenticated API rate limit was reached part-way through. Stars for Graphify, Understand-Anything, obsidian-skills, OpenWiki, repowise, deepwiki-skill and ekuttan/codewiki are from the rendered page (rounded), and their exact last-commit dates were not obtained.
- **Repository renames.** `safishamsi/graphify` → `Graphify-Labs/graphify`, `Lum1104/Understand-Anything` → `Egonex-AI/Understand-Anything`, `kepano/obsidian-skills` → `obsidianmd/obsidian-skills` were observed as redirects on fetch; no rename announcement was read.
- **Graphify licence.** The repo shows both an Apache-2.0 `LICENSE` and a `LICENSE-MIT`; which applies to which part was not checked.
- **Graphify Obsidian export.** Described on `graphify.com/vs/obsidian`, but the current README does not mention it; the `--obsidian` flag from older releases was not confirmed. Whether re-export overwrites or merges is unknown. The `graphify-export` Rust crate may be a separate project.
- **Graphify PreToolUse hook and SHA-256 cache** come from PyPI listing summaries for older versions, not the current README.
- **code-review-graph Obsidian export details** come from a third-party explainer; frontmatter fields and edge typing are not confirmed.
- **deepwiki-open internals** (RAG, embeddings, FAISS) were not confirmed; update behaviour is from a competitor's comparison article.
- **DeepWiki internals** are not public. "Last indexed" date and MCP tool names are from a competitor's article. The "never regenerated" statement is the OpenWrt forum's, not Cognition's.
- **Google Code Wiki staleness measurement** (0–1 commits behind) and its private-repo waitlist status in October 2026 are from the same competitor article.
- **Mutable.ai** acquisition date and discontinuation are from secondary sources that disagree.
- **Autodoc** details are from search summaries and directory listings, not a direct read of the README.
- **CodeWiki** parser library (tree-sitter or other) and decomposition token thresholds were not found on the README; the `skills/codewiki-wiki-generator` folder was seen but not opened.
- **OpenWiki** release number and date, supported agent list and "stated weaknesses" are from a competitor's article; the GitHub Releases section was empty in the fetched page.
- **repowise** page types and the 260-pages-in-1m58s figure are the vendor's own.
- **Serena** memory file layout, onboarding flow and staleness handling were not on the README.
- **Aider** tree-sitter/PageRank internals are from third-party code analyses; the official page confirms only the graph ranking and the 1k-token default.
- **codebase-vault-docs** `SKILL.md` could not be fetched (404 at the guessed path), so "no frontmatter schema, no typed links" rests on the README alone.
- **tutor-skills** codebase templates were not opened; "no frontmatter or typed links" rests on the README alone.
- **Karpathy gist** star and fork counts were not read. The HN comment on second-order errors and the aksel.mataroa.blog critique are from search summaries.
- **AGENTS.md study** figures other than "over 20%" cost increase vary between secondary summaries; only the abstract was read.
- **CodeGraph (tool-call and cost test on Hono)** is cited from a search summary of a DEV post; the tool itself was not reviewed.
- **Not investigated:** Zread, Kiro, Litho (deepwiki-rs), CodeBoarding, Meta DocAgent, Davia, Driver.ai, nashsu/llm_wiki and other Karpathy-pattern repos beyond those listed. No clones or downloads of any repository were made; all findings are from web pages.
- **Marketplace search** was by web search only; individual Claude plugin marketplaces were not enumerated, so small unpublished skills may exist that were not found.
