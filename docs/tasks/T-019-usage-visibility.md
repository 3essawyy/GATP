# T-019: Usage panel — per-call metrics, averages, fresh vs reused

- **Status:** Todo
- **Phase:** P2
- **Target:** W+6
- **Modules:** llm-gateway, api, web-ui
- **Requirements:** REQ-P2-5, REQ-Q8, REQ-Q9, REQ-Q10
- **Depends on:** T-010, T-014
- **Plan:** PLAN-019 (to write)
- **TCs:** TC-212
- **Branch / PR:** `feat/T-019-usage-visibility`

## Goal
Full model-usage visibility.

## Scope
- In: per-call table (purpose, model, tokens + source label, latency, fresh/reused); session and page-level average response time; browser/test execution time shown separately; export of usage log for submission; rate-limit notes in SG-003.
- Out: —

## Acceptance criteria
- [ ] Averages correct (unit test); estimates labelled; reused calls excluded from latency averages or clearly separated

## Definition of Done
Standard (see [CLAUDE.md](../../CLAUDE.md)).

## Explain it (code-defense prep)
_To be written on completion._
