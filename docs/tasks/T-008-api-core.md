# T-008: API core — projects, inspections, workflow state, gates, clarifications

- **Status:** Todo
- **Phase:** P1
- **Target:** W+2
- **Modules:** api, store
- **Requirements:** REQ-G3, REQ-G4, REQ-G5, REQ-P1-2, REQ-P1-3
- **Depends on:** T-004, T-007
- **Plan:** PLAN-008 (to write)
- **TCs:** TC-109
- **Branch / PR:** `feat/T-008-api-core`

## Goal
The orchestrator backbone: endpoints, state machine, approval and clarification objects (see [api LLD](../modules/api/README.md)).

## Scope
- In: projects/pages/inspections endpoints; scope + selection + goal endpoints; generic `Approval` (bound to exact artifact versions) and `Clarification` models; state machine with guards; SSE progress; regenerate TS client.
- Out: feature-specific endpoints (added by their tasks).

## Acceptance criteria
- [ ] Guard tests: gated transitions fail without approval; editing a version invalidates its approval; open clarification blocks its step
- [ ] OpenAPI client regenerated and committed/generated in CI

## Definition of Done
Standard (see [CLAUDE.md](../../CLAUDE.md)).

## Explain it (code-defense prep)
_To be written on completion._
