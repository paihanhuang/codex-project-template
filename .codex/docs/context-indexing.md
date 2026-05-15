# Context Indexing

This template uses a staged, local-first context system for large codebases and
document archives. The goal is to keep agent prompts grounded and compact
without hiding source evidence.

## Operating Model

Use the smallest context path that fits the task:

- Small tasks: read the 1-3 known files directly.
- Medium tasks: create or refresh focused markdown indexes under `.codex/index/`.
- Large tasks: refresh the context index and generate a context capsule under
  `.codex/context/capsules/` before spawning agents or doing broad local work.

Context capsules are task-specific. They should include selected evidence,
source paths, anchors, freshness status, token estimates, retrieval layers, and
gaps. Capsules do not replace raw file reads before edits.

## Default Stack

- Configuration: `.codex/context.toml`
- Manifest schema: `.codex/context/schemas/manifest.schema.json`
- Capsule schema: `.codex/context/schemas/capsule.schema.json`
- Generated manifest: `.codex/context/manifest.json`
- Generated lexical index: `.codex/context/inventory.sqlite`
- Generated vectors: `.codex/context/vectors/`
- Generated graph data: `.codex/context/graph/`

The Stage 1 default is local-only. Lexical/BM25 indexing is the first backend.
Semantic, rerank, and graph layers stay disabled until later stages add tooling
and benchmark gates.

## Privacy Defaults

The default excludes `.git`, generated context indexes, worktrees, build
outputs, dependency folders, environment files, and private-key-like files.
Hosted vector stores and external embedding services are disabled unless a
project deliberately changes `.codex/context.toml`.

## Agent Usage

When a capsule exists, pass the capsule path to architect, engineer, and QA
agents. Do not paste bulky indexes into prompts. If an agent finds the capsule
insufficient, it should identify the missing context instead of independently
scanning a large tree.

For implementation stages, the engineer must read the raw source files it will
edit even when a capsule identifies the relevant files.

The repo-local `context-indexing` skill at
`.agents/skills/context-indexing/SKILL.md` provides the short operational
runbook for using these commands during a Codex task.

## Stage 2 Commands

The local inventory and lexical backend is implemented by
`.codex/tools/context_index.py`.

Create or refresh the manifest only:

```bash
python3 .codex/tools/context_index.py --root . scan
```

Create or refresh the manifest and SQLite FTS5 lexical index:

```bash
python3 .codex/tools/context_index.py --root . index-lexical
```

Check whether the manifest matches current files:

```bash
python3 .codex/tools/context_index.py --root . status
```

Query the lexical index:

```bash
python3 .codex/tools/context_index.py --root . query "context capsule" --limit 5
```

Generated `manifest.json`, `inventory.sqlite`, bytecode caches, vectors, graph
data, and generated capsules are ignored by Git. Config, schemas, docs, tests,
and hand-authored sample capsules are tracked.
