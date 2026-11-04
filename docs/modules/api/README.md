# Module: api

- **Owner:** TBD
- **Status:** In progress
- **Code:** `backend/src/gatp/api/`
- **Tasks:** T-008, plus endpoints for every feature task
- **ADRs:** ADR-002, ADR-004, ADR-012

## Responsibility
The orchestrator. Exposes the JSON/SSE API, owns the workflow state machine, enforces approval gates (G0–G5) and blocking clarification requests, and dispatches typed jobs to the runner. Does not run browsers and does not call LLM providers directly (goes through feature modules → llm-gateway).

## Interfaces
| Direction | Interface | Contract |
|---|---|---|
| Provides | REST JSON + SSE | OpenAPI schema → TS client |
| Consumes | store | Repositories |
| Consumes | test-designer, codegen, maintainer | Python service calls |
| Consumes | runner | Typed job protocol (`inspect`, `run_tests`) — transport decided in T-006 |

## Workflow states (initial)
`created → inspected → scoped(G0) → plan_proposed → plan_approved(G1) → code_generated → code_approved(G2) → run_approved(G3) → ran → (feedback → revised → run_approved)* → rescanned → repairs_proposed → repair_approved(G4) → rerun`

A clarification request in `open` state blocks the transition that raised it.

## Approval rule
No endpoint that executes tests or applies repairs proceeds without an `Approval` row referencing the **exact** artifact version(s) being acted on. Editing a version invalidates its approval.

## Implemented so far (T-002 skeleton)
| Item | Where | Notes |
|---|---|---|
| App factory `create_app(settings=None)` | `api/app.py` | Factory so tests inject settings; adds CORS for the Vite origins in `GATP_CORS_ORIGINS` |
| `GET /api/health` → `Health{status, app, version}` | `api/app.py`, `api/schemas.py` | `operation_id="getHealth"`; every route gets an explicit operation id + Pydantic response model so the generated TS types are stable |
| `gatp-api` entrypoint | `api/main.py` | uvicorn with `factory=True`; flags `--host --port --reload` (defaults from settings) |
| OpenAPI export | `api/export_openapi.py` | `python -m gatp.api.export_openapi <file>`; sorted JSON so diffs are stable; used by `uv run poe gen-client` |
| Settings | `gatp/config.py` | pydantic-settings, prefix `GATP_`, reads `.env`; shared with the runner |

Tests: `backend/tests/test_health.py`, `test_openapi_export.py`.

## Known limitations
TBD.
