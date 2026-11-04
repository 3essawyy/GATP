# T-002: Repo skeleton (backend, frontend, CI, tooling)

- **Status:** Todo
- **Phase:** P1
- **Target:** W+0
- **Modules:** all (scaffold)
- **Requirements:** REQ-P1-S, REQ-P2-6
- **Depends on:** T-001
- **Plan:** PLAN-002 (to write)
- **TCs:** TC-102
- **Branch / PR:** `chore/T-002-repo-skeleton`

## Goal
A runnable empty system: FastAPI app with health endpoint, runner entrypoint stub, React/Vite/TS app calling the health endpoint through a generated client, and CI running lint/type/tests for both.

## Scope
- In: `backend/` package layout with one package per module; Python env + tooling (decide uv vs pip+venv, ruff, mypy/pyright, pytest); `frontend/` Vite React TS; OpenAPI → TS client generation script; Vite dev proxy; `.env.example`; GitHub Actions workflow; Makefile or task runner scripts; `playwright install chromium` step.
- Out: feature logic.

## Acceptance criteria
- [ ] One command each to start api, runner, frontend (documented in SG-001)
- [ ] UI shows backend health via the generated client
- [ ] CI green on PR (backend lint+types+tests, frontend lint+typecheck+build)
- [ ] ADR(s) recording tooling choices (env tool, lint/type tools, frontend libs)

## Definition of Done
Standard (see [CLAUDE.md](../../CLAUDE.md)).

## Explain it (code-defense prep)
_To be written on completion._
