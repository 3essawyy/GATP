# T-006: Runner process — job protocol, sandbox, allowlist, headed browser

- **Status:** Todo
- **Phase:** P1
- **Target:** W+1
- **Modules:** runner, api
- **Requirements:** REQ-P1-2, REQ-Q5, REQ-Q6
- **Depends on:** T-002
- **Plan:** PLAN-006 (to write)
- **TCs:** TC-106
- **Branch / PR:** `feat/T-006-runner`

## Goal
The isolated process that owns every browser (ADR-004).

## Scope
- In: choose core↔runner transport (ADR); typed jobs (`inspect` stub, `recount`, later `collect`/`run_tests`); per-job sandbox dir; Playwright routing allowlist with blocked-request log; headed Chromium (headless flag for CI); timeouts; api-side client.
- Out: inspection logic (T-007), test execution (T-014).

## Acceptance criteria
- [ ] Runner rejects unknown job types and non-allowlisted URLs
- [ ] Requests to non-allowlisted origins are aborted and logged (test against fixture site linking out)
- [ ] Sandbox dir created per job and cleaned up

## Definition of Done
Standard (see [CLAUDE.md](../../CLAUDE.md)).

## Explain it (code-defense prep)
_To be written on completion._
