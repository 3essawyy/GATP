# T-015: Feedback → revise → approved rerun

- **Status:** Todo
- **Phase:** P2
- **Target:** W+4
- **Modules:** api, test-designer, codegen, web-ui
- **Requirements:** REQ-P2-3, REQ-P2-D1, REQ-Q3
- **Depends on:** T-014
- **Plan:** PLAN-015 (to write)
- **TCs:** TC-207
- **Branch / PR:** `feat/T-015-feedback-rerun`

## Goal
Tester feedback on results drives a revision (case and/or code) and an approved rerun, without weakening intent.

## Scope
- In: feedback on a run/test; revision proposal (new versions, diff shown); guard that flags assertion weakening for explicit tester confirmation; re-approval (G1/G2 as needed) and G3 rerun.
- Out: maintenance repairs (T-017).

## Acceptance criteria
- [ ] Demo step "provide feedback; revise and rerun" works end to end
- [ ] Revisions that remove/loosen assertions are flagged, never silent

## Definition of Done
Standard (see [CLAUDE.md](../../CLAUDE.md)).

## Explain it (code-defense prep)
_To be written on completion._
