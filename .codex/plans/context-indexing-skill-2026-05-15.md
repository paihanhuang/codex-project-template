# Context Indexing Skill Plan

Date: 2026-05-15
Status: Implemented on 2026-05-15

## Problem Restatement

The project now has local context-indexing tooling under `.codex/tools/` and
configuration under `.codex/context.toml`, but Codex will only use that tooling
reliably if the workflow is discoverable at the right time. A repo-local skill
should teach Codex when to refresh/query the local index, when to generate or
use context capsules, and when raw file reads are still required.

This skill must remain a thin procedural layer. It should not duplicate the
implementation, replace `.codex/docs/context-indexing.md`, or encourage agents
to trust generated summaries without source verification.

## Proposed Skill

Path:

```text
.agents/skills/context-indexing/SKILL.md
```

Skill name:

```text
context-indexing
```

Trigger description:

Use when a task asks Codex to query, reference, summarize, navigate, or work
across a large codebase or document archive; when the user asks to save tokens
or avoid re-scanning; when `.codex/tools/context_index.py`, `.codex/context.toml`,
context capsules, lexical indexes, manifests, or retrieval status are relevant.

Core responsibilities:

- decide whether the task is small, medium, or large context;
- run `status`, `index-lexical`, or `query` commands when useful;
- use existing capsules when fresh;
- generate or request capsule creation when a large task needs shared context;
- require raw file reads before implementation edits;
- report freshness, gaps, and privacy-sensitive indexing concerns.

## Stage-Based Implementation Plan

### Stage 0: Scope And Trigger Contract

Implementation:

- Define exact trigger cases for the skill:
  - large codebase reference/query;
  - big document archive reference/query;
  - token-saving context retrieval;
  - use of `.codex/tools/context_index.py`;
  - use of `.codex/context/capsules/`;
  - stale index or manifest troubleshooting.
- Define explicit non-trigger cases:
  - tiny tasks scoped to 1-3 known files;
  - unrelated skill creation;
  - general search when no local repo/archive context is involved.
- Decide that the skill is repo-local under `.agents/skills/`, not global
  `$CODEX_HOME/skills`, because it references project-specific paths.

Testing:

- Review the frontmatter description against realistic prompts:
  - "Find where auth timeout is configured."
  - "Query the docs archive for retention policies."
  - "Use the context index."
  - "Edit this one file."
- Confirm the first three should trigger and the single-file edit should not.

Exit criteria:

- Trigger wording is broad enough to catch real context-indexing requests and
  narrow enough to avoid loading for normal small edits.

### Stage 1: Minimal SKILL.md

Implementation:

- Create `.agents/skills/context-indexing/SKILL.md`.
- Keep the body concise and procedural.
- Include the local command recipes:

```bash
python3 .codex/tools/context_index.py --root . status
python3 .codex/tools/context_index.py --root . index-lexical
python3 .codex/tools/context_index.py --root . query "<query>" --limit 10
```

- Add the decision workflow:
  - small task: read raw files directly;
  - medium task: use focused `rg` and `.codex/index/` markdown summaries;
  - large task: check status, refresh index if needed, query, then use or create
    a context capsule.
- Add a hard rule that implementation edits require raw source reads even when
  query results or capsules identify likely files.
- Add a hard rule to report stale/missing index state rather than silently
  trusting it.

Testing:

- Run the skill-creator `quick_validate.py` against the skill directory.
- Manually inspect that `SKILL.md` has valid frontmatter with `name` and
  `description`.
- Confirm it does not include bulky implementation docs already present in
  `.codex/docs/context-indexing.md`.

Exit criteria:

- The skill validates and is short enough to be loaded frequently without
  wasting context.

### Stage 2: Optional UI Metadata

Implementation:

- Add `.agents/skills/context-indexing/agents/openai.yaml` only if the repo wants
  UI-facing skill metadata.
- Generate it using `skill-creator` scripts instead of hand-writing stale UI
  fields.
- Keep metadata aligned with the `SKILL.md` trigger contract.

Testing:

- Validate generated metadata if the generator is used.
- Confirm the default prompt points users toward local context status/query
  workflows, not broad implementation claims.

Exit criteria:

- Optional metadata exists only if it adds value; otherwise the stage is skipped.

### Stage 3: Workflow Integration Checks

Implementation:

- Update `.codex/docs/context-indexing.md` only if it needs a short pointer to
  the skill.
- Avoid adding skill instructions to `AGENTS.md` unless a concise pointer is
  genuinely needed. `AGENTS.md` should stay small.
- Confirm the skill references existing docs instead of duplicating them.

Testing:

- Run `./verify.sh`.
- Run:

```bash
python3 .codex/tools/context_index.py --root . status
python3 .codex/tools/context_index.py --root . query "context capsule" --limit 3
```

- Confirm generated context artifacts remain ignored by Git.

Exit criteria:

- Existing context-indexing verification still passes.
- Skill addition does not cause generated indexes or caches to become tracked.

### Stage 4: Scenario-Based Validation

Implementation:

- Create a lightweight scenario checklist in the implementation notes or test
  output, not as a permanent extra README.
- Validate behavior against four task classes:
  - codebase lookup;
  - document archive lookup;
  - stale index recovery;
  - implementation task using query results.

Testing:

- Codebase lookup:
  - run a lexical query;
  - verify results include source paths and line anchors;
  - read the selected raw file before making any hypothetical edit.
- Document archive lookup:
  - with current Stage 2 tooling, verify text/markdown docs are searchable;
  - note that PDFs/DOCX remain Stage 4 of the broader plan.
- Stale index recovery:
  - modify a temporary fixture file in tests or use the existing unit test;
  - confirm `status` reports stale.
- Implementation task:
  - verify the skill says query/capsule results are selection aids, not edit
    authority.

Exit criteria:

- The skill consistently leads Codex to use the local index when helpful and to
  fall back to raw evidence when necessary.

### Stage 5: Maintenance And Drift Controls

Implementation:

- Add a verification check only if it can be simple and stable:
  - frontmatter exists;
  - required command strings still point to `.codex/tools/context_index.py`;
  - skill mentions raw file reads before edits;
  - skill mentions stale index handling.
- Do not add brittle prose snapshot tests.

Testing:

- Extend `.codex/tools/validate-context-artifacts.py` or add a small dedicated
  skill validation script.
- Run `./verify.sh`.

Exit criteria:

- Future edits cannot accidentally remove the core safety and usage rules.

## Cross-Critique Concerns Addressed

- Architect concern: the skill could become a second workflow system. Resolution:
  keep it as a thin trigger/runbook layer and link to existing docs.
- Architect concern: global installation could leak project-specific assumptions.
  Resolution: create it as a repo-local skill under `.agents/skills/`.
- Engineer concern: skill instructions can drift from actual CLI behavior.
  Resolution: use the real command names from `context_index.py` and add minimal
  validation for required command strings.
- Engineer concern: adding references and docs could increase token load.
  Resolution: no extra README or broad reference files unless the skill body
  grows too large; keep `SKILL.md` concise.
- QA robustness concern: agents may trust capsules or FTS results as truth.
  Resolution: skill must explicitly require raw file reads before editing and
  freshness checks before reuse.
- QA robustness concern: indexing can expose secrets or private archives.
  Resolution: skill must point to `.codex/context.toml` privacy defaults and
  report secret/exclusion concerns before refreshing indexes over new roots.
- QA robustness concern: stale indexes can cause wrong answers. Resolution:
  skill begins large-context work with `status` and refreshes or reports stale
  state before relying on results.
- QA quality concern: skill may trigger too often and waste context. Resolution:
  explicit non-trigger cases and concise frontmatter.
- QA quality concern: validation could become brittle. Resolution: validate only
  structural frontmatter and safety-critical command/rule presence.

## Acceptance Criteria

- `.agents/skills/context-indexing/SKILL.md` exists with valid frontmatter.
- The skill tells Codex when to use direct reads, markdown indexes, lexical
  context index queries, and capsules.
- The skill includes the correct Stage 2 commands.
- The skill requires freshness checks and raw file reads before edits.
- The skill does not duplicate the full context-indexing docs.
- `./verify.sh` passes after implementation.
- Generated indexes and caches remain ignored by Git.

## Recommended Approval

Approve Stages 0, 1, 3, 4, and 5. Skip Stage 2 unless UI-facing skill metadata
is actually needed.
