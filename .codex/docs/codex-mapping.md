# Claude to Codex Mapping

This file documents how the original Claude Code template maps to Codex CLI.
The repository root `AGENTS.md` intentionally keeps only startup-critical
instructions; historical mapping details live here to avoid bloating every
Codex session.

| Claude template | Codex template | Notes |
|-----------------|----------------|-------|
| `CLAUDE.md` | `AGENTS.md` | Codex reads `AGENTS.md` as project instructions. |
| `.claude/settings.json` | `.codex/config.toml` + user/global Codex settings | Codex uses TOML config. Hooks are optional legacy or strict-mode material, not the template default. |
| `.claude/agents/*.md` | `.codex/agents/*.toml` | Codex custom agents are standalone TOML files. |
| `.claude/hooks/*.sh` | `.codex/hooks/*.sh` | Optional legacy/strict-mode scripts only; default workflow uses features, rules, and `AGENTS.md`. |
| `.claude/rules/*.md` | `.codex/docs` and `.codex/rules/*.rules` | Codex command approval rules use Starlark `.rules`. |
| `.claude/skills/*` | `.agents/skills/*` | Repo skills use the open agent skills layout. |
| `.claude/plans` | `.codex/plans` | Same workflow state convention. |
| `.claude/research` | `.codex/research` | Same provenance and index pattern. |
| `.claude/agent-memory` | `.codex/agent-memory` | Template-managed memory, not automatic Codex memory. |

Project-specific active plans, session-state files, and old agent-memory entries
from the Claude repository were intentionally not copied into this template.
