# GATP — Human-in-the-Loop Web Testing Assistant

Course project for **Generative AI for Software Testing** (Fall 2026).

GATP helps a human tester inspect a webpage, design test cases, generate Playwright (Python, POM) tests, execute approved tests in an isolated runner, and maintain those tests after the page changes — with explicit human approval at every consequential step.

| Phase | Due | Points | Status |
|---|---|---|---|
| Phase 1 — Architecture and guided inspection | Week 9 | 10 | Planning |
| Phase 2 — Complete supervised workflow | Week 13 | 20 | Planning |
| Bonus — Creative work | Week 13 | +1 | Deferred (decide after P1 feedback) |

## Stack (see [ADRs](docs/decisions/README.md))

- **Backend:** Python 3.11+, FastAPI (JSON API), SQLite + artifacts folder
- **Frontend:** React + Vite + TypeScript (thin UI, generated API client)
- **Models:** Google Gemini Flash (free tier) primary, Ollama local fallback
- **Browser automation:** Playwright for Python; generated tests use pytest-playwright + Page Object Model
- **Runner:** separate, restricted host process with a visible browser

## Documentation

All project knowledge lives in [`docs/`](docs/README.md). Start there.

- High-level design: [docs/architecture/HLD.md](docs/architecture/HLD.md)
- Modules: [docs/modules/](docs/modules/README.md)
- Task status (source of truth): [docs/tasks/README.md](docs/tasks/README.md)
- Latest session handoff: [docs/sessions/](docs/sessions/README.md)

## Repository layout (planned — created in T-002)

```
backend/            FastAPI app + Python packages (one package per module)
frontend/           React/Vite/TS thin UI
fixtures/site-v1/   Our own test website (baseline)
fixtures/site-v2/   Modified version (locator change + ambiguous change)
docs/               All documentation
```
