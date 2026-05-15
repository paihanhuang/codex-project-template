# Agent Prompt Templates

All templates end with: `Include the ## Memory Entry block.`

## Architect - Design Mode

- Mode: `You are in DESIGN MODE.`
- Task: `{user request, paraphrased with clarified scope}`
- Context: `{relevant index files or codebase context, verbatim when required}`
- Context Capsule: `{optional path to .codex/context/capsules/<name>.json or .md plus freshness status}`
- Constraints: `{from Clarity Gate and technology constraints}`
- Research Files: `{optional paths plus quoted ## TL;DR sections}`
- Deliverable: `Design proposal per output format.`

## Research - Investigation Mode

- Mode: `You are in INVESTIGATION MODE.`
- Topic: `{concise research question}`
- Context: `{why this research is needed and what decision it informs}`
- Seed Queries: `{optional}`
- Existing Research: `{optional prior research paths}`
- Deliverable: `Research file under .codex/research/ with INDEX.md updated.`

## Architect - Review Mode

- Mode: `You are in REVIEW MODE.`
- Design Under Review: `{Architect design proposal, verbatim}`
- Context Capsule: `{optional path used by the design, if any}`
- Focus: `Scalability risks, flexibility gaps, over-engineering.`
- Deliverable: `Architecture review per output format.`

## Engineer - Review Mode

- Mode: `You are in REVIEW MODE.`
- Design Under Review: `{Architect design proposal, verbatim}`
- Context Capsule: `{optional path used by the design, if any}`
- Focus: `Implementation feasibility, maintainability risks, performance concerns, missing edge cases.`
- Deliverable: `Engineering review per output format.`

## Engineer - Implementation Mode

- Mode: `You are in IMPLEMENTATION MODE.`
- Approved Plan: `{full content of .codex/plans/current.md, verbatim}`
- Current Stage: `Stage {N}: {stage title} / Scope: {stage scope only}`
- Codebase Context: `{relevant index files or file contents}`
- Context Capsule: `{optional path to .codex/context/capsules/<name>.json or .md; read raw files before editing}`
- Prior Stage Output: `{summary if any}`
- Deliverable: `Implement this stage exactly per the plan. No deviations.`

## QA-Robustness - Review Mode

- Mode: `You are in REVIEW MODE.`
- Design Under Review: `{Architect design proposal, verbatim}`
- Context Capsule: `{optional path used by the design, if any}`
- Focus: `Testability gaps, missing acceptance criteria, edge cases, failure modes, input handling gaps, order-of-operations vulnerabilities, regression risks.`
- Boundary Crossing: `Report efficiency/performance/UX issues tagged [out-of-scope: quality].`
- Deliverable: `Robustness review per output format.`

## QA-Quality - Review Mode

- Mode: `You are in REVIEW MODE.`
- Design Under Review: `{Architect design proposal, verbatim}`
- Context Capsule: `{optional path used by the design, if any}`
- Focus: `Performance risks, resource usage concerns, UX degradation paths, efficiency gaps, quality regression risks.`
- Boundary Crossing: `Report correctness/edge case/failure mode issues tagged [out-of-scope: robustness].`
- Deliverable: `Quality review per output format.`

## QA-Robustness - Verification Mode

- Mode: `You are in VERIFICATION MODE.`
- Approved Plan: `{full content of .codex/plans/current.md, verbatim}`
- Current Stage: `Stage {N}: {stage title} / Robustness Acceptance Criteria: {criteria}`
- Context Capsule: `{optional path used by the implementation, if any}`
- Implementation Diff: `{git diff or file changes}`
- Boundary Crossing: `Report efficiency/performance/UX issues tagged [out-of-scope: quality].`
- Deliverable: `Verify this stage against robustness acceptance criteria.`

## QA-Quality - Verification Mode

- Mode: `You are in VERIFICATION MODE.`
- Approved Plan: `{full content of .codex/plans/current.md, verbatim}`
- Current Stage: `Stage {N}: {stage title} / Quality Acceptance Criteria: {criteria}`
- Context Capsule: `{optional path used by the implementation, if any}`
- Implementation Diff: `{git diff or file changes}`
- Boundary Crossing: `Report correctness/edge case/failure mode issues tagged [out-of-scope: robustness].`
- Deliverable: `Verify this stage against quality acceptance criteria.`

When a context capsule is present, agents should use it as the shared retrieval
artifact and report missing or stale context explicitly. Capsules do not replace
raw source reads before implementation edits.

## Engineer - Infrastructure Review Mode

- Mode: `You are in REVIEW MODE (Infrastructure).`
- Analysis Under Review: `{Orchestrator analysis, verbatim}`
- Scope: `{hooks, agents, settings, workflow, etc.}`
- Focus: `Maintainability risks, implementation gaps, efficiency concerns, practical issues overlooked.`
- Deliverable: `Engineering review per output format.`

## QA-Robustness - Infrastructure Review Mode

- Mode: `You are in REVIEW MODE (Infrastructure).`
- Analysis Under Review: `{Orchestrator analysis, verbatim}`
- Scope: `{hooks, agents, settings, workflow, etc.}`
- Focus: `Failure modes, workflow enforcement gaps, robustness issues, silent bypass scenarios.`
- Boundary Crossing: `Report efficiency/performance/UX issues tagged [out-of-scope: quality].`
- Deliverable: `QA robustness review per output format.`

Note: QA-Quality does not participate in infrastructure reviews.
