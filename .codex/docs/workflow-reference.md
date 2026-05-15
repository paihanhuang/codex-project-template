# Workflow Reference

Detailed step-by-step instructions for each phase of the V-Model workflow.

For standardized custom agent prompts, see
[prompt-templates.md](prompt-templates.md).

## Phase 0.5: Context Indexing

Before spawning agents, determine whether the task involves scanning a large
codebase or many input documents. Use the smallest context path that gives
reliable evidence without wasting tokens.

Context paths:

- Small: read the 1-3 known files directly.
- Medium: scan focused sources and write markdown indexes under `.codex/index/`.
- Large: use `.codex/context.toml` settings to refresh or reuse the project
  context index, then generate a task-specific context capsule under
  `.codex/context/capsules/`.

When to use the large context path:

- The task references more than about 10 files or multiple modules.
- The task references a large archive of documents, specs, requirements, RFCs,
  PDFs, or exported knowledge bases.
- The codebase or archive is unfamiliar and broad discovery would otherwise be
  repeated by multiple agents.
- The user asks for efficient querying, reusable indexes, or token reduction.

When to skip:

- The task is scoped to 1-3 known files.
- The needed evidence is already present in the current conversation.
- A current capsule or markdown index exists and its sources have not changed.

Medium process:

1. Identify the relevant scope.
2. Scan source files and documents.
3. Write structured index files to `.codex/index/`.
4. Use one file per logical area, such as `auth-module.md` or `api-endpoints.md`.

Index file format:

```markdown
---
source: [file/path/a.py, file/path/b.py, docs/spec.md]
indexed: {ISO date}
scope: {what area/module this covers}
---

{Structured summary: key interfaces, public APIs, data flow, dependencies,
constraints. Include only information agents need to make decisions.}
```

Large process:

1. Read `.codex/context.toml` and identify relevant code/document roots.
2. Check existing manifest and capsule artifacts under `.codex/context/`.
3. If tooling exists for the project, refresh stale inventory, lexical, symbol,
   document, vector, or graph indexes according to the configured backends.
4. If tooling does not exist yet, create a manual capsule matching
   `.codex/context/schemas/capsule.schema.json` and clearly mark freshness as
   `manual` or `unknown`.
5. Pass capsule paths to downstream agents instead of pasting bulky indexes.
6. Include only the minimum raw file contents needed for the current stage.
7. For implementation, read raw files before editing even when the capsule
   identifies likely files.

Capsule requirements:

- task query and intent;
- source paths and anchors;
- retrieval layers used, such as `manual`, `path`, `lexical`, `metadata`,
  `symbol`, `semantic`, `graph`, or `rerank`;
- freshness status;
- token budget or token estimate;
- gaps, conflicts, or extraction warnings;
- suggested raw files to read next.

Staleness protocol: markdown indexes compare `indexed` dates against source
modification times. Context manifests and capsules should use content hashes,
Git HEAD, extractor version, and dirty-worktree overlays when tooling is
available. If any source is newer, dirty, missing, or has an unknown freshness
state for edit work, re-scan or read the raw source directly before proceeding.

## Phase 0.6: Research (Optional)

Spawn the `research` custom agent to gather external knowledge before design
begins. This phase is optional. Skip when no external information is needed.

When to research:

- The task involves choosing between technologies, libraries, or patterns.
- Implementation requires an external API, specification, or protocol.
- The user references a technology or pattern the codebase has not used before.
- An agent memory entry surfaced an unknown requiring web research.

When to skip:

- The task touches <=3 known files and all referenced external APIs already
  appear in codebase imports.
- The task is a refactor, bug fix in existing logic, formatting, naming, or
  documentation change.
- The user supplied the external information directly.

Process:

1. Check `.codex/research/INDEX.md`.
2. If a relevant `current` entry exists and is not stale, reuse it.
3. If a relevant entry is stale, spawn research with `existing_research`.
4. If no entry exists, spawn research for the topic.
5. Announce before spawning: `Researching <topic>...`.
6. Run research sequentially only. Do not spawn two research agents in parallel
   because concurrent writes can corrupt `INDEX.md`.
7. Validate the output:
   - `## Memory Entry` exists.
   - `sources[].url` is a subset of `fetched_urls[]`.
   - `INDEX.md` was updated with the new `current` entry.
   - `files_written` lists only paths under `.codex/research/`.
   - contradictions or caveats that challenge user assumptions are escalated to
     the user before Phase 1.
8. Announce completion: `Research complete -- <N> sources, confidence=<level>`.
9. Persist the memory entry under `.codex/agent-memory/research/`.
10. Pass research paths and quoted `## TL;DR` sections to downstream agents.

Staleness protocol:

| Stability | Max Age | Action when stale |
|-----------|---------|-------------------|
| `stable` | Never expires | Reuse indefinitely. If older than 180 days, re-evaluate classification next time. |
| `evolving` | 30 days | Spawn research for refresh. |
| `volatile` | 7 days | Spawn research for refresh. |

If unsure, default to `evolving`.

Partial failure recovery:

- Research file exists but INDEX has no entry: re-invoke research with
  `existing_research` pointing to the orphan and instruct it to update INDEX
  only.
- INDEX entry exists but research file does not: flag corrupt state to the user.

## Review Flow

Use for infrastructure reviews, setup audits, and configuration critique. This
is lighter than the full Phase 1 pipeline.

When to use:

- User asks to evaluate, audit, or revise hooks, agents, settings, or workflow
  config.
- User asks for second opinions on infrastructure changes.
- Any "what should change?" request about this template.

Process:

1. Orchestrator scans relevant files and produces an initial assessment with
   findings by severity.
2. Spawn `engineer` and `qa-robustness` in parallel, if agent use is authorized.
   Do not spawn `qa-quality` for infrastructure reviews.
3. Pass the orchestrator analysis verbatim.
4. Verify each response includes `## Memory Entry` and persist entries.
5. Synthesize agreement, disagreement, missed findings, and prioritized
   recommendations.
6. Present to the user. Approved implementation follows normal workflow or a
   direct edit for trivial changes.

## Phase 1: Design

Step 1: Architect designs.

- Spawn `architect` with the user request and relevant context or indexes.
- Prompt must specify design mode.
- If research was conducted, include file paths and quoted `## TL;DR` sections.
- Verify `## Memory Entry` exists.
- If the architect identifies a research gap, run Phase 0.6 before proceeding.
- Persist the memory entry.

Step 2: Cross-critique.

- Spawn `engineer`, `qa-robustness`, and `qa-quality` in parallel.
- Prompt must specify review mode.
- Pass the architect design verbatim.
- Verify every response includes `## Memory Entry`.
- Persist memory entries.

Step 3: Orchestrator synthesizes.

Produce a Final Proposal containing:

- Problem Restatement
- Assumptions and Constraints
- Architecture Design
- Technical Stack and rationale
- Stage-Based Implementation Plan
- QA Plan with robustness and quality criteria
- Rationale behind key design decisions
- Addressed Critiques

Step 4: User approval gate.

- Archive any existing `.codex/plans/current.md`.
- Write the new proposal to `.codex/plans/current.md`.
- Present the proposal to the user.
- Wait for explicit approval.
- On approval, create `.codex/plans/.approved`.

## Phase 2 & 3: Stage-Based Implementation and Verification

Prerequisite: `.codex/plans/.approved` exists.

Execute each approved stage sequentially. Do not begin stage N+1 until stage N
passes verification.

For each stage:

1. Engineer implements the stage.
   - Pass `.codex/plans/current.md` verbatim.
   - Specify current stage number and scope.
   - Provide relevant code context or indexes.
   - Prompt must specify implementation mode.
2. Orchestrator reviews the stage.
   - Verify `## Memory Entry`.
   - Persist memory.
   - Review implementation against approved stage scope.
   - Re-spawn or redirect engineer if non-compliant.
3. Dual QA verification.
   - Spawn `qa-robustness` and `qa-quality` in parallel.
   - Pass the approved plan, stage acceptance criteria, and implementation diff.
   - Confirm both outputs arrive.
4. Process stage results.
   - Verify `## Memory Entry` blocks.
   - Persist memory entries.
   - Both QA agents must emit `pass`.
   - If either fails, engineer fixes identified issues, then both QA agents
     re-verify.
   - Route `[out-of-scope]` findings to the appropriate memory directory.
5. Refresh stale context indexes before the next stage.

After all stages pass, remove `.codex/plans/.approved` and `.codex/plans/.stage`.

## Verification Timeout Pattern

For longer Bash checks, use the OS-agnostic timeout pattern:

```bash
TIMEOUT_CMD=$(command -v timeout 2>/dev/null || command -v gtimeout 2>/dev/null || echo "")
VERIFY_TIMEOUT="${VERIFY_TIMEOUT:-30}"
if [[ -n "$TIMEOUT_CMD" ]]; then
  "$TIMEOUT_CMD" "$VERIFY_TIMEOUT" ./verify.sh
else
  ./verify.sh
fi
```
