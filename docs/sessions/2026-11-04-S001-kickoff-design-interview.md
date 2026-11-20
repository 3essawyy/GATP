# Session S001 — 2026-11-04 — Kickoff: design interview + docs scaffold

- **Tasks touched:** T-001
- **Branches / PRs:** `docs/T-001-docs-scaffold`

## Done
- Read the brief (`docs/RefrenceDocs/GenAI_Fall26_project.pdf`) and extracted it into [REQ IDs](../RefrenceDocs/REQ-requirements.md).
- Ran a full design interview with Abdo covering team, stack, models, runner, storage, locators, maintenance, versioning, testing, DoD, docs structure and scope.
- Created the docs system: [CLAUDE.md](../../CLAUDE.md), [HLD](../architecture/HLD.md), 9 [module LLD stubs](../modules/README.md), [ADR-001…011](../architectureDecisionRecords/README.md), [tasks T-001…T-022](../tasks/README.md), [acceptance TCs](../TCs/README.md), [SystemGuides index](../SystemGuides/README.md), templates for every folder.

## Decisions
| Topic | Decision | ADR |
|---|---|---|
| Team/workflow | 4 members; Claude implements all; no PR review; branch per task → PR → squash merge; ownership by component | ADR-001 |
| Docs | In-repo `/docs`; dropped HOs/PRs/ReviewLearnings; added architecture/modules/decisions; ID naming + README indexes; tasks markdown = status source of truth | ADR-001 |
| Stack | FastAPI JSON API + thin React/Vite/TS UI; generated TS client | ADR-002 |
| Models | Gemini Flash free tier primary; Ollama ~3B fallback (16 GB RAM) | ADR-003 |
| Runner | Separate restricted host process, visible browser, allowlist, sandbox | ADR-004 |
| Storage | SQLite + artifacts; immutable versions; restore = new version | ADR-005 |
| Locators | Playwright priority + live uniqueness | ADR-006 |
| Maintenance | Deterministic scoring; LLM explains only; ambiguity → clarification | ADR-007 |
| Generated tests | pytest-playwright + POM | ADR-008 |
| Testing | Own fixture site v1/v2 + pytest + GitHub Actions | ADR-009 |
| Scope | Phase 1 front-loads as much of Phase 2 as possible; relative weeks | ADR-010 |
| Bonus | Decide after Phase 1 feedback | ADR-011 |

## Open items / blockers
- **Calendar dates** for Week 9 / Week 13 unknown — plan uses relative weeks (W+0 = week of 2026-11-04).
- **Component owners** not assigned — fill in [modules/README](../modules/README.md).
- **Demo machine GPU** unconfirmed (16 GB RAM known) — confirm before T-005 pins the Ollama model.
- **Old project templates:** user's previous project folders (sessions/tasks/plans) couldn't be read (computer not reachable). Templates here are new; mirror the old ones later if wanted.
- **GitHub CLI token** was invalid in this session, so no PR could be opened via `gh`; the branch was merged to `main` with git directly. Branch protection on `main` is not configured yet (do it in GitHub settings).
- Open technical decisions listed in [architectureDecisionRecords/README](../architectureDecisionRecords/README.md#open-decisions-to-become-adrs).

## Next steps (in order)
1. **T-002** Repo skeleton + CI (write PLAN-002 first; record tooling ADRs).
2. **T-003** Fixture site v1/v2.
3. **T-004** Store core, **T-006** Runner, then **T-005** LLM gateway and **T-007** Inspector.
4. **T-008 → T-009 → T-010 → T-011** to close the Phase 1 path, then Phase 2 tasks in order.

## Notes for next session
Start by reading [CLAUDE.md](../../CLAUDE.md), this log, and [tasks/README](../tasks/README.md). The user wants Claude to do planning, implementation and testing; follow the Definition of Done strictly, especially the **Explain it** section of every task.
