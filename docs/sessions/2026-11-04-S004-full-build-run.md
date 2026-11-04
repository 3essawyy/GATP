# Session S004 — 2026-11-04 — Full-build run (T-003 onward)

- **Tasks touched:** T-003 (more appended as completed)
- **Branches / PRs:** `claude/serene-johnson-xtbl4s`, one squash-merged PR per task

## Interview outcome (before the run)
Abdo approved a "grill now, then run" mode: Claude builds T-003…T-021 in order without stopping and asks only for blockers. Decisions agreed, each recorded as an ADR in the task that implements it:

| Area | Decision | ADR (when written) |
|---|---|---|
| LLM in dev | Real Gemini via `GATP_GEMINI_API_KEY` env secret (added by Abdo, never in the repo); CI uses a deterministic fake provider; Ollama checked by the team locally | T-005 |
| Visible browser | Always headed; Xvfb + screenshots in the cloud; `GATP_RUNNER_HEADLESS=1` only for CI | T-006 |
| Fixture site | "BookShelf" static HTML/JS; FXC-1 clear, FXC-2 ambiguous | T-003 (in PLAN-003, ADR-009) |
| Store | SQLAlchemy 2 + Alembic behind repositories | T-004 |
| Runner IPC | Typed HTTP over a Unix domain socket (0600); progress relayed API → UI via SSE | T-006 |
| Codegen | Page objects rendered from inspected elements; LLM emits step JSON referencing known element IDs only; Jinja templates render pytest + POM; AST check as second guard | T-013 |
| Sandbox | bubblewrap + resource limits + scrubbed env + origin allowlist; clear error if bwrap is missing | T-014/T-020 |
| Product shape | Project = one origin, many pages inspected one by one; workspace + step nav with gate states (React Router); single local user, no auth, approver name recorded | T-008/T-009 |
| Owners | Member 1–4 suggested grouping; names filled in later | — |
| Submission | Claude writes SG-004 and records a backup walkthrough video; team records the live demo; Markdown + PDF export; tags `phase1-rc`/`phase2-rc`, final tags at real submission | T-011/T-021 |
| Bonus | Stays deferred (ADR-011) | — |

## Done
- **T-003:** BookShelf fixture site v1/v2, `poe fixtures`, `GATP_CHROMIUM_EXECUTABLE` setting, 14 new tests (TC-103 Pass), fixtures README, SG-001 section.

## Decisions (with ADR links)
- None new in T-003 beyond PLAN-003 (no ADR needed).

## Open items / blockers
- Waiting on Abdo to add `GATP_GEMINI_API_KEY` to the cloud environment; it is only visible to a **new** session.

## Next steps (in order)
1. T-004 Store core.

## Notes for next session
- In this cloud container, Python Playwright needs `GATP_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium-1243/chrome-linux64/chrome` (the preinstalled revision differs from the one the pinned Playwright expects).
- Docker: start `dockerd` manually if you need it (TC-102 reruns).
