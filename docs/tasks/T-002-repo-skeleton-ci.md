# T-002: Repo skeleton (backend, frontend, CI, tooling)

- **Status:** Done
- **Phase:** P1
- **Target:** W+0
- **Modules:** all (scaffold); api, runner, web-ui have code
- **Requirements:** REQ-P1-S, REQ-P2-6
- **Depends on:** T-001
- **Plan:** [PLAN-002](../implementationPlans/PLAN-002-repo-skeleton-ci.md)
- **ADRs:** [ADR-012](../decisions/ADR-012-backend-and-dev-tooling.md), [ADR-013](../decisions/ADR-013-frontend-libraries.md)
- **Guides:** [SG-001](../SystemGuides/SG-001-setup-and-run.md), [SG-002](../SystemGuides/SG-002-developer-workflow.md)
- **TCs:** TC-102 (partial: fixture site comes in T-003)
- **Session:** [S002](../sessions/2026-11-04-S002-t002-repo-skeleton.md)
- **Branch / PR:** `claude/serene-johnson-xtbl4s` (cloud-session branch; see S002) → squash-merged to `main`

## Goal
A runnable empty system: FastAPI app with a health endpoint, a runner entrypoint stub, a React/Vite/TS app that calls the health endpoint through a generated client, and CI running lint, type checks and tests for both.

## Scope
- In: `backend/` package layout with one package per module; Python env + tooling; `frontend/` Vite React TS; OpenAPI → TS client generation; Vite dev proxy; `.env.example`; GitHub Actions workflow; task runner; `playwright install chromium` step.
- Out: feature logic.

## Acceptance criteria
- [x] One command each to start api, runner and frontend (`uv run poe api|runner|web`, documented in SG-001)
- [x] UI shows backend health via the generated client (verified in headless Chromium: badge "API ok · v0.1.0")
- [x] CI green on the PR (backend lint+types+tests, frontend lint+typecheck+build, client freshness)
- [x] ADRs recording tooling choices (ADR-012 backend/dev tooling, ADR-013 frontend libraries)

## Deviations from PLAN-002
- **Ruff limited to Python files.** The installed ruff version also formats Markdown by default, which would have rewritten docs, so `include = ["*.py", "*.pyi"]`.
- **The import-linter test runs in a subprocess.** In-process, import-linter reconfigures logging and disables existing loggers, which broke the runner log test when the suite ran in order.
- **TypeScript pinned to 5.9.3, not 7.x.** `openapi-typescript` and `typescript-eslint` don't support TS 7 yet.
- **Kept `httpx` for the TestClient.** Starlette suggests `httpx2`; adding that package was blocked in this session, and the warning is harmless.
- **Layer contract design.** import-linter doesn't allow mixing independent (`|`) and non-independent (`:`) siblings in one layer, so the rules are one `layers` contract plus three `forbidden` contracts.

## Explain it (code-defense prep)

**What.** The empty system that every later task plugs into:

- **Processes:** two Python processes (`gatp-api`, `gatp-runner`) and one web app (`frontend/`).
- **Shared code:** both Python processes live in one package (`backend/src/gatp/`), which has a sub-package for each of the 9 modules.
- **Commands:** one cross-platform command per action (`uv run poe …`).
- **CI:** one workflow that blocks bad merges.

**Why these choices** (details in ADR-012/013):
- **uv:** one tool installs Python 3.12, creates the venv and installs the exact locked versions. A fresh-machine setup (TC-102) is therefore three commands on every OS.
- **poethepoet:** Make doesn't exist on native Windows, and part of the team uses Windows. poe tasks live in `pyproject.toml` and run through uv.
- **mypy `--strict` + ruff:** Claude writes most of the code, so strict automated checks are our safety net in place of human review.
- **Generated client:** the UI must stay thin (ADR-002), and hand-written API calls drift from the backend. openapi-typescript generates *types only*; openapi-fetch is a ~6 kB wrapper. There's very little generated code to understand.
- **Runner as a separate process now:** ADR-004 requires the browser to run outside the API process. Having the entrypoint from day one keeps that boundary real before any job code exists.

**How it works:**
1. `uv run poe api`: poe runs `gatp-api --reload`. `gatp.api.main` parses flags and calls `uvicorn.run("gatp.api.app:create_app", factory=True)`. `create_app()` builds FastAPI, adds CORS for the dev origins, and registers `GET /api/health`, which returns a Pydantic `Health` model.
2. `uv run poe web`: Vite serves React on :5173 and proxies every `/api/*` request to :8000. The browser therefore talks to one origin, and production can serve both from the same place later.
3. In the browser:
   - `main.tsx` wraps the app in `MantineProvider` and `QueryClientProvider`.
   - `HealthBadge` calls `useHealth()`.
   - `useHealth()` is a TanStack Query hook that calls `api.GET('/api/health')`, where `api` is the openapi-fetch client typed by `schema.d.ts`.
   - The hook polls every 10 s, and the badge renders one of three states.
4. Client generation: `uv run poe gen-client` runs `python -m gatp.api.export_openapi frontend/openapi.json`, which builds the app in-process and dumps the schema as sorted JSON. It then runs `openapi-typescript`, which turns that JSON into `src/api/schema.d.ts`. If a backend change isn't followed by regeneration, both CI and a pytest test fail.
5. `uv run poe runner` starts `gatp.runner.main`, which logs "runner ready" and waits on a `threading.Event`. SIGINT/SIGTERM set the event, and the process exits with code 0.
6. Module boundaries: import-linter reads contracts from `pyproject.toml`. For example, "runner never imports llm_gateway/store", and "feature modules never import runner". `test_architecture.py` runs it, so a forbidden import fails CI.

**Likely examiner questions:**
- *Why is the runner a separate process if it shares the venv?* Isolation in ADR-004 means process, filesystem and network boundaries: the browser and generated code never run inside the API process. Sharing installed packages doesn't weaken that. Import contracts stop the runner from reaching LLM or DB code, and a separate venv can be added later without changing callers.
- *How do you know the TS client matches the API?* It's generated from FastAPI's own OpenAPI schema. CI regenerates it and fails on any diff, and `test_committed_schema_is_current` checks the same thing in pytest.
- *What happens when the API is down?* The query fails (`retry: false`), and the badge shows "API unreachable" in red. Polling continues every 10 s and recovers on its own.
- *Why the Vite proxy instead of CORS?* With the proxy, the browser sees a single origin, so dev behaves like production. CORS is still configured only for the two dev origins, and a test proves other origins get no `Access-Control-Allow-Origin` header.
- *How would you add an endpoint?* Add the route with an `operation_id` and a response model, run `uv run poe gen-client`, write a hook in `queries.ts`, then use the hook in a component.
- *Why `--strict` mypy on a student project?* Most code is generated by an AI assistant without human review. Strict types plus tests are the cheapest way to catch errors before they reach the demo.
