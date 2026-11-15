# 05. Deterministic tooling: dependency extraction, vault validation and graph queries

Research date: 2026-11-14/15. Scope: tools the skill could call (or imitate) to extract real dependency structure from code, and tools to validate and query the generated vault.

How to read the evidence in this report:

- "Last push" dates come from the public GitHub repository API (`pushed_at`, any branch), read on 2026-11-14/15. It is a proxy for maintenance, not a release date.
- Anything I could not confirm from a primary source today is marked **(unverified)**.
- No tool was installed or run for this report. Everything is from documentation, READMEs and repository metadata.

## Summary of recommendations

1. **Ship a zero-dependency baseline and make every better tool optional.** One bundled Python script, standard library only, that inventories files, parses manifests, extracts import edges (Python via `ast`, other languages via regexes) and emits a JSON edge list. Nothing else is required for the skill to work.
2. **Use better extractors only when they are already on the machine.** Ecosystem-native commands (`go list`, `cargo metadata`, `npm ls`) and already-installed tools (dependency-cruiser, grimp, universal-ctags, ast-grep) give exact edges with no install step. Do not install anything on the user's behalf by default.
3. **Offer one opt-in "rich" tier through `uv run` with PEP 723 inline metadata**, for symbol-level definition/reference edges using tree-sitter (Aider's approach). It needs `uv` and network on first run, so it cannot be the default.
4. **Skip the heavy analysers.** CodeQL, Joern, Semgrep and SCIP are too heavy, too restricted by licence, or too build-dependent for a general public skill. GitHub stack-graphs is archived.
5. **Record provenance on every edge.** `extracted` (a tool or parser saw it) versus `inferred` (the LLM concluded it), with the method and evidence. Keep frontmatter flat, because Obsidian's Properties UI does not support nested properties, and put per-edge detail in a sidecar file.
6. **Write the validator as a small bundled script.** No existing tool covers more than a third of the checks, and the important ones (inverse edges, `sources:` paths, stale hashes, drift) are specific to this vault format. Existing linters can be optional extras.
7. **Constrain frontmatter to a strict YAML subset.** Neither the Python standard library nor Node's built-ins include a YAML parser. A strict subset (scalars and flat lists of quoted strings) can be parsed in about a hundred lines and doubles as schema enforcement.
8. **Use one canonical graph file: node-link JSON**, sorted deterministically so it diffs cleanly. Generate Mermaid, DOT and GraphML from it on demand.
9. **Implement the query set in the standard library.** Direct and transitive dependencies, reverse dependencies, impact of a changed file, cycles, shortest path, orphans and hubs are all short breadth-first or Tarjan routines at vault scale. networkx is not needed.
10. **"Compare" is two different features**: diffing two graph snapshots across commits, and diffing the documented graph against a fresh extraction (drift). Both reduce to a set difference over edges with stable keys.
11. **Agents should query the vault as plain files.** Ripgrep plus the bundled query script work headless and in CI. The official Obsidian CLI, Dataview, Bases and the Local REST API all need the Obsidian app running.
12. **CI integration is a thin wrapper**: run the validator, print GitHub workflow annotations, exit non-zero on errors. Staleness detection should use content hashes, not commit ranges, so it works in shallow clones.

## Comparison table A: extraction tools (Part A, item 1)

| Tool | Languages | Granularity | Install weight | Licence | Maintenance (as of 2026-11-15) | Output |
|---|---|---|---|---|---|---|
| [tree-sitter](https://github.com/tree-sitter/tree-sitter) | Any language with a grammar | Syntax tree; imports, definitions and references via queries. No name resolution across files | Library plus one grammar per language | MIT | Active, last push 2026-11-15 | In-memory tree; you write the queries |
| [tree-sitter-language-pack](https://github.com/xberg-io/tree-sitter-language-pack) ([PyPI](https://pypi.org/project/tree-sitter-language-pack/)) | 371 grammars per PyPI | Same as tree-sitter, plus a "code intelligence" layer extracting functions, classes, imports, docstrings and symbols | `pip`/`npm` install; wheels about 2 MB because **grammars are downloaded on first use** and cached; `prefetch()` and `ts-pack download` exist | MIT; only permissively licensed grammars | Active, v1.25.0 released 2026-11-06. Repo has moved orgs twice (Goldziher, kreuzberg-dev, now xberg-io) | Python/Node/Rust APIs, `ts-pack` CLI, MCP server |
| [py-tree-sitter-languages](https://github.com/grantjenks/py-tree-sitter-languages) | Fixed bundled set | Same as tree-sitter | `pip`; grammars bundled in the wheel | Apache-2.0 **(unverified, API reports no SPDX id)** | Stale, last push 2025-02-17 | Python API |
| [ast-grep](https://github.com/ast-grep/ast-grep) | [28 built-in](https://ast-grep.github.io/reference/languages.html), custom grammars possible | Structural pattern match per file; no cross-file resolution | Single binary; also on npm, pip, cargo | MIT | Active, last push 2026-11-14 | JSON matches **(JSON flag not re-verified today)** |
| [universal-ctags](https://github.com/universal-ctags/ctags) | Many parsers; exact count **(unverified)** | Definitions (tags); references only for some parsers. No edges between files | System package or build; not on pip/npm | GPL-2.0 | Active, last push 2026-11-08 | Tags file, or [JSON Lines](https://docs.ctags.io/en/latest/man/ctags-json-output.5.html) only if built with libjansson |
| [SCIP](https://github.com/scip-code/scip) indexers | TypeScript/JS, Java/Kotlin/Scala, Python, Go, C/C++, Rust (via rust-analyzer); community: C#, Dart, PHP ([list](https://sourcegraph.com/docs/code-search/code-navigation/writing_an_indexer)) | Precise symbol-level definitions and references, compiler accuracy | One indexer per language, each needing that language's toolchain and usually a resolvable or buildable project. [scip-python](https://github.com/sourcegraph/scip-python) needs Node 16+, Python 3.10+ and the project's virtualenv active | Apache-2.0 for scip and scip-typescript; scip-python licence **(unverified)** | Active: scip 2026-11-11, scip-typescript 2026-11-15, scip-python 2026-11-13. `scip`, `scip-go`, `scip-java` now live under the `scip-code` org | Protobuf index file |
| [multilspy](https://github.com/microsoft/multilspy) | 12 languages (Java, Python, Rust, C#, TS/JS, Go, Dart, Ruby, Kotlin, PHP, C++) | Symbol level: definition, references, hover, document symbols, completions | `pip`, then it downloads language-server binaries automatically (network) | MIT | Low activity but alive, last push 2026-10-29; PyPI at v0.0.15 per aggregator **(unverified)** | Python API returning LSP JSON |
| [Serena](https://github.com/oraios/serena) | "Over 40" via language servers | Symbol level: find symbol, file outline, find referencing symbols | `uv tool install`, plus language servers | Per README: SolidLSP component MIT, Serena application GPL-3.0-or-later **(recent change; verify before depending on it)** | Very active, last push 2026-11-14, 31k stars | MCP tools |
| [Claude Code LSP tool](https://code.claude.com/docs/en/tools-reference) | 13 official plugins: C/C++, C#, Go, Java, Kotlin, Liquid, Lua, PHP, Python, Ruby, Rust, Swift, TS/JS ([list](https://code.claude.com/docs/en/plugins/code-intelligence.md)) | Symbol level: definition, references, type info, file symbols, workspace symbol search, implementations, call hierarchies | Built in, but inactive until the user installs a plugin **and** the language-server binary. Not started in cloud sessions | Part of Claude Code | Current | Tool results to the model only; not callable from a script |
| [GitHub stack-graphs](https://github.com/github/stack-graphs) | Was: a few languages via tree-sitter rules | Precise name resolution | Rust crates | MIT OR Apache-2.0 | **Archived 2025-09-09, read-only** | Not recommended |
| [Semgrep CE](https://github.com/semgrep/semgrep) | 30+ **(count unverified)** | Pattern and dataflow rules within a file; [cross-file analysis is Pro only](https://semgrep.dev/docs/faq/comparisons/opengrep) | `pip`/brew, sizeable binary | Engine LGPL-2.1; registry rules under the separate Semgrep Rules License. Fork: [Opengrep](https://github.com/opengrep/opengrep) (LGPL-2.1) | Active, last push 2026-11-13 | JSON, SARIF |
| [CodeQL](https://github.com/github/codeql) | [C/C++, C#, Go, Java/Kotlin, JS/TS, Python, Ruby, Rust, Swift, GitHub Actions](https://codeql.github.com/docs/codeql-overview/supported-languages-and-frameworks/) | Full semantic database: calls, dataflow, types | Large CLI bundle; a database build step; compiled languages need a working build | Queries MIT; the **CLI is proprietary and restricted to open-source codebases, academic research, or paid licence holders** ([terms](https://securitylab.github.com/tools/codeql/license)) | Active, last push 2026-11-13 | Query results as CSV, JSON, SARIF |
| [Joern](https://github.com/joernio/joern) | C/C++, Java, JS/TS, Python, Kotlin, Go, PHP, Ruby, Swift, C#, binaries **(full list from secondary source, unverified)** | Code property graph: AST, control flow, dataflow, calls | Needs JDK 21; large download | Apache-2.0 | Active, last push 2026-11-14 | [neo4j CSV, GraphML, GraphSON, DOT](https://docs.joern.io/export/) |
| [dependency-cruiser](https://github.com/sverweij/dependency-cruiser) | JS, TS, CoffeeScript, LiveScript; Vue and Svelte with their compilers present | File/module import edges with resolution; rule validation | `npm` | MIT | Active, last push 2026-11-12, v17.x | json, dot, mermaid, d2, html, csv, text, markdown |
| [madge](https://github.com/pahen/madge) | JS (AMD, CommonJS, ES modules), TS, CSS preprocessors | File import edges; circular, orphans, leaves, "depends on" | `npm`; Graphviz only for images | MIT | Slow, last push 2026-01-21 | JSON, DOT, images |
| [pydeps](https://github.com/thebjorn/pydeps) | Python | Module import edges, **found from bytecode through the import machinery**, so the package and its deps must be importable | `pip`; Graphviz unless `--nodot`/`--no-output` | BSD-2-Clause | Active, last push 2026-11-09, v3.0.9 | SVG/PNG, DOT, JSON-style deps |
| [import-linter](https://github.com/import-linter/import-linter) / [grimp](https://github.com/python-grimp/grimp) | Python | Module import graph with queries (upstream/downstream modules, shortest chain) and layering contracts | `pip`; grimp has a Rust core | BSD-2-Clause | Active; import-linter 2.11 dated 2026-03-06 per its [release notes](https://import-linter.readthedocs.io/en/stable/release_notes/) | Python API; contract pass/fail |
| [tach](https://github.com/tach-org/tach) | Python | Declared module boundaries, cycles; `tach map` JSON, `tach show` DOT | `pip`, Rust core | MIT | Repo moved from gauge-sh to tach-org; current activity **(unverified)** | JSON, DOT |
| `go list`, `cargo metadata`, `mvn dependency:tree`, `npm ls` | One ecosystem each | Package level; `go list -deps -json` also gives per-package import lists | Already present if the project builds | Toolchain licences | Maintained with toolchains | JSON ([go](https://pkg.go.dev/cmd/go), [cargo](https://doc.rust-lang.org/cargo/commands/cargo-metadata.html), [npm](https://docs.npmjs.com/cli/commands/npm-ls/)); text/DOT/GraphML for [Maven](https://maven.apache.org/plugins/maven-dependency-plugin/tree-mojo.html) |
| [Aider repo map](https://aider.chat/docs/repomap.html) (technique, not a tool to call) | Whatever its tree-sitter tag queries cover | File-level graph weighted by symbol definitions/references, then graph ranking | Part of aider (`pip`); several standalone re-implementations exist | Apache-2.0 | Aider last push 2026-05-22, so slowing | Text map; graph is internal |
| [graphify](https://github.com/safishamsi/graphify) (closest prior art) | About 40 via tree-sitter | Code graph with edges tagged `EXTRACTED` or `INFERRED` | `uv tool install graphifyy` | Apache-2.0 and MIT files present | Active **(push date not checked)** | `graph.json` (NetworkX format per secondary source), `GRAPH_REPORT.md`, `graph.html`; `--wiki` for Markdown |

## Comparison table B: validator building blocks (Part B, item 5)

| Tool | What it can check for this vault | What it cannot | Runtime | Headless/CI | Maintenance |
|---|---|---|---|---|---|
| [obsidiantools](https://github.com/mfarragher/obsidiantools) | Wikilinks, embeds, backlinks, front matter, `nonexistent_notes`, `isolated_notes`, NetworkX graph | Schema, typed edges, inverses, sources, hashes. Heavy deps: pandas, numpy, lxml, networkx, bs4. Built for "shortest path when possible" links | Python 3.9+, pip | Yes | Slow, last push 2026-06-07; BSD-3 |
| [markdownlint](https://github.com/DavidAnson/markdownlint) / [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2) | Markdown style. Custom rules can read front matter lines **(per third-party page, unverified)** | No wikilink resolution, no schema, no graph checks | Node | Yes | Active, last push 2026-11-15; MIT |
| [remark-validate-links](https://github.com/remarkjs/remark-validate-links) | Relative Markdown links and heading anchors | Wikilinks **(not supported natively, unverified)** | Node | Yes | Quiet, last push 2025-02-21; MIT |
| [remark-lint-frontmatter-schema](https://github.com/JulianCataldo/remark-lint-frontmatter-schema) | YAML front matter against a JSON Schema (uses ajv) | Everything else | Node, remark stack | Yes | Stale, last push 2024-09-21; ISC |
| JSON Schema via [check-jsonschema](https://github.com/python-jsonschema/check-jsonschema) or ajv | Schema validation once front matter has been extracted to JSON | Does not read Markdown; needs an extraction step | pip or npm | Yes | Active **(not checked today)** |
| [lychee](https://github.com/lycheeverse/lychee) | Broken links, including [wikilinks](https://lychee.cli.rs/recipes/md-wikilinks/) with `--include-wikilinks --base-url <dir> --fallback-extensions md`; `--offline` mode | Wikilinks are off by default; no front matter, no graph. Combination of `--offline` with wikilinks **(unverified)** | Single Rust binary | Yes; [lychee-action](https://github.com/lycheeverse/lychee-action) | Active, last push 2026-11-13; Apache-2.0 |
| [obsidian-linter](https://github.com/platers/obsidian-linter) | YAML key ordering, formatting, heading rules | It is an Obsidian plugin; no documented CLI **(unverified)** | Obsidian app | No | Active, last push 2026-10-31; MIT |
| [vale](https://github.com/vale-cli/vale) | Prose style and terminology | Not a link or schema checker **(unverified in docs today)** | Single Go binary | Yes | Active; org renamed from errata-ai to vale-cli; MIT |
| Official [Obsidian CLI](https://obsidian.md/help/cli) | `orphans`, `unresolved`, `deadends`, `backlinks`, `properties` exactly as Obsidian resolves them | Needs the app running; no schema or custom checks | Obsidian 1.12.4+ | No | Current |
| **Small bundled script (recommended)** | All checks in section 5 | Prose quality | Python stdlib | Yes | Owned by the project |

## Part A

### 1. Language-agnostic extraction options

Details beyond the table, grouped by what they mean for the skill.

**Syntax-level, any language (tree-sitter family).** Tree-sitter gives a parse tree and a query language; its own docs describe a ["tags" convention for definitions and references](https://tree-sitter.github.io/tree-sitter/4-code-navigation.html). It does not resolve names across files: knowing that `foo()` is called is not knowing which `foo`. Two practical consequences:

- Import statements are syntactically explicit, so tree-sitter extracts them reliably. That is the edge type this skill most needs.
- Symbol-level edges from tree-sitter are name matches. They are useful as weighted hints, which is exactly how Aider uses them.

The packaging situation matters for a no-network skill. `tree-sitter-language-pack` 1.x no longer bundles grammars: its README says it "downloads each parser on first use so the install stays small", with `prefetch()` for up-front download. The older `py-tree-sitter-languages` bundles grammars but has had no push since February 2025.

**Aider's repo map.** Aider parses files with tree-sitter, takes definitions and references from modified `tags.scm` queries, builds a graph "where each source file is a node and edges connect files which have dependencies", and ranks it with "a graph ranking algorithm" ([2023 write-up](https://aider.chat/2023/10/22/repomap.html), [docs](https://aider.chat/docs/repomap.html)). The official pages do not name the algorithm; third-party analyses of [`repomap.py`](https://github.com/Aider-AI/aider/blob/main/aider/repomap.py) say it is personalised PageRank via networkx **(source file not re-read today)**. The useful idea for this skill is the ranking: it tells the generator which files deserve their own note and which can be grouped.

**Precise, symbol-level (SCIP, LSP).** These give compiler-accurate references but need a working toolchain and resolved dependencies per language.

- SCIP indexers are batch tools that write one index file, which suits a script. The cost is one indexer per language plus a buildable project.
- LSP servers answer one question at a time. Driving them in bulk (every symbol in a repo) is slow and fragile. multilspy and Serena wrap this; both download or require language servers.
- Claude Code's own LSP tool is the cheapest of the three when it happens to be active, because the user has already set it up. It is a model-facing tool, so a bundled script cannot call it. Its fit is spot verification: the agent confirms a specific inferred edge with "find references" before recording it. The skill cannot rely on it: it is inactive without a plugin and binary, and is not started in cloud sessions.

**Semantic analysers (Semgrep, CodeQL, Joern).** All three answer richer questions than "who imports whom", and all three are a poor fit as a dependency of a public skill:

- CodeQL's CLI terms restrict use to open-source codebases, academic research or paying customers. A skill for "any codebase" cannot assume that.
- Joern needs JDK 21 and builds a full code property graph, far more than documentation needs.
- Semgrep CE analyses within one file; cross-file analysis is a Pro feature. Its engine is LGPL-2.1 and its rule registry has a separate licence. Its one relevant strength is framework-aware pattern rules (routes, queries), which matters for section 3.

**Ecosystem-specific import graphers (dependency-cruiser, madge, pydeps, grimp, tach).** These produce exactly the file/module import graph the skill wants, with proper resolution of path aliases, `tsconfig` paths, package `__init__` files and so on. That resolution is the hard part a regex baseline gets wrong. They cover one ecosystem each. pydeps is the odd one: it reads bytecode through Python's import machinery, so the project must be importable in the current environment.

**Build-tool commands.** `go list -json`, `cargo metadata --format-version 1` and `npm ls --json` are authoritative for package-level structure and are present whenever the project can be built. Caveats: `mvn dependency:tree` typically resolves from remote repositories, and `cargo metadata` may touch the network unless run with `--offline` or `--no-deps` **(flags from memory, see the [cargo docs](https://doc.rust-lang.org/cargo/commands/cargo-metadata.html))**.

**Prior art to study.** graphify already does "tree-sitter extraction plus LLM inference, with each edge tagged `EXTRACTED` or `INFERRED`" and writes a `graph.json`. Its README says code parsing "is deterministic, no LLM, nothing leaves your machine". Secondary sources also mention an `AMBIGUOUS` tag and confidence scores; the current README does not **(unverified)**. It is installed as a Python tool rather than being dependency-free, and its Markdown output is a flag rather than the primary artefact.

### 2. Package-manifest extraction

External dependency notes need only names, version constraints and (optionally) resolved versions. Two routes:

**Direct parsing in the bundled script.** Most manifests are in formats the Python standard library reads:

| Manifest | Format | Standard-library parser |
|---|---|---|
| `package.json`, `package-lock.json`, `composer.json` | JSON | `json` |
| `pyproject.toml`, `Cargo.toml`, `Cargo.lock`, `uv.lock`, `poetry.lock` | TOML | [`tomllib`](https://docs.python.org/3/library/tomllib.html), Python 3.11+ |
| `pom.xml`, `*.csproj`, `packages.config` | XML | `xml.etree.ElementTree` |
| `go.mod`, `requirements.txt`, `Gemfile`, `build.gradle` | Line-oriented or a DSL | Regex; Gradle and Gemfile are code, so results are best-effort |
| `pnpm-lock.yaml`, `pubspec.yaml`, `environment.yml` | YAML | None in the standard library; skip, or handle with the subset parser |

**Existing multi-ecosystem parsers**, usable when already installed:

- [syft](https://github.com/anchore/syft): SBOMs for directories, images and archives across "dozens of packaging ecosystems"; outputs CycloneDX, SPDX and Syft JSON. Apache-2.0, active (last push 2026-11-14). Distributed as release binaries. Whether a directory scan ever needs network is not stated **(unverified)**.
- [cdxgen](https://github.com/cdxgen/cdxgen) (moved from the CycloneDX org): CycloneDX output for many languages, but needs the ecosystem toolchain for some (Maven, Gradle, sbt). Registry lookups for licences are off unless `FETCH_LICENSE` is set. Fully offline operation **(unverified)**.
- [osv-scanner](https://github.com/google/osv-scanner) with [osv-scalibr](https://github.com/google/osv-scalibr): built for vulnerability matching, but its extractors read a [wide set of lockfiles](https://google.github.io/osv-scanner/supported-languages-and-lockfiles/). It has an `--offline-vulnerabilities` mode and SPDX/CycloneDX output. Apache-2.0, active (last push 2026-11-14).

Assessment: these tools are built for security inventories and list every transitive package. Documentation wants the direct dependencies and why they are used, which direct manifest parsing gives with no install. Use an SBOM tool only as an optional cross-check, never as a requirement.

### 3. Dependencies that import analysis misses

| Dependency kind | How existing tools approach it | Deterministic signal available to the skill | Recommended handling |
|---|---|---|---|
| Declared service topology | Read deployment descriptors | `docker-compose.yml` `depends_on` ([compose config](https://docs.docker.com/reference/cli/docker/compose/config/)), Kubernetes manifests, [Terraform graph](https://developer.hashicorp.com/terraform/cli/commands/graph), [Backstage `catalog-info.yaml`](https://backstage.io/docs/features/software-catalog/descriptor-format/) `dependsOn`/`consumesApis` | `extracted` when the file states it explicitly |
| Build-system edges | Query the build graph | [`bazel query`](https://bazel.build/query/guide), [Nx project graph](https://nx.dev/docs/features/explore-graph), Gradle dependency reports, workspace members in `Cargo.toml`/`package.json`/`go.work` | `extracted` |
| API contracts | Parse the schema files | OpenAPI, protobuf/gRPC, GraphQL schema files define provided APIs. Which service *consumes* them is rarely declared | Provider: `extracted`. Consumer: `inferred` |
| HTTP/RPC calls between services | Semgrep/CodeQL framework models; runtime tracing ([OpenTelemetry](https://opentelemetry.io/docs/specs/semconv/) service graphs) | Grep for client calls and URL literals; route decorators. URLs are often built from config at run time | `inferred`, with file and line as evidence |
| Database tables | SQL parsers such as [sqlglot](https://github.com/tobymao/sqlglot) and [sqllineage](https://github.com/reata/sqllineage); ORM model inspection | Migration files and ORM model classes name tables explicitly; raw SQL strings can be grepped | Table definitions: `extracted`. "Module X reads table Y": `inferred` unless from a literal query |
| Message queues and events | Mostly runtime tracing; some framework-specific rules | Topic and queue names as string literals or config keys | `inferred`; pair publisher and subscriber only when the same literal appears on both sides |
| Env vars and config | Grep-based | `os.environ[...]`, `process.env.X`, `os.Getenv(...)`, `.env.example`, Helm values | Reads of a literal name: `extracted`. What the variable connects to: `inferred` |
| Dynamic dispatch, DI, plugins, reflection | Call-graph analysis (CodeQL, Joern) with known imprecision | DI container registrations and entry-point tables (`[project.entry-points]`, Spring config) are sometimes declarative | Declarative registrations: `extracted`. Everything else: `inferred` |

General finding: a web search found no established open-source tool that statically extracts cross-service dependencies across languages. What exists is academic (for example a GraalVM-based Java prototype) or commercial, and practitioner sources agree that static analysis shows what code *can* call while tracing shows what it *does* call ([overview](https://last9.io/blog/guide-to-application-dependency-mapping.md)). [specfy/stack-analyser](https://github.com/specfy/stack-analyser) detects technologies in a repo from files and manifests, which is a related but narrower job.

So the rule for the skill: **extract what a file states explicitly; let the LLM infer the rest and say so.** An inferred edge must carry evidence (path and line, or the config key) so that a reader, or the validator, can check it.

### 4. Recommended tiered strategy

**Tier 0: baseline, always available.** One bundled Python script using only the standard library.

- File inventory from `git ls-files` (respects `.gitignore`), with a directory walk as fallback.
- Manifest parsing as in section 2.
- Python imports via [`ast`](https://docs.python.org/3/library/ast.html): exact, including relative imports.
- Other languages via per-language import regexes: JS/TS `import`/`export from`/`require`, Go `import`, Rust `use`/`mod`, Java/Kotlin/Scala `import`, C/C++ `#include`, C# `using`, Ruby `require`, PHP `use`. Resolve relative paths to repository files where the language allows; leave package-style imports as module names matched against the inventory.
- Declarative non-import sources: compose files, workspace members, entry points, env-var reads of literal names.
- Output: a JSON edge list, each edge with `method` (`ast`, `regex`, `manifest`, `config`) and source location.

Known weaknesses of regex imports, to state in the skill's docs: path aliases (`tsconfig` paths, webpack aliases), re-exports and barrel files, conditional and dynamic imports, macros and generated code, and imports inside strings or comments. For this reason regex edges should be marked with their method, so they can be told apart from `ast` or tool edges.

What Node built-ins could do instead: file walking, JSON manifests, regexes, hashing and SQLite ([`node:sqlite`](https://nodejs.org/api/sqlite.html)) are all there. Node has no built-in TOML, YAML or XML parser and no parser for its own language, so a Node-only baseline would be regex throughout. Python is the stronger choice for the baseline because of `ast`, `tomllib`, `xml.etree` and [`graphlib`](https://docs.python.org/3/library/graphlib.html).

**Tier 1: opportunistic, no install.** The script probes for tools and uses what it finds. Nothing is installed.

- Ecosystem commands: `go list -deps -json`, `cargo metadata --no-deps`, `npm ls --json`.
- Import graphers already in the project's dev dependencies: dependency-cruiser or madge in `node_modules`; grimp, pydeps or tach in the active Python environment.
- General tools on `PATH`: `ctags` with JSON support for symbol inventories, `ast-grep` for structural import matching.
- The agent's own LSP tool, when active, for confirming individual edges.

Edges from these replace Tier 0 regex edges for the same files and record the tool name and version.

**Tier 2: opt-in rich extraction.** A second script with PEP 723 inline metadata, run with `uv run`, depending on tree-sitter and a grammar pack. It adds symbol-level definition/reference edges and a ranking of files by importance.

Is `uv run` with PEP 723 a reasonable way to ship richer scripts? Yes, as an option, with clear limits:

- The Agent Skills documentation recommends exactly this pattern: "bundle a script in `scripts/` that declares its own dependencies inline" and run it with `uv run`; `pipx run` also understands PEP 723 ([guide](https://agentskills.io/skill-creation/using-scripts)).
- It needs `uv` installed, which is "not bundled with Python", and it needs network on first run to fetch packages (the [uv guide](https://docs.astral.sh/uv/guides/scripts/) implies this without stating it). With `tree-sitter-language-pack` there is a second download, for grammars.
- Reproducibility and supply-chain controls exist: version pins, `uv lock --script` (writes `script.py.lock` beside the script), and `exclude-newer` in `[tool.uv]`. A third-party [threat model for skills](https://safedep.io/agent-skills-threat-model/) flags unpinned script dependencies as a risk, so pin and lock.
- uv has an offline mode that uses only its cache **(flag from memory; see the [CLI reference](https://docs.astral.sh/uv/reference/cli/))**. After one successful online run the rich tier can work offline.

Because of the first two points this tier must fail soft: if `uv` is missing or the network is blocked, the skill reports that and continues on Tier 0/1.

**Tier 3: LLM inference.** The agent reads code and adds the edges of section 3 that no tool states. Every such edge is `inferred` and carries evidence.

**Not recommended as tiers:** SCIP (precise, but per-language toolchains and builds), CodeQL (licence), Joern (JDK and weight), Semgrep (single-file in CE; licence complexity), stack-graphs (archived), multilspy/Serena (download language servers; Serena's application licence is now GPL per its README).

**Recording provenance in frontmatter.** Two constraints shape this:

- Obsidian's Properties UI has no support for nested properties, and links in properties must be quoted strings ([Properties help](https://obsidian.md/help/properties)). A list of `{target, provenance, evidence}` objects would be valid YAML but awkward in Obsidian.
- The standard library has no YAML parser, so the simpler the frontmatter, the more reliable the tooling.

Recommended shape: flat lists of quoted wikilinks, one property per edge type and provenance, plus a sidecar file for per-edge detail.

```yaml
---
type: module
sources:
  - src/auth/session.py
source_hash: "9c1f0e4a"
depends_on:
  - "[[db-client]]"
depends_on_inferred:
  - "[[billing-service]]"
---
```

```json
{"source": "auth-session", "target": "billing-service", "type": "depends_on",
 "provenance": "inferred", "method": "llm", "confidence": "medium",
 "evidence": ["src/auth/session.py:88"], "extractor": null}
```

- `provenance`: `extracted` or `inferred`. Keep it to two values; `method` carries the detail (`ast`, `regex`, `manifest`, `config`, `tool:<name>@<version>`, `llm`).
- An alternative that avoids a sidecar is a fixed "Edges" table in the note body. It keeps everything in one file but makes parsing depend on Markdown table layout. This is an open decision (see the end).
- When a later extraction finds an edge that was `inferred`, the validator should offer to promote it.

## Part B

### 5. Validator design

**Checks.** Severity is a default; each should be configurable.

Frontmatter and naming

| ID | Check | Default |
|---|---|---|
| V01 | Frontmatter block present and parseable within the supported YAML subset | error |
| V02 | Required keys present for the note's `type` | error |
| V03 | Values have the right type and enum membership (`type`, `status`, provenance, confidence); unknown keys reported | error / warning |
| V04 | Note names unique across the vault, compared case-insensitively; aliases do not collide with names | error |
| V05 | File names free of characters Obsidian or Windows reject, and of `#`, `^`, `[`, `]`, `\|` which break wikilinks | error |
| V06 | No nested properties; wikilinks in properties are quoted; tag syntax valid | error |
| V07 | Vault schema version recorded and supported by this validator | error |

Links

| ID | Check | Default |
|---|---|---|
| V08 | Body wikilinks resolve, including `[[note#heading]]`, `[[note#^block]]`, `[[note\|alias]]` and embeds; code blocks ignored | error |
| V09 | Wikilinks in frontmatter properties resolve | error |
| V10 | Relative Markdown links and links to source files resolve | error |
| V11 | No wikilink resolves to more than one note | error |

Graph

| ID | Check | Default |
|---|---|---|
| V12 | Orphan notes (no inbound or outbound edges), with an allow-list for index notes | warning |
| V13 | Every note reachable from the root index note | warning |
| V14 | Inverse consistency: if A `depends_on` B then B `used_by` A (or, if inverses are derived, no hand-written inverse exists) | error, auto-fixable |
| V15 | Edge type allowed between the two note types (for example `depends_on` may not point at a `decision` note) | error |
| V16 | No self-loops or duplicate edges; the same edge not both `extracted` and `inferred` | warning, auto-fixable |
| V17 | Dependency cycles reported | info |
| V18 | Every `inferred` edge has evidence and a confidence value | warning |

Sources and freshness

| ID | Check | Default |
|---|---|---|
| V19 | Every `sources:` path exists in the repository | error |
| V20 | Stale hash: recorded `source_hash` differs from the current hash of the note's sources | warning |
| V21 | Coverage: source files not claimed by any note; paths claimed by several notes | info |
| V22 | Drift: `extracted` edges in the vault absent from a fresh extraction, and fresh edges absent from the vault | warning |
| V23 | External-dependency notes match manifests: missing, extra, or version mismatch | warning |
| V24 | Canonical graph file, if committed, matches the graph rebuilt from the notes | error |
| V25 | Note size above a line threshold (notes are meant to be small) | info |

**Stale-hash design.** Hash content, not commits.

- Per note, `source_hash` is a digest over the sorted list of (path, git blob id) for its `sources:`. Blob ids come from `git ls-files -s` without reading file contents, or from `hashlib` when outside git.
- A commit-based scheme ("note generated at commit X, diff X..HEAD") fails in shallow CI clones and after rebases. A content hash does not.
- Directory or glob sources need a defined expansion rule (tracked files only, sorted) so the hash is stable.
- Open point: a whitespace-only change makes a note "stale". Accepting that is simpler than normalising code.

**Reuse or write?** Write a small bundled script.

- The checks that matter most (V14, V15, V18 to V24) are specific to this vault format; no surveyed tool does them.
- The reusable part is small. Wikilink resolution and orphan detection are a few dozen lines once notes are indexed by name.
- obsidiantools is the nearest fit but pulls in pandas, numpy and lxml, and its last push was June 2026.
- lychee and markdownlint are good optional extras for external URLs and Markdown style, run separately in CI when present.
- JSON Schema is worth keeping as the *published description* of the frontmatter (useful to editors and other tools), while the bundled validator enforces the same rules in code, since the standard library has no JSON Schema validator either.

**The YAML problem.** Neither Python's standard library nor Node's built-ins parse YAML. Options:

- **Strict subset (recommended).** The skill only ever writes scalars and flat lists of quoted strings. The validator parses exactly that and reports anything else as V01. Hand edits that stray outside the subset are caught, not silently misread.
- JSON frontmatter. Obsidian accepts it but "the JSON block will be read, interpreted, and saved as YAML", so it does not survive editing in the app.
- PyYAML through PEP 723. Correct for all YAML, but moves the validator out of the zero-dependency tier.

**Script interface**, following the [Agent Skills guidance](https://agentskills.io/skill-creation/using-scripts): no prompts, `--help`, JSON on stdout and diagnostics on stderr, bounded output, distinct exit codes (0 clean, 1 errors found, 2 usage or internal error), and `--fix` limited to mechanical repairs (inverse edges, duplicates). It should never rewrite prose or refresh hashes on its own, because a refreshed hash claims a human or agent re-read the source.

### 6. Graph export and query

**Building the graph.** Nodes are notes, keyed by note name, with `type`, `path`, `sources` and `source_hash`. Edges come from typed frontmatter properties, plus untyped `mentions` edges from body wikilinks. Edge attributes: `type`, `provenance`, `method`, `evidence`.

**Formats.**

| Format | Role | Notes |
|---|---|---|
| Node-link JSON | **Canonical** | The shape networkx reads and writes ([readwrite reference](https://networkx.org/documentation/stable/reference/readwrite/index.html)) and close to [graphology's serialised form](https://graphology.github.io/). graphify uses NetworkX JSON for its `graph.json` (per secondary source). Sort nodes and edges and fix key order so the file diffs cleanly |
| [Mermaid](https://mermaid.js.org/syntax/flowchart.html) | Embedding in notes and PR comments | Obsidian and GitHub both render it. Only for small subgraphs; large graphs become unreadable |
| [DOT](https://graphviz.org/doc/info/lang.html) | Rendering with Graphviz | Text, trivial to emit |
| [GraphML](http://graphml.graphdrawing.org/) | Import into Gephi, yEd, Cytoscape | XML; `xml.etree` can write it |
| [JSON Canvas](https://jsoncanvas.org/) | An Obsidian canvas of a subgraph | Optional; needs a layout step |
| [JSON Graph Format](https://jsongraphformat.info/) | Alternative canonical format with a published schema | Less tooling than node-link |

**Libraries.** [networkx](https://github.com/networkx/networkx) (Python, active, BSD-3 **(licence from memory)**) and [graphology](https://github.com/graphology/graphology) (JS, MIT, last push 2026-11-10) both cover every query below, with [algorithm libraries](https://networkx.org/documentation/stable/reference/algorithms/index.html) for centrality and communities. Neither is needed for the core set: a documentation vault has hundreds to low thousands of nodes, and breadth-first search, Tarjan's strongly-connected components and a topological sort (`graphlib.TopologicalSorter` is in the standard library) are enough. Keep networkx for the optional rich tier (PageRank, community detection).

**Query set for agents.**

| Query | Meaning | Implementation |
|---|---|---|
| `deps X` | What X depends on directly | Outbound edges |
| `rdeps X` | What depends on X | Inbound edges |
| `closure X [--reverse]` | Transitive dependencies or dependents | Breadth-first search |
| `impact <path>...` | Notes whose `sources` include the file, plus everything that transitively depends on them | Source map, then reverse closure |
| `impact --diff <git range>` | Same, for the files changed in a range | `git diff --name-only`, then `impact` |
| `cycles` | Dependency cycles | Tarjan SCC |
| `path A B` | Shortest dependency chain | Breadth-first search |
| `neighbours X --depth N` | Local subgraph, for loading context | Bounded breadth-first search |
| `orphans`, `hubs` | Unlinked notes; highest in-degree notes | Degree counts |
| `layers` | Topological layering of the acyclic part | `graphlib` |
| `stats` | Counts by note type, edge type, provenance | Aggregation |

All queries take `--type` (edge types) and `--provenance extracted|inferred|all`, and can emit JSON, a note list, or Mermaid. Filtering by provenance matters: an agent assessing change impact may want every edge, while one checking architecture rules wants only extracted ones. graphify's rule that a path's confidence "is that of its weakest hop" is a sensible way to report multi-hop results.

**Compare, part 1: two snapshots.**

- Input: two canonical graph files, or two git revisions. For revisions, read the committed graph with `git show <rev>:<path>`, or rebuild from the notes at that revision in a temporary worktree.
- Output: nodes added, removed and changed (type, sources); edges added, removed and changed (provenance, method). Keys are note name for nodes and (source, target, type) for edges.
- Renames are the hard case: a renamed note looks like a removal plus an addition. A stable `id` in frontmatter, separate from the file name, solves it at the cost of one more required key.
- Presentation: JSON for agents, a Markdown summary for pull requests, and optionally a Mermaid diagram with added and removed edges styled differently.

**Compare, part 2: documented graph versus code (drift).**

- Run the extractor, project file-level edges onto notes through the `sources` map, and compare against the vault's `extracted` edges only.
- Categories: edge in code but not in docs; edge in docs but not in code; inferred edge now confirmed by extraction; source files with no note; notes whose sources are all gone.
- Compare like with like: an edge documented from a Tier 1 tool should not be reported missing because today's run only had Tier 0 regexes. Record the extractor in the graph and warn when tiers differ.
- Prior art: [Swimm](https://docs.swimm.io/features/keep-docs-updated-with-auto-sync) couples docs to code snippets and paths and verifies them on each pull request, auto-fixing trivial changes and failing the check on significant ones. dependency-cruiser, import-linter and tach do the converse, checking code against declared architecture rules.

### 7. How agents query an Obsidian vault today

| Route | Needs Obsidian running? | Headless / CI | Notes |
|---|---|---|---|
| Plain files with ripgrep and the agent's own Read/Grep tools | No | Yes | Works everywhere; frontmatter with one key per line and quoted wikilinks is easy to grep. No link resolution or graph traversal |
| Bundled query script over the canonical graph | No | Yes | Fills the traversal gap; recommended |
| Official [Obsidian CLI](https://obsidian.md/help/cli) (general availability in [1.12.4, 2026-02-27](https://obsidian.md/changelog/2026-02-27-desktop-v1.12.4/)) | **Yes**: "requires the Obsidian app to be running"; launches it otherwise | No | `backlinks`, `links`, `orphans`, `unresolved`, `deadends`, `properties`, `search`, `base:query`, `eval`, with JSON/TSV/CSV output on several |
| [Obsidian Headless](https://obsidian.md/help/headless) | No | Yes | Sync and Publish only; does not query or run plugins (per secondary summary of the help page) |
| [Local REST API with MCP](https://github.com/coddingtonbear/obsidian-local-rest-api) plugin | **Yes** | No | Built-in MCP server at `/mcp/`; fuzzy search and JsonLogic queries over frontmatter. MIT, last push 2026-10-17 |
| [mcp-obsidian](https://github.com/MarkusPfundstein/mcp-obsidian) (bridge to the REST plugin) | **Yes** | No | MIT, last push 2026-08-31 |
| Filesystem-based MCP servers, for example [mcpvault](https://github.com/bitbonsai/mcpvault), [obsidian-mcp](https://github.com/StevenStavrakis/obsidian-mcp), or a generic filesystem server | No | Yes | Read and write Markdown directly; no Obsidian index. Individual maintenance **(not checked)** |
| [notesmd-cli](https://github.com/Yakitrak/notesmd-cli) | No | Yes | Works on vault files without the app (per secondary source). MIT, last push 2026-10-13 |
| [Dataview](https://github.com/blacksmithgu/obsidian-dataview) | **Yes** (plugin) | No | Last push 2025-11-17, so slowing; successor project [Datacore](https://github.com/blacksmithgu/datacore) |
| [Bases](https://obsidian.md/help/bases/syntax) (core plugin, public since 1.9.10) | **Yes** | No | `.base` files are YAML with filters, formulas and views. The skill can generate them as static files for human readers; they only evaluate in the app |
| [obsidiantools](https://github.com/mfarragher/obsidiantools) | No | Yes | Python; gives a networkx graph of the vault |

There is no first-party Obsidian MCP server (per a [secondary survey](https://dev.to/grove_chatforest/obsidian-mcp-servers-eight-servers-three-architectures-no-official-blessing-gjn)).

Conclusion: anything the skill itself depends on must be file-based. App-dependent features (Bases views, Dataview blocks) are fine as extras for humans browsing the vault, provided nothing in validation or querying needs them.

### 8. CI integration

**GitHub Actions.** A workflow step that runs the bundled validator with a GitHub output mode.

- Annotations come from [workflow commands](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-commands) printed to stdout (`::error file=...,line=...::message`), so no extra action or token is needed.
- A Markdown summary (stale notes, drift, graph diff against the base branch) can be written to the job summary file.
- Python is preinstalled on GitHub-hosted runners **(unverified today)**, so a standard-library validator adds no setup step.
- Content hashes make the default shallow checkout sufficient for staleness. Only the snapshot diff against the base branch needs more history.
- Suggested policy: structural errors (V01 to V11, V14, V15, V19, V24) fail the job; staleness and drift (V20, V22, V23) warn by default, with a strict flag for teams that want them blocking. Swimm's own material notes developers "may be annoyed that they can't merge their code because the docs are out of sync" ([source](https://swimm.io/blog/sync-dont-sink-why-we-built-swimm-for-dev-teams)).
- Optional extra jobs when wanted: [lychee-action](https://github.com/lycheeverse/lychee-action) for external URLs, markdownlint-cli2 for style.

**pre-commit.** Two ways with the [pre-commit framework](https://pre-commit.com/): a `repo: local` hook that calls the script copied into the user's repo, or a `.pre-commit-hooks.yaml` published in the skill's repository so users reference it by URL and tag. The second needs network at hook-install time. Limit the hook to fast checks on changed notes plus notes whose `sources` changed.

**Where the script lives.** A skill is installed in the agent's skill directory, which CI cannot see. For CI, the validator has to be either vendored into the documented repo (for example under `docs/.tools/`) or fetched from the skill's repository at a pinned tag. Vendoring keeps CI offline-capable and pins behaviour, at the cost of a copy to update.

**Agent-side hook.** Claude Code hooks can run the validator after the agent edits files under `docs/` ([hooks docs](https://code.claude.com/docs/en/hooks.md) **(page not read today)**), catching errors before commit.

## Open questions / decisions for the project owner

1. **Baseline runtime.** Python standard library only (recommended), Node built-ins only, or both? If Python, what minimum version? `tomllib` needs 3.11; supporting older interpreters means a fallback for TOML manifests.
2. **Will the skill ever install tools?** Recommended: never by default; only detect and use. Confirm.
3. **Ship the opt-in `uv run` rich tier in v1, or defer it?** It adds symbol-level edges and ranking, plus a network requirement, a lock file to maintain, and a grammar-download step.
4. **Edge granularity.** File/module level only (recommended for v1), or symbol/call level too? Symbol level multiplies notes and needs Tier 2 or better.
5. **Provenance vocabulary.** Two values (`extracted`, `inferred`) plus a `method` field, or a third value such as `ambiguous` or `declared` (stated in a config file rather than in code)?
6. **Where provenance lives.** Suffixed frontmatter keys (`depends_on` / `depends_on_inferred`) plus a sidecar edge file (recommended), a table in the note body, or nested YAML objects despite Obsidian's limited support?
7. **Confidence.** Coarse levels (low/medium/high) or numbers for inferred edges? Or none, with evidence only?
8. **Inverse edges.** Stored on both notes and checked by the validator (Obsidian's graph and backlinks show them either way), or stored once and derived in the graph file?
9. **Frontmatter dialect.** Enforce the strict YAML subset (recommended), which means hand edits outside it are validation errors?
10. **Note identity.** File name as the only identity, or a stable `id` key so renames can be tracked in snapshot diffs?
11. **Unique note names.** Require vault-wide unique base names (simplest wikilinks, matches obsidiantools' assumption) or allow duplicates in different folders with path-style links?
12. **Staleness hash.** Git blob ids (recommended) or raw content hashes; per note only, or per source file as well; and are whitespace-only changes accepted as "stale"?
13. **Canonical graph file.** Committed to the repo (reviewable diffs, snapshot compare without rebuilding, but one more file that can go stale) or always rebuilt from the notes? Where does it live so that Obsidian ignores it?
14. **Graph format.** networkx-style node-link JSON (recommended) or JSON Graph Format?
15. **Body wikilinks.** Do untyped links in prose count as graph edges (`mentions`), or do only typed frontmatter links count?
16. **Severity policy.** Which checks fail CI and which only warn, in particular staleness (V20) and drift (V22)?
17. **Validator distribution for CI.** Vendored into each documented repo, or fetched from the skill repository at a pinned tag? And should the project publish a reusable GitHub Action and a `.pre-commit-hooks.yaml`?
18. **Auto-fix scope.** May `--fix` add missing inverse edges and remove duplicates? Should it ever refresh hashes or promote inferred edges to extracted without an agent re-reading the source?
19. **Non-import dependency coverage in v1.** Which kinds from section 3 are in scope (compose and workspace files, env vars, DB tables, HTTP calls, queues), and is evidence mandatory for every inferred edge?
20. **External dependency notes.** One note per direct dependency, one per ecosystem, or a single table note? Direct dependencies only, or transitive ones from lockfiles too?
21. **Relationship to graphify.** It overlaps substantially (tree-sitter extraction, extracted/inferred tags, `graph.json`, query commands). Differentiate on "Markdown vault is the source of truth, zero install", interoperate with its graph format, or both?
22. **Monorepos and scale.** One vault per repository or per package? At what size do the standard-library graph routines and a single graph file stop being adequate?
23. **Obsidian-only extras.** Should the skill generate `.base` files or Dataview blocks for human readers, given they do nothing outside the app?
24. **Drift baseline.** When the available extractor tier differs between runs (regex locally, a real tool in CI), should drift comparison refuse, downgrade to a warning, or compare only the common subset?
