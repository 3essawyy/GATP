# PLAN-008: API core (for T-008)

- **Task:** [T-008](../tasks/T-008-api-core.md)
- **Status:** Executed
- **Date:** 2026-11-04

## Approach
Turn the T-002 skeleton into the orchestrator: a `Services` container built at startup (DB migrated, runner client, gateway), routers per area, domain errors mapped to HTTP in one place, gates per [ADR-019](../decisions/ADR-019-gates-on-versions-computed-workflow.md), and an SSE event bus. Store additions: a `GateRepository` (approvals, clarifications, requirements), page setup steps (migration `0004`), and the `scope` artifact kind.

## Steps
1. Store: `gates.py`, `pages.setup`, `scope` kind.
2. API: `services.py`, `workflow.py`, `events.py`, `schemas.py`, `routes/*`, `app.py` lifespan + error handlers.
3. Tests: in-process runner adapter (real headless executor, no socket) + isolated settings per test.
4. Regenerate the TS client.
5. Docs: ADR-019, api LLD, TC-109/TC-110, task doc.

## Tests to add
| Test | Proves |
|---|---|
| `test_api_core.py` | Projects/pages/origin rule, goal/requirements, inspection end to end, setup steps, files (+ traversal), runner down → 503 |
| `test_api_gates.py` | TC-109 guards; scope storage/versioning (TC-110 stored part); G5 restore; SSE bus |

## Risks / open questions
| Item | Mitigation / decision |
|---|---|
| Long inspections block a worker thread | Acceptable for a single local user; SSE events report progress |

## Deviations (filled after execution)
- SSE is implemented as a per-project event bus (no streamed runner progress yet). Streaming test-run progress comes with `run_tests` in T-014.
