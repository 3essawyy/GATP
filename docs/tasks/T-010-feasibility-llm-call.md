# T-010: Grounded LLM summary / next action + usage display

- **Status:** Todo
- **Phase:** P1
- **Target:** W+2
- **Modules:** llm-gateway, api, web-ui
- **Requirements:** REQ-P1-4, REQ-P1-D, REQ-Q7, REQ-Q8, REQ-Q9
- **Depends on:** T-005, T-009
- **Plan:** PLAN-010 (to write)
- **TCs:** TC-111
- **Branch / PR:** `feat/T-010-feasibility-call`

## Goal
The graded Phase 1 model call: summarize selected elements or suggest a next testing action, grounded in the snapshot, with usage evidence.

## Scope
- In: prompt template; output schema citing element IDs (rejected if unknown); UI panel showing result + model, version, tokens (provider/estimated), latency, fresh/reused; usage evidence export for submission.
- Out: test case generation (T-012).

## Acceptance criteria
- [ ] Every element referenced in the response exists in the snapshot
- [ ] Usage metrics visible and logged; model time shown separately from inspection time

## Definition of Done
Standard (see [CLAUDE.md](../../CLAUDE.md)).

## Explain it (code-defense prep)
_To be written on completion._
