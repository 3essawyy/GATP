# Module: api

- **Owner:** TBD
- **Status:** Planned
- **Code:** `backend/gatp/api/`
- **Tasks:** T-008, plus endpoints for every feature task
- **ADRs:** ADR-002, ADR-004

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

## Known limitations
TBD.
