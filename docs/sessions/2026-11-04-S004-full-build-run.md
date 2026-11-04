# Session S004 — 2026-11-04 — Full-build run (T-003 onward)

- **Tasks touched:** T-003, T-004, T-005, T-006, T-007 (more appended as completed)
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
- **T-003:** BookShelf fixture site v1/v2, `poe fixtures`, `GATP_CHROMIUM_EXECUTABLE` setting, 14 new tests (TC-103 Pass), fixtures README, SG-001 section. PR #3.
- **T-004:** Store core: 15-table SQLAlchemy schema, Alembic (auto-migrate on start), repositories returning DTOs, immutable versions with diff/restore, double immutability (ORM guards + SQLite triggers), artifact files confined to `artifacts/`, `poe db-upgrade`/`db-revision`. 22 new tests (TC-104 Pass).
- Fixed: the ADR index was missing the ADR-014 row (a silent replace failure in S003). PR #4.
- **T-005:** LLM gateway: httpx Gemini/Ollama/fake providers, versioned templates with untrusted-data framing, cache (`reused` rows), backoff + fallback, Pydantic validation + one repair retry + semantic `check` hook, every attempt logged (`llm_calls`, migration 0002 adds `template_version`), `poe llm-check`, SG-003. 20 new tests (TC-105 automated Pass). PR #5.
- **T-006:** Runner: typed jobs (`inspect` stub, `recount`) over HTTP on a private Unix socket (0600 in 0700 dir, no TCP port), single worker thread, per-job 0700 sandbox, Playwright allowlist routing with blocked-request log, headed Chromium (verified under `xvfb-run`), `RunnerClient`, `LocatorSpec`. 17 runner tests (TC-106 Pass). PR #6.
- **T-007:** Inspector: read-only in-page extraction, ADR-006 candidates verified live (count + identity), non-positional default, flags for weak elements, source lines from served HTML, fingerprints; runner `inspect` with scope + setup steps (sign-in) + redirect check; store migration 0003; api converter; sample snapshots in `docs/samples/`. 8 inspector tests (TC-108 Pass).

## Decisions (with ADR links)
- T-003: none beyond PLAN-003.
- T-004: [ADR-015](../decisions/ADR-015-db-access-sqlalchemy-alembic.md) SQLAlchemy 2 + Alembic; immutability enforced twice.
- T-005: [ADR-016](../decisions/ADR-016-llm-gateway-design.md) gateway design; default `gemini-2.5-flash` (limits unverified: Google docs host blocked in the sandbox).
- T-006: [ADR-017](../decisions/ADR-017-runner-unix-socket-jobs.md) runner transport on a private Unix socket.
- T-007: [ADR-018](../decisions/ADR-018-inspection-setup-and-usability.md) setup steps; usable = unique and targets the element; positional CSS never default.

## Open items / blockers
- Waiting on Abdo to add `GATP_GEMINI_API_KEY` to the cloud environment; it is only visible to a **new** session. Then run `uv run poe llm-check` and fill SG-003 §6 (TC-105 live part, TC-111).
- Ollama live check must be done on a team machine (ollama.com is blocked here).

## Next steps (in order)
1. T-008 API core (projects, pages, inspections via runner, workflow state, gates, clarifications, migrate on startup, TS client).

## Notes for next session
- In this cloud container, Python Playwright needs `GATP_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium-1243/chrome-linux64/chrome` (the preinstalled revision differs from the one the pinned Playwright expects).
- Docker: start `dockerd` manually if you need it (TC-102 reruns).
