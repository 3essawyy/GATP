# Module: api

- **Owner:** TBD
- **Status:** Implemented (core, T-008)
- **Code:** `backend/src/gatp/api/`
- **Tasks:** T-008, plus endpoints for every feature task
- **ADRs:** ADR-002, ADR-004, ADR-012, ADR-019

## Responsibility
The orchestrator. Exposes the JSON/SSE API, owns the workflow state machine, enforces approval gates (G0–G5) and blocking clarification requests, and dispatches typed jobs to the runner. Does not run browsers and does not call LLM providers directly (goes through feature modules → llm-gateway).

## Interfaces
| Direction | Interface | Contract |
|---|---|---|
| Provides | REST JSON + SSE | OpenAPI schema → TS client |
| Consumes | store | Repositories |
| Consumes | test-designer, codegen, maintainer | Python service calls |
| Consumes | runner | Typed job protocol (`inspect`, `run_tests`) — transport decided in T-006 |

## Endpoints (T-008; all JSON under `/api`, OpenAPI → `frontend/src/api/schema.d.ts`)
| Area | Endpoint | Notes |
|---|---|---|
| System | `GET /health`, `GET /runner/health`, `GET /gates` | Runner health reports `available` / `headless` |
| Projects | `POST /projects`, `GET /projects`, `GET /projects/{id}`, `PUT /projects/{id}/goal` | Creating a project stores its **origin** (the runner allowlist) and adds the start page |
| Pages | `GET/POST /projects/{id}/pages`, `PUT /pages/{id}/setup` | Pages and setup-step `goto` URLs must be on the project origin (ADR-018) |
| Requirements | `GET/POST /projects/{id}/requirements` | Tester's free-text requirements |
| Inspection | `POST /pages/{id}/inspections`, `GET /pages/{id}/snapshots`, `GET /snapshots/{id}`, `GET /files/{path}` | Runs the runner's `inspect` job with the page's setup steps, stores an immutable snapshot, returns browser time separately |
| Scope (G0) | `PUT/GET /projects/{id}/scope` | Selection (`include`/`exclude` element keys per snapshot), goal, notes → versioned `scope` artifact |
| Artifacts | `GET /projects/{id}/artifacts`, `GET /artifacts/{id}/versions[/{n}]`, `POST /artifacts/{id}/versions`, `GET /artifacts/{id}/diff?a=&b=`, `POST /artifacts/{id}/restore` | Every edit is a new version; restore needs a G5 approval of that exact version |
| Gates | `POST/GET /projects/{id}/approvals`, `GET /projects/{id}/clarifications`, `POST /clarifications/{id}/answer`, `GET /projects/{id}/workflow` | See rules below |
| Events | `GET /projects/{id}/events` (SSE) | `inspection_started/finished/failed`, `scope_saved`, `artifact_changed`, `approved`, `clarification_answered`, … |

## Gate rules ([ADR-019](../../architectureDecisionRecords/ADR-019-gates-on-versions-computed-workflow.md))
- **What gets approved:** content behind a gate is a versioned artifact. G0 → `scope`, G1 → `test_plan`, G2 → `page_object`/`test_file`, G5 → any version being restored. G3 (run) and G4 (repair) approvals carry a `subject` (which tests/versions, which repair) and arrive in T-014/T-017.
- **An approval names an exact `artifact_version_id`.** It's accepted only if:
  - The gate fits the artifact kind.
  - The version belongs to the project.
  - It's the latest version (except G5).
  - The step has no open clarification.
- **Edits invalidate:** a tester edit or a model revision creates a new version, which carries no approval, so the step goes back to `needs_approval` without any explicit "revoke".
- **Gated actions check:** they call `require_approval(services, gate, version)`, so actions downstream of a gate check the exact version they are about to use.
- **Clarifications** (raised by feature modules) block their step (`inspect`, `scope`, `plan`, `code`, `run`, `maintain`). An answer records the tester's name and time.

## Weakening clarifications (T-015, [ADR-023](../../architectureDecisionRecords/ADR-023-feedback-and-weakening-guard.md))
- **Where they come from:** `guard_sync.py` keeps one open `weakening` clarification per guard finding. The baseline is the last approved version (plan: G1; `tests/` files: G2).
- **When they are synced:**
  - after a plan store or answer (`plan_service`);
  - after a generic artifact edit or restore (`code_service.on_artifact_changed`);
  - after generation.
- **Answers:** only **Accept this change** or **Restore the approved version**; free text gets 422. Restore writes a new version (plan check back with its confirmation, or the approved test file).
- **Run feedback:** `POST /plan/propose` takes `run_id` + `test_ids`. `RunResultOut.failed_expectations` lists the plan expectation ids on the failing line.

## Workflow state (computed, never stored)
`GET /projects/{id}/workflow` returns `inspect`, `scope`, `plan`, `code` (later `run`, `maintain`) with `status ∈ todo | needs_approval | approved | blocked`, derived from snapshots, artifacts, approvals and open clarifications (`api/workflow.py`).

## Files
| File | Contents |
|---|---|
| `app.py` | `create_app(settings=None, services=None)`, lifespan (build services → migrate DB, bind event loop), router includes, error mapping (404/409/422/502/503 with `{"error", "detail"}`) |
| `services.py` | `Services` container (repositories, runner client, LLM gateway, files, events), `build_services()` |
| `workflow.py` | Gate rules, `GateBlockedError`, `workflow_state()` |
| `events.py` | `EventBus` for SSE |
| `inspections.py` | `to_snapshot_in()` (runner result → store snapshot) |
| `schemas.py` | All request/response models |
| `routes/` | `system`, `projects`, `inspections`, `scope`, `artifacts`, `gates`, `assist`, `plan`, `code`, `runs`, `maintain` |
| `main.py`, `export_openapi.py` | Entrypoint, schema export |

## Error mapping
| Error | HTTP | `error` |
|---|---|---|
| `NotFoundError` | 404 | `not_found` |
| `ValidationError` (store) | 422 | `invalid` |
| `GateBlockedError` | 409 | `gate_blocked` |
| Runner down / rejected | 503 / 400 | `runner_unavailable` / `runner_rejected` |
| Inspection failed in browser | 502 | `inspection_failed` |
| No model / invalid model output | 503 / 502 | `model_unavailable` / `model_output_invalid` |

## Tests
`test_api_core.py` (projects, origin rule, goal/requirements, inspection through a real headless executor, setup steps, files, runner down), `test_api_gates.py` (TC-109: exact-version approvals, edit invalidates, stale/wrong-gate refusals, clarification blocking, G5 restore; TC-110 stored scope; SSE bus), `test_health.py`.

## Known limitations
- Single local user, no authentication; the server binds to 127.0.0.1 (agreed in S004). The approver's name is self-declared and recorded per approval.
- Inspection requests are synchronous (a few seconds); progress is announced over SSE events.
