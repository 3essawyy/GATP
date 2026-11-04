# GATP — Human-in-the-Loop Web Testing Assistant

Course project for **Generative AI for Software Testing** (Fall 2026).

GATP helps a human tester inspect a webpage, design test cases, generate Playwright (Python, POM) tests, execute approved tests in an isolated runner, and maintain those tests after the page changes — with explicit human approval at every consequential step.

| Phase | Due | Points | Status |
|---|---|---|---|
| Phase 1 — Architecture and guided inspection | Week 9 | 10 | Planning |
| Phase 2 — Complete supervised workflow | Week 13 | 20 | Planning |
| Bonus — Creative work | Week 13 | +1 | Deferred (decide after P1 feedback) |

## Stack (see [ADRs](docs/decisions/README.md))

- **Backend:** Python 3.12 (uv), FastAPI (JSON API), SQLite + artifacts folder; ruff + mypy strict + pytest
- **Frontend:** React + Vite + TypeScript, Mantine, TanStack Query (thin UI, client generated from OpenAPI)
- **Models:** Google Gemini Flash (free tier) primary, Ollama local fallback
- **Browser automation:** Playwright for Python; generated tests use pytest-playwright + Page Object Model
- **Runner:** separate, restricted host process with a visible browser

## Documentation

All project knowledge lives in [`docs/`](docs/README.md). Start there.

- High-level design: [docs/architecture/HLD.md](docs/architecture/HLD.md)
- Modules: [docs/modules/](docs/modules/README.md)
- Task status (source of truth): [docs/tasks/README.md](docs/tasks/README.md)
- Latest session handoff: [docs/sessions/](docs/sessions/README.md)

## Quick start

Needs **uv** and **Node.js 22+**. Full guide (incl. Windows): [SG-001](docs/SystemGuides/SG-001-setup-and-run.md).

```bash
uv sync
```
```bash
uv run poe web-install
```
Then, in three terminals: `uv run poe api`, `uv run poe runner`, `uv run poe web`, and open http://localhost:5173. `uv run poe check` runs everything CI runs ([SG-002](docs/SystemGuides/SG-002-developer-workflow.md)).

## Repository layout

```
pyproject.toml      Python project, tool config and `poe` tasks
backend/src/gatp/   FastAPI app + one sub-package per module
backend/tests/      pytest suite
frontend/           React/Vite/TS thin UI (generated API client in src/api/)
fixtures/site-v1/   Our own test website (baseline)                        — T-003
fixtures/site-v2/   Modified version (locator change + ambiguous change)  — T-003
docs/               All documentation
```
