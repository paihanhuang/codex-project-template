---
name: context-indexing
description: Use when a task needs to query, reference, summarize, navigate, or work across a large codebase or document archive; when the user asks to save tokens or avoid re-scanning; or when .codex/tools/context_index.py, .codex/context.toml, context capsules, manifests, lexical indexes, or retrieval freshness are relevant.
---

# Context Indexing

Use this skill to decide how much local context machinery a task needs.

## Context Path

- Small task: if the task is scoped to 1-3 known files, read those raw files directly.
- Medium task: use focused `rg` searches and, when useful, markdown summaries under `.codex/index/`.
- Large task: check the context index, refresh it if stale or missing, query it, then use or create a context capsule under `.codex/context/capsules/`.

## Commands

Check freshness before relying on indexed context:

```bash
python3 .codex/tools/context_index.py --root . status
```

Refresh the local manifest and SQLite FTS5 lexical index:

```bash
python3 .codex/tools/context_index.py --root . index-lexical
```

Query the lexical index:

```bash
python3 .codex/tools/context_index.py --root . query "<query>" --limit 10
```

## Rules

- Treat index query results and capsules as selection aids, not source truth.
- Before implementation edits, read the raw files that will be changed.
- If `status` reports stale, missing, or unknown context, refresh the index or report the gap before relying on results.
- Before indexing new roots or archives, check `.codex/context.toml` privacy rules and excludes.
- For large multi-agent work, pass capsule paths to agents instead of pasting bulky indexes.
- If a capsule is insufficient, name the missing context rather than scanning the entire tree by default.

## References

- Detailed workflow: `.codex/docs/context-indexing.md`
- Context settings: `.codex/context.toml`
- Capsule schema: `.codex/context/schemas/capsule.schema.json`
- Manifest schema: `.codex/context/schemas/manifest.schema.json`
