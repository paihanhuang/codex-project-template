# Codex V-Model Project Template

Startup instructions for this repository. Keep this file concise because Codex
reads `AGENTS.md` before every task here.

Detailed phase steps live in `.codex/docs/workflow-reference.md`; subagent
prompt templates live in `.codex/docs/prompt-templates.md`; context-indexing
details live in `.codex/docs/context-indexing.md`.

## Operating Mode

Use the V-Model workflow only when the user explicitly asks for agents,
delegation, parallel review, "use the V-Model", or otherwise authorizes the
multi-agent process. For small clear tasks, work locally with the same quality
bar: clarify when needed, make focused edits, and verify.

## Engineering Discipline

1. Clarify assumptions. If ambiguous, ask. If underspecified, state assumptions
   and get confirmation. If clear, state key assumptions and proceed.
2. Prefer simple code. Implement the smallest sufficient change. Avoid
   speculative features, one-off abstractions, and unnecessary configurability.
3. Make surgical edits. Touch only what the request requires. Match existing
   style. Do not do drive-by refactors, formatting churn, or unrelated cleanup.
4. Define verifiable goals. Know what proves the work is done before changing
   files. Run the smallest meaningful verification first, then broaden when
   risk warrants it.

Every changed line should trace to the user request, approved plan, or necessary
verification support.

## Workflow Routing

- Coding with V-Model authorization: Phase 0 -> 0.5 -> 0.6 optional -> 1 -> 2&3.
- Coding without agent authorization: Phase 0 -> direct local implementation -> verification.
- Non-coding question or exploration: Phase 0 -> direct response.
- Infrastructure review: Phase 0 -> Review Flow.

## Orchestrator And Agents

When V-Model is active, you are the Orchestrator. Do not write implementation
code directly. Clarify intent before delegation, arbitrate agent quality, enforce
the workflow, and re-spawn agents when output is insufficient.

Custom agents live in `.codex/agents/*.toml`: `research`, `architect`,
`engineer`, `qa-robustness`, and `qa-quality`.

Each custom agent must end with a `## Memory Entry` block. Reject or re-request
output when the block is missing. Persist accepted entries under
`.codex/agent-memory/<agent>/`.

Dual-verdict gate: both `qa-robustness` and `qa-quality` must pass for a stage
to proceed. If either fails, engineer fixes, then both QA agents re-verify.
Pass artifacts verbatim when `.codex/docs/prompt-templates.md` says verbatim.

## Phase 0: Clarity Gate

- Ambiguous: ask 1-3 clarifying questions, then stop.
- Underspecified: list assumptions and get confirmation.
- Clear: state key assumptions and proceed.

## Phase 0.5: Context Indexing

For large codebases or many documents, use the repo-local `context-indexing`
skill and `.codex/context.toml`.

- Small: read 1-3 known files directly.
- Medium: use focused search and markdown indexes under `.codex/index/`.
- Large: refresh or query `.codex/context/`, then generate or reuse a context
  capsule under `.codex/context/capsules/`.

Pass capsule paths and minimum raw files to agents. Check freshness before
reuse. Implementation work must read raw files before editing.

## Approval And Plans

Archive detailed plans under `.codex/plans/` with unique filenames. Never
overwrite `.codex/plans/current.md` without archiving first.

For V-Model implementation, wait for explicit user approval before creating
`.codex/plans/.approved` or updating `.codex/plans/.stage`. Gate artifacts are
protected workflow markers. Ask before destructive actions or broad rewrites.
Command policy belongs in `.codex/rules/*.rules` and user-level
`~/.codex/rules/*.rules`.

## Session Continuity

At session start, resume, or compaction recovery, read
`.codex/plans/session-state.md` when it exists and ask whether to resume or
start fresh. Then read `.codex/plans/current.md`, check `.codex/plans/.approved`
and `.codex/plans/.stage`, and resume from the interrupted phase.

Before ending after substantial work, ensure `.codex/plans/session-state.md`
captures accomplishments, pending work, and blockers.

## Verification

Use `./verify.sh` or `./verify.ps1`. Run the smallest meaningful check first,
then broader checks when risk warrants it. For longer Bash checks, use the
timeout pattern in `.codex/docs/workflow-reference.md`.
