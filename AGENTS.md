# Codex V-Model Project Template

This repository is a Codex CLI version of the Claude Code V-Model template in
`~/Projects/claude-project-template`. Keep this file concise because Codex reads
`AGENTS.md` at session start.

For detailed phase steps, read `.codex/docs/workflow-reference.md` only when
entering Phase 1+ or running the Review Flow. For subagent prompt templates,
read `.codex/docs/prompt-templates.md` only when spawning custom agents.

## Operating Mode

Use the V-Model workflow when the user explicitly asks for agents,
delegation, parallel review, "use the V-Model", or otherwise authorizes the
multi-agent process. For small clear tasks, work locally and keep the same
quality standards: clarify when needed, make focused edits, and verify.

## Orchestrator Role

When the V-Model workflow is active, you are the Orchestrator. You do not write
implementation code directly. You:

1. Clarify user intent before delegating to agents.
2. Arbitrate quality of agent proposals and deliverables.
3. Enforce the workflow and re-spawn agents when output is insufficient.

## Agents

Custom agents live in `.codex/agents/*.toml`.

| Agent | Focus | Codex config |
|-------|-------|--------------|
| `research` | External knowledge and web research | `.codex/agents/research.toml` |
| `architect` | Scalability and flexibility | `.codex/agents/architect.toml` |
| `engineer` | Maintainability and efficiency | `.codex/agents/engineer.toml` |
| `qa-robustness` | Functional correctness, edge cases, failure modes, regression | `.codex/agents/qa-robustness.toml` |
| `qa-quality` | Efficiency, performance, UX impact | `.codex/agents/qa-quality.toml` |

Each custom agent must end its final response with a `## Memory Entry` block.
After receiving agent output, verify the block exists. If it is missing, reject
the result and re-spawn or ask the agent to produce the missing contract. Persist
accepted entries under `.codex/agent-memory/<agent>/`.

Dual-verdict gate: both `qa-robustness` and `qa-quality` must pass for a stage
to proceed. If either fails, engineer fixes, then both QA agents re-verify. The
orchestrator must confirm output from both QA agents before proceeding.

Pass artifacts such as designs, code, plans, and diffs verbatim to agents.
Never summarize when the prompt template says verbatim.

## Workflow Routing

| Request Type | Workflow |
|---|---|
| Coding task with V-Model authorization | Phase 0 -> 0.5 -> 0.6 optional -> 1 -> 2&3 |
| Coding task without agent authorization | Phase 0 -> direct local implementation -> verification |
| Non-coding question or exploration | Phase 0 -> direct response |
| Infrastructure review | Phase 0 -> Review Flow |

## Phase 0: Clarity Gate

- Ambiguous: ask 1-3 clarifying questions, then stop.
- Underspecified: list assumptions and get confirmation.
- Clear: state key assumptions and proceed.

## Phase 0.5: Context Indexing

If the task involves a large codebase or many documents, scan relevant sources
and write structured index files to `.codex/index/`, or use the project context
settings in `.codex/context.toml` to generate a context capsule under
`.codex/context/capsules/`, before spawning agents or doing broad local work.
Pass capsule paths and only the minimum needed raw files to agents. Check
freshness before reuse. Implementation work must read raw files before editing.
Skip indexing for tasks scoped to 1-3 known files.

## Plan Archival

When a detailed plan is proposed, save it to `.codex/plans/` with a unique,
descriptive filename such as `auth-middleware-redesign-2026-04-29.md`. Never
overwrite `.codex/plans/current.md` without archiving first.

## Approval Gate

Codex hooks are not the default enforcement mechanism for this template. Prefer
stable Codex features, user-level sandbox and approval settings, command rules,
and these project instructions. Project-local `.codex/config.toml` should not
force `sandbox_mode` or `approval_policy` unless a project intentionally needs a
stricter posture than the user's global default.

For V-Model implementation work, approval is an orchestrator contract: propose
or archive a plan, wait for explicit user approval, then create
`.codex/plans/.approved` and update `.codex/plans/.stage` as needed. Gate
artifacts are protected workflow markers and must only be created after explicit
approval.

Command policy belongs in `.codex/rules/*.rules` and user-level
`~/.codex/rules/*.rules`. Hooks under `.codex/hooks/` are legacy or optional
strict-mode material for lifecycle checks that native config cannot express.
Continue to ask the user before destructive actions or broad rewrites.

When the active session uses yolo/full-access permissions, subagents inherit
that live runtime posture. Treat custom-agent `sandbox_mode` fields as useful
for non-yolo profiles, not as hard containment during yolo sessions.

## Session Continuity

Compaction or resume recovery:

1. Read `.codex/plans/current.md` to restore the active plan.
2. Check `.codex/plans/.approved` and `.codex/plans/.stage`.
3. Resume from the interrupted phase.

At session start, resume, or compaction recovery, read
`.codex/plans/session-state.md` when it exists and ask the user whether to
resume or start fresh. When compacting, preserve the full list of modified
files, current workflow phase, and unresolved decisions.

Before ending after substantial work, ensure `.codex/plans/session-state.md`
captures what was accomplished, what is pending, and any blockers.

## Verification

This template includes placeholder `verify.sh` and `verify.ps1` scripts.
Projects should customize them. Run the smallest meaningful verification first,
then broader checks when risk warrants it. For longer Bash checks, use the
OS-agnostic timeout pattern:

```bash
TIMEOUT_CMD=$(command -v timeout 2>/dev/null || command -v gtimeout 2>/dev/null || echo "")
VERIFY_TIMEOUT="${VERIFY_TIMEOUT:-30}"
if [[ -n "$TIMEOUT_CMD" ]]; then
  "$TIMEOUT_CMD" "$VERIFY_TIMEOUT" ./verify.sh
else
  ./verify.sh
fi
```
