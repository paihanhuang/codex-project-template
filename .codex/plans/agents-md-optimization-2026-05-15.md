# AGENTS.md Optimization Plan

Date: 2026-05-15
Status: Implemented on 2026-05-15

## Problem Restatement

The current `AGENTS.md` is 136 lines and about 6 KB. It is below the configured
`project_doc_max_bytes = 65536`, so it is not at immediate truncation risk.
However, Codex reads `AGENTS.md` before doing any work, so every line competes
with the user's prompt, tool output, and repository context. The file should be
an always-loaded operating index, not a full workflow manual.

OpenAI's Codex guidance says `AGENTS.md` is layered from global to project to
current directory, and Codex stops adding project instructions once the combined
size reaches `project_doc_max_bytes`. OpenAI's best-practices guidance also
emphasizes giving Codex clear expectations for tests, checks, behavior, and
review. This plan keeps those high-frequency rules in `AGENTS.md` and moves
detailed workflow material into on-demand docs or skills.

References:

- https://developers.openai.com/codex/guides/agents-md
- https://developers.openai.com/codex/learn/best-practices
- https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide

## Goals

- Reduce `AGENTS.md` from about 136 lines to roughly 70-90 lines.
- Keep critical behavior available at session start.
- Make the four engineering principles explicit:
  - clarify assumptions;
  - prefer simple code;
  - make surgical edits;
  - define verifiable goals.
- Make `AGENTS.md` a pointer to detailed docs, skills, and command rules.
- Preserve V-Model routing, approval gate, memory contract, context indexing,
  and verification requirements.

## Non-Goals

- Do not change custom agent behavior or `.codex/agents/*.toml`.
- Do not change sandbox, approval, or user-level config behavior.
- Do not remove the V-Model workflow.
- Do not move active workflow state such as `.codex/plans/current.md`.
- Do not add long prose copied from OpenAI docs or external repos.

## Proposed New Structure

```markdown
# Codex V-Model Project Template

## Startup Rules
## Engineering Discipline
## Workflow Routing
## Orchestrator And Agents
## Phase 0: Clarity Gate
## Phase 0.5: Context Indexing
## Approval And Plans
## Session Continuity
## Verification
```

## Content Changes

### Keep In AGENTS.md

- One-sentence project identity.
- Pointers to:
  - `.codex/docs/workflow-reference.md`;
  - `.codex/docs/prompt-templates.md`;
  - `.codex/docs/context-indexing.md`;
  - `.agents/skills/context-indexing/SKILL.md`.
- Operating-mode routing for V-Model vs direct local work.
- Engineering discipline rules.
- Orchestrator role.
- Agent memory block requirement.
- Dual QA verdict gate.
- Phase 0 clarity gate.
- Phase 0.5 context-indexing trigger.
- Approval markers and gate protection.
- Session-state recovery pointer.
- Verification command expectation.

### Move Or Shorten

- Historical Claude-template explanation:
  - keep only one short line in `AGENTS.md`;
  - leave details in `.codex/docs/codex-mapping.md`.
- Full agent table:
  - replace with "custom agents live in `.codex/agents/*.toml`";
  - optionally keep the five names in one compact sentence.
- Long approval/hook explanation:
  - keep only the gate contract and pointer to `.codex/rules/*.rules`;
  - leave hook details in `.codex/hooks/README.md`.
- Full timeout Bash snippet:
  - move to `.codex/docs/workflow-reference.md`;
  - `AGENTS.md` should say "use `./verify.sh` or `./verify.ps1`; for long checks use the timeout pattern in workflow reference."
- Session continuity procedure:
  - keep the three recovery files and session-state requirement;
  - avoid detailed compaction prose.
- Context indexing prose:
  - keep trigger and raw-read-before-edit rule;
  - rely on the repo-local skill and `.codex/docs/context-indexing.md` for commands.

## Stage-Based Implementation Plan

### Stage 0: Baseline And Safety Snapshot

Implementation:

- Record current `AGENTS.md` line and byte counts.
- Confirm `./verify.sh` passes before changing instructions.
- Confirm no uncommitted user changes are present outside the intended files.

Testing:

- `wc -l -c AGENTS.md`
- `./verify.sh`
- `git status --short`

Exit criteria:

- Baseline numbers are known.
- Verification passes before edits.

### Stage 1: Draft Shorter AGENTS.md

Implementation:

- Rewrite `AGENTS.md` to the proposed structure.
- Add the Engineering Discipline section with the four principles.
- Preserve V-Model authorization conditions and direct-work path.
- Preserve memory entry, dual QA gate, approval marker, and session-state rules.
- Add concise pointers to detailed docs and `context-indexing` skill.
- Remove the long timeout snippet and historical explanation.

Testing:

- Manual compare against the current `AGENTS.md` checklist:
  - V-Model trigger preserved;
  - Phase 0 preserved;
  - Phase 0.5 preserved;
  - plan archival preserved;
  - approval gate preserved;
  - agent memory contract preserved;
  - dual QA gate preserved;
  - verification preserved.

Exit criteria:

- `AGENTS.md` is materially shorter and still contains all critical routing and
  gate rules.

### Stage 2: Move Detailed Text To Existing Docs

Implementation:

- Ensure `.codex/docs/workflow-reference.md` contains the long timeout pattern
  or a clear verification reference.
- Ensure `.codex/docs/codex-mapping.md` contains the Claude-to-Codex historical
  context, so removing it from `AGENTS.md` does not lose provenance.
- Ensure `.codex/docs/context-indexing.md` contains the context-indexing command
  details already used by the skill.
- Avoid creating new docs unless an existing doc cannot reasonably own the
  moved content.

Testing:

- `rg` checks for the moved concepts:
  - `timeout pattern`;
  - `Claude to Codex`;
  - `context_index.py`;
  - `context-indexing`.

Exit criteria:

- Removed startup details remain discoverable in on-demand docs.

### Stage 3: Add Instruction Drift Validation

Implementation:

- Extend `.codex/tools/validate-context-artifacts.py`, or split a small
  `.codex/tools/validate-project-instructions.py`, to check `AGENTS.md` for
  critical phrases or sections.
- Validate structure, not exact prose. Required concepts:
  - `Engineering Discipline`;
  - clarify assumptions;
  - simple code;
  - surgical edits;
  - verifiable goals or verification;
  - V-Model authorization;
  - Phase 0 clarity gate;
  - context-indexing skill;
  - `.codex/plans/.approved`;
  - `## Memory Entry`;
  - dual QA gate.

Testing:

- `python3 .codex/tools/validate-context-artifacts.py`
- `./verify.sh`

Exit criteria:

- Future edits cannot accidentally remove critical startup rules without
  failing verification.

### Stage 4: Smoke Test Instruction Load

Implementation:

- Run a non-mutating Codex instruction-summary smoke test if practical:

```bash
codex exec --ask-for-approval never "Summarize the current project instructions in 8 bullets."
```

- If this is too slow or unsuitable for routine verification, keep it as a
  manual release check rather than wiring it into `verify.sh`.

Testing:

- Inspect the summary for:
  - V-Model routing;
  - clarity gate;
  - engineering discipline;
  - context-indexing skill;
  - approval gate;
  - verification.

Exit criteria:

- Codex can accurately summarize the shortened `AGENTS.md`.

### Stage 5: Final Verification And Index Refresh

Implementation:

- Run full local verification.
- Refresh the context index after instruction/doc changes:

```bash
python3 .codex/tools/context_index.py --root . index-lexical
python3 .codex/tools/context_index.py --root . status
```

- Update `.codex/plans/session-state.md`.

Testing:

- `./verify.sh`
- `python3 .codex/tools/context_index.py --root . status`
- `git diff --stat`

Exit criteria:

- Verification passes.
- Context index reports fresh.
- Diff is scoped to instruction/docs/validator/session-state files.

## Cross-Critique Concerns Addressed

- Architect concern: over-compressing `AGENTS.md` could hide important workflow
  contracts. Resolution: validate critical concepts and keep detailed docs
  linked.
- Architect concern: splitting instructions can make them harder to find.
  Resolution: keep `AGENTS.md` as an index with explicit paths.
- Engineer concern: phrase-based validation can be brittle. Resolution:
  validate section/concept presence, not exact paragraphs.
- Engineer concern: moving timeout or hook details may break operational use.
  Resolution: move only to existing docs and verify with `rg`.
- QA robustness concern: losing approval gate or dual QA gate would weaken the
  V-Model. Resolution: both gates are required validation concepts.
- QA robustness concern: abbreviated session continuity could break resume.
  Resolution: preserve the three recovery files and session-state rule.
- QA quality concern: startup instructions still may be too long if global
  instructions are also large. Resolution: target 3-4 KB for project
  `AGENTS.md`, below both default and configured caps.
- QA quality concern: adding a Codex smoke test to routine verification may be
  slow or flaky. Resolution: keep it manual unless it proves stable.

## Acceptance Criteria

- `AGENTS.md` is reduced to roughly 70-90 lines.
- `AGENTS.md` contains the four engineering principles explicitly.
- `AGENTS.md` preserves V-Model routing, approval, memory, QA, context indexing,
  session continuity, and verification rules.
- Detailed material removed from startup instructions remains available in
  `.codex/docs/` or repo skills.
- `./verify.sh` passes.
- The context index is refreshed and reports fresh.

## Recommended Approval

Approve Stages 0-3 and 5 for implementation. Treat Stage 4 as an optional manual
smoke check unless the user specifically wants it automated.

## Implementation Results

- `AGENTS.md` was reduced from 136 lines / 6006 bytes to 100 lines / 4368
  bytes. It is slightly above the original 70-90 line target but below the
  enforced 100-line validation ceiling.
- The four engineering principles are now explicit in startup instructions.
- Historical mapping and timeout details were moved or pointed to on-demand
  docs.
- `validate-context-artifacts.py` now checks that `AGENTS.md` keeps critical
  workflow, approval, context-indexing, QA, memory, and verification concepts.
- `./verify.sh` passes.
- The context index was refreshed and reported fresh.

## Before/After Comparison

Comparison task:

```text
Implement a --paths-only flag for the context_index.py query subcommand, add
tests, run ./verify.sh, and leave the tree uncommitted.
```

Controlled setup:

- `before`: last committed setup with the 136-line `AGENTS.md`.
- `after`: revised setup with the 100-line `AGENTS.md`.
- Both ran in isolated temp copies with the same prompt and same nested Codex
  sandbox posture.

Observed results:

| Metric | Before | After |
|---|---:|---:|
| Exit status | completed | completed |
| Files changed | 2 | 2 |
| Diff size | 67 insertions | 58 insertions |
| Tests | passed | passed |
| Nested exec commands | 19 | 22 |
| Nested tokens reported | 37,386 | 73,789 |

Quality notes:

- Both solutions were scoped to the requested tool and test files.
- Both preserved default query output and added `--paths-only`.
- The revised setup gave a clearer final report: "only those two files modified."
- The revised setup explicitly used the small-task path and raw source reads.
- The revised setup caught a useful edge case: one file with many matching chunks
  should not crowd out other matching files.
- The revised setup also made a debatable assumption: `--paths-only` ignores
  `--limit`, while the before solution applies `--limit` to unique paths. The
  original prompt did not specify limit semantics.

Conclusion:

The revised `AGENTS.md` improved process clarity and scope reporting, but this
single coding sample does not prove uniformly better implementation quality. The
best next improvement is to add a prompt-template or AGENTS rule that ambiguous
CLI option interactions, such as `--paths-only` plus `--limit`, should be named
explicitly before choosing behavior.
