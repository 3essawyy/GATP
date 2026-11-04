# ADR-001: Team workflow and documentation structure

- **Status:** Accepted
- **Date:** 2026-11-04
- **Session:** S001
- **Related:** REQ-P2-6, all tasks

## Context
Team of 4. Maintainability of project assets and continuity between chat sessions are top priorities. Claude does the planning, implementation and testing; team members must still defend the code.

## Decision
- Claude implements everything. **No PR review**; Claude self-merges.
- Git: one branch per task (`<type>/T-NNN-slug`) → PR → **squash merge** to protected `main`; tags `phase1`, `phase2`.
- Work is owned **by component** (9 modules, see [modules/README](../modules/README.md)). Owners prepare for the defense using the task docs' **Explain it** sections.
- Docs live **in the repo under `/docs`**, versioned with code.
- Folders: `architecture/`, `modules/<name>/`, `decisions/`, `implementationPlans/`, `tasks/`, `TCs/`, `SystemGuides/`, `RefrenceDocs/`, `sessions/`. The old project's `HOs/`, `PRs/`, `ReviewLearnings/` were deliberately dropped; HLD + module + decision folders added.
- `docs/tasks/` markdown is the **single source of truth** for task status.
- Files named by ID (`T-NNN`, `PLAN-NNN`, `ADR-NNN`, `TC-NNN`, `SG-NNN`; sessions date-prefixed). Every folder has a README index.
- Full Definition of Done applies to every task (see [CLAUDE.md](../../CLAUDE.md)).

## Alternatives considered
| Option | Why not |
|---|---|
| Docs outside repo | No history, drifts from code |
| GitHub Issues as status source | Chosen markdown so every session can read/write status in-repo |
| PR review by component owners | User chose speed; defense prep moved into task docs |
| Branch per phase | Huge, unreviewable merges |

## Consequences
- Without review, task docs carry the full burden of knowledge transfer — the **Explain it** section is mandatory.
- Session logs are the handoff mechanism between chats.
- Old-project templates (sessions/tasks/plans) may be mirrored later if samples become available.
