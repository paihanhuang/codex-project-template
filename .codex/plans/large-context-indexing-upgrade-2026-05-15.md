# Large Context Indexing Upgrade Plan

Date: 2026-05-15
Status: Proposed, not approved for implementation

## Problem Restatement

The current template has a lightweight Phase 0.5 context-indexing step that
asks the orchestrator to scan relevant sources and write markdown summaries
under `.codex/index/`. That works for moderate tasks, but it does not scale
well to very large codebases or archives of documents because every run still
depends on ad hoc scanning, manual summaries, and source-list timestamp checks.

The desired outcome is a project-local context system that lets Codex and
custom agents retrieve precise code and document context quickly, reuse indexes
across turns and agents, avoid repeatedly loading irrelevant files, and keep
the prompt token budget focused on grounded evidence.

## Research Findings

- GitHub Copilot repository indexing uses semantic code search so the agent can
  find relevant code by meaning when exact names are unknown; large initial
  indexing may run in the background, and later re-indexing is much faster.
  Source: https://docs.github.com/en/copilot/concepts/context/repository-indexing
- Sourcegraph Cody combines keyword search, Sourcegraph search, and code graph
  context, which supports the conclusion that no single retrieval path is
  sufficient for codebase work. Source:
  https://sourcegraph.com/docs/cody/core-concepts/context
- Aider uses a concise repository map containing important classes, functions,
  types, and signatures, then ranks the most relevant portions to fit a token
  budget. Source: https://aider.chat/docs/repomap.html
- Anthropic's contextual retrieval results support chunk contextualization,
  BM25 plus embeddings, and reranking as a useful combination, while explicitly
  noting latency and cost tradeoffs. Source:
  https://www.anthropic.com/engineering/contextual-retrieval
- Microsoft GraphRAG shows that document archives with entity and relationship
  questions benefit from structured graph indexes, community summaries, and
  different query modes for local, global, and broad exploratory questions.
  Sources: https://microsoft.github.io/graphrag//index/overview/ and
  https://microsoft.github.io/graphrag/query/overview/
- Tree-sitter is appropriate for code structure extraction because it builds
  concrete syntax trees, supports named-node traversal, and is designed for
  fast incremental parsing. Sources:
  https://tree-sitter.github.io/tree-sitter/using-parsers/2-basic-parsing.html
  and https://github.com/tree-sitter/tree-sitter
- LlamaIndex's ingestion pipeline validates the need for explicit
  transformations, caching, docstore deduplication, persistence, and parallel
  processing rather than one-off ingestion scripts. Source:
  https://developers.llamaindex.ai/python/framework-api-reference/ingestion/
- OpenAI Retrieval documents useful hosted-vector-store patterns such as
  semantic search, attribute filtering, ranking controls, hybrid search
  weighting, async ingestion status, rate limits, and expiration policies.
  Source: https://developers.openai.com/api/docs/guides/retrieval

## Current Template Gaps

- `.codex/docs/workflow-reference.md` only defines manual markdown index files
  with source paths, dates, and summaries.
- `.codex/config.toml` has no context-index settings for source roots,
  exclusion rules, token budgets, backends, embedding provider, stale-index
  policy, or privacy mode.
- There is no manifest with content hashes, Git commit, parser version,
  embedding model, extraction version, or chunk IDs.
- There is no machine-queryable index for lexical search, semantic search,
  symbol lookup, document metadata, or graph relationships.
- There is no common "context capsule" artifact that can be passed verbatim to
  architect, engineer, and QA agents.
- There is no evaluation harness for retrieval recall, answer grounding, token
  savings, latency, or stale-index behavior.
- `verify.sh` and `verify.ps1` are placeholders and will not catch regressions
  in indexing or retrieval behavior.

## Proposed Architecture

Add a project-local context layer with these artifacts:

- `.codex/context.toml`: declarative settings for source roots, document
  archive roots, ignore/include patterns, privacy mode, chunk sizes, token
  budgets, lexical/vector/graph backends, reranking, and stale-index policy.
- `.codex/context/manifest.json`: content-addressed manifest keyed by source
  path, size, mtime, hash, Git HEAD, parser/extractor version, embedding model,
  and index build time.
- `.codex/context/inventory.sqlite`: file inventory, metadata, extracted
  document sections, code symbols, imports, exports, references, and FTS5/BM25
  lexical tables.
- `.codex/context/vectors/`: local vector index by default, with adapters for
  hosted vector stores only when explicitly configured.
- `.codex/context/graph/`: optional graph store or serialized graph for
  code-symbol and document-entity relationships.
- `.codex/context/capsules/`: generated context packs that contain only the
  selected evidence for a task, with source paths, line ranges or document
  anchors, retrieval method, confidence, token estimate, freshness status, and
  explicit gaps.
- `.codex/docs/context-indexing.md`: operator guide and troubleshooting notes.
- `.codex/evals/context/`: small gold datasets and benchmark scripts.

Retrieval should be hybrid and routed by query type:

- exact symbol/path/config lookup: `rg`, SQLite FTS, and symbol table first;
- broad code behavior lookup: repo map plus lexical plus semantic retrieval;
- "where is this used" work: symbol graph/import graph plus source verification;
- document fact lookup: metadata filters plus hybrid BM25/vector retrieval;
- multi-hop archive questions: optional GraphRAG-style entity/relationship
  retrieval, enabled only for archives where graph extraction pays for itself;
- implementation work: retrieved capsule first, then raw file reads for files
  that will be edited.

## Settings Changes To Propose

### AGENTS.md

- Expand Phase 0.5 from "write markdown indexes" to "select or refresh the
  project context index, then generate a context capsule before spawning agents
  or performing large local work."
- Add a rule that agents should receive context capsule paths and only the
  minimum raw files needed for their stage.
- Require any large-codebase answer or implementation to cite the capsule or
  raw file evidence used.
- Keep `project_doc_max_bytes` small; do not solve large-context work by making
  AGENTS.md bigger.

### .codex/config.toml

Add template-scoped defaults without forcing sandbox or approval posture:

```toml
[context_index]
enabled = true
config_file = ".codex/context.toml"
capsule_token_budget = 12000
max_index_age_hours = 24
require_fresh_for_edits = true
prefer_local_indexes = true
```

### .codex/context.toml

Introduce a new project-editable file:

```toml
[sources]
code_roots = ["."]
document_roots = []
exclude = [".git/**", ".codex/context/**", "node_modules/**", "dist/**", "build/**", ".env*", "**/*.key", "**/*.pem"]

[retrieval]
lexical_backend = "sqlite-fts5"
vector_backend = "local"
graph_backend = "off"
rerank = "off"
top_k_initial = 80
top_k_capsule = 20

[chunking.code]
strategy = "tree-sitter-symbols-with-fallback"
max_chunk_tokens = 900
overlap_tokens = 120

[chunking.docs]
strategy = "section-aware"
max_chunk_tokens = 700
overlap_tokens = 100
contextualize_chunks = false

[privacy]
local_only = true
secret_scan = true
hosted_vector_store = "disabled"
```

### Workflow Reference

- Replace the current markdown-only Phase 0.5 process with three paths:
  - small task: direct file reads;
  - medium task: quick inventory and focused markdown index;
  - large task: context index refresh plus capsule generation.
- Add freshness rules based on content hashes and Git HEAD, not only date
  comparison.
- Add "dirty overlay" handling so uncommitted changed files are read directly
  and temporarily override persisted index entries.
- Require capsule reuse across V-Model agents to avoid each agent repeating
  broad scans.

### Prompt Templates

- Add a `Context Capsule` field to architect, engineer, and QA prompts.
- Require agents to flag missing context instead of independently scanning large
  trees when a capsule is present but insufficient.
- For QA prompts, include retrieval-quality checks: missing relevant files,
  stale capsule, unsupported source, and unverifiable evidence.

### Verification

- Replace placeholder `verify.sh` and `verify.ps1` with staged checks once
  tooling exists:
  - manifest schema validation;
  - ignore/secret exclusion tests;
  - hash-based stale detection tests;
  - sample retrieval benchmark;
  - capsule schema validation;
  - cross-platform smoke tests.

## Stage-Based Implementation And Testing Plan

### Stage 0: Requirements, Scope, And Acceptance Metrics

Implementation:

- Define target scale bands: small, medium, large codebase, and document
  archive.
- Choose local-first default backends: SQLite FTS5 for metadata/BM25 and a
  pluggable local vector backend.
- Define privacy constraints, supported document types, maximum archive size,
  and whether hosted embedding/vector services are allowed.
- Create `.codex/docs/context-indexing.md` with the intended operator model.

Tests:

- No runtime tests yet.
- Acceptance is a reviewed requirements document with explicit metrics:
  Recall@10, MRR@10, median retrieval latency, index refresh latency, token
  savings against manual scan baseline, and citation accuracy.

Exit criteria:

- User has approved local-only vs hosted options.
- The project has a retrieval benchmark fixture plan.

### Stage 1: Config, Schemas, And Manual Capsule Format

Implementation:

- Add `.codex/context.toml`.
- Add JSON schemas for manifest and capsule artifacts.
- Add documentation to `AGENTS.md`, `.codex/docs/workflow-reference.md`, and
  `.codex/docs/prompt-templates.md`.
- Add a manually generated sample capsule for this repository.

Tests:

- Schema validation for sample manifest and capsule.
- Documentation lint check for required Phase 0.5 language.
- Verify no approval markers are created by plan-only changes.

Exit criteria:

- Agents can be prompted with a stable context capsule path and know when to
  request more context.

### Stage 2: Inventory, Hashing, Ignore Rules, And Lexical Index

Implementation:

- Build `context-index` commands:
  - `scan`: produce manifest entries with path, hash, mtime, size, language,
    Git status, and ignore reason;
  - `index-lexical`: populate SQLite FTS5 tables for text/code chunks;
  - `status`: report stale, missing, ignored, and dirty-overlay files.
- Respect `.gitignore`, `.codex/context.toml`, and secret exclusion patterns.
- Store generated files under `.codex/context/` and keep bulky indexes ignored
  if needed.

Tests:

- Unit tests for ignore precedence, binary detection, secret exclusion, hashing,
  deleted files, renamed files, symlinks, and dirty worktree overlays.
- Smoke test against this template.
- Regression test that `.env`, private keys, build outputs, and `.git` content
  are not indexed.

Exit criteria:

- Lexical search answers exact filename, symbol-like, config-key, and phrase
  queries without scanning the whole tree.

### Stage 3: Code Structure Index And Repository Map

Implementation:

- Add Tree-sitter-based code parsing for common languages with a fallback
  regex/ctags-style extractor for unsupported languages.
- Extract symbols, definitions, imports, exports, class/function signatures,
  docstrings, and test-file relationships.
- Build a compact repo map with graph ranking and a configurable token budget.
- Store symbol graph edges in SQLite first; defer external graph DB until needed.

Tests:

- Parser fixtures for each supported language.
- Fallback behavior for unsupported or syntactically invalid files.
- Ranking tests that files importing or referencing a target symbol are ranked
  above unrelated files.
- Token-budget tests for repo-map output.

Exit criteria:

- A code task can generate a capsule containing relevant symbols and candidate
  files before raw file reads.

### Stage 4: Document Archive Ingestion

Implementation:

- Add loaders for markdown, text, HTML, PDF text, and Office documents where
  dependencies are acceptable.
- Extract document metadata: title, source path, created/modified dates,
  headings, section anchors, page numbers when available, and checksums.
- Use section-aware chunking with parent-child relationships.
- Mark OCR/scanned PDF support as optional, with explicit dependency and quality
  warnings.

Tests:

- Fixtures for markdown, HTML, PDF text, docx, large files, duplicate docs,
  empty docs, malformed docs, and non-UTF encodings.
- Parent-child retrieval test: child chunk match returns a useful parent
  section anchor.
- Duplicate and stale-document tests.

Exit criteria:

- Document facts can be retrieved with source anchors and without loading whole
  archives into the prompt.

### Stage 5: Semantic And Hybrid Retrieval

Implementation:

- Add a pluggable embedding interface.
- Default to local-only embeddings when configured; require explicit
  configuration for hosted embeddings or hosted vector stores.
- Add vector search over code/doc chunks.
- Add hybrid fusion across BM25/FTS and vector results.
- Add optional reranking with strict latency and cost budgets.
- Add contextualized chunks only as an opt-in mode after baseline evaluation.

Tests:

- Golden-query retrieval benchmark across exact, semantic, architecture,
  document-fact, and multi-hop query classes.
- Compare BM25-only, vector-only, hybrid, and hybrid-plus-rerank.
- Measure Recall@10, MRR@10, median and p95 latency, generated capsule token
  count, and cost where hosted services are enabled.
- Failure tests for missing embedding provider, model changes, index version
  changes, and partial vector index corruption.

Exit criteria:

- Hybrid retrieval improves target benchmark quality enough to justify added
  dependencies and latency, otherwise the stage remains optional.

### Stage 6: Context Capsule Generation And Workflow Integration

Implementation:

- Add `context-query` command to produce capsules:
  - query text;
  - selected retrieval routes;
  - ranked evidence;
  - source anchors;
  - freshness status;
  - token estimate;
  - missing-context warnings;
  - suggested raw files to read next.
- Update Phase 0.5 to require capsule generation for large tasks.
- Update V-Model prompts so architect, engineer, and QA agents share the same
  capsule path.
- Add a rule that implementation must read raw files before editing even when a
  capsule identifies candidate files.

Tests:

- Capsule schema tests.
- Token budget enforcement tests.
- Stale capsule rejection tests for edit tasks.
- Agent-prompt snapshot tests to ensure capsules are referenced without dumping
  unnecessary full indexes into prompts.

Exit criteria:

- A large-codebase task can move from user request to agent-ready context with
  predictable token usage and source grounding.

### Stage 7: Optional Graph Retrieval For Multi-Hop Archives

Implementation:

- Add graph extraction only for repositories or archives that need multi-hop
  questions.
- For code, keep symbol/import/reference graph as the first graph layer.
- For documents, optionally extract entities, claims, relationships, and
  community summaries.
- Add local/global query modes only after benchmarks show ordinary hybrid
  retrieval misses valid multi-hop answers.

Tests:

- Multi-hop QA fixture where facts span multiple documents or code modules.
- Entity normalization and alias tests.
- Graph extraction cost and latency budget tests.
- Regression tests showing graph retrieval does not replace direct source
  citation.

Exit criteria:

- Graph mode is justified by measured benchmark gains, not enabled by default.

### Stage 8: Hardening, CI, And Operational Documentation

Implementation:

- Wire the smallest meaningful context tests into `verify.sh` and `verify.ps1`.
- Add a slower benchmark command for periodic review.
- Add repair commands for corrupt indexes.
- Add docs for rebuilding indexes, rotating embedding models, excluding private
  paths, and troubleshooting stale or low-quality retrieval.

Tests:

- Cross-platform smoke tests.
- Corruption recovery test.
- Large-fixture performance test with recorded thresholds.
- Privacy audit test for ignored files and secret-like content.

Exit criteria:

- Indexing failures are visible and actionable.
- Slow or optional tests are separated from routine verification.

## Cross-Critique Concerns Addressed

- Architect concern: avoid overbuilding a graph database too early. Resolution:
  start with manifest, SQLite FTS, code structure, and capsules; make graph mode
  optional and benchmark-gated.
- Architect concern: keep the template portable. Resolution: local-first
  defaults, pluggable backends, and no project-local sandbox or approval
  overrides.
- Engineer concern: vector search alone will miss exact identifiers, error
  strings, config keys, and APIs. Resolution: lexical/BM25 and symbol lookup are
  first-class retrieval paths.
- Engineer concern: indexes can become stale and cause bad edits. Resolution:
  content hashes, Git HEAD, dirty-overlay handling, freshness reports, and raw
  file reads before edits.
- Engineer concern: dependency sprawl. Resolution: stage dependencies by value;
  SQLite FTS and manifest first, Tree-sitter second, embeddings third, graph last.
- QA robustness concern: private files and secrets might be indexed. Resolution:
  default excludes, secret scan, local-only mode, and tests proving `.env`,
  private keys, `.git`, build artifacts, and generated indexes are excluded.
- QA robustness concern: malformed or unsupported docs may silently produce poor
  chunks. Resolution: extraction status per file, warnings in capsules, fixture
  tests for malformed/empty/non-UTF/scanned files.
- QA robustness concern: agents may trust summaries without evidence. Resolution:
  capsules must include source anchors and gaps; implementation still reads raw
  files before editing.
- QA quality concern: reranking and graph extraction can add latency and cost.
  Resolution: rerank and graph modes are opt-in, budgeted, and benchmark-gated.
- QA quality concern: token savings must be measured, not assumed. Resolution:
  baseline manual-scan comparison and token-count telemetry are required in the
  eval harness.

## Recommended Rollout

Implement Stages 1 through 3 first. They provide the largest token and speed
benefit for codebases without introducing hosted services or expensive graph
extraction. Add document ingestion in Stage 4 when there is a concrete archive
fixture. Add semantic/hybrid retrieval in Stage 5 only after lexical and symbol
baselines are measured. Treat GraphRAG-style indexing as a later specialized
capability for multi-hop document archives, not as the default.

## Approval Needed Before Implementation

- Confirm whether the default must be fully local-only.
- Confirm preferred implementation language for tools, likely Python for
  portability and SQLite/Tree-sitter ecosystem support.
- Confirm which document types matter first.
- Confirm whether bulky generated indexes should be git-ignored, while schemas,
  docs, and small fixtures remain tracked.
