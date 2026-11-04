# T-014: Approved execution, results, screenshots (G3)

- **Status:** Todo
- **Phase:** P2
- **Target:** W+4
- **Modules:** runner, api, web-ui
- **Requirements:** REQ-P2-3, REQ-G5, REQ-Q3, REQ-Q5, REQ-Q6, REQ-Q8
- **Depends on:** T-013
- **Plan:** PLAN-014 (to write)
- **TCs:** TC-205, TC-206
- **Branch / PR:** `feat/T-014-execution`

## Goal
Run exactly the approved code version in the isolated runner with a visible browser and show reviewable results.

## Scope
- In: G3 approval screen (tests, target, limits); `run_tests` job; per-test status, duration, error message, stack excerpt, screenshot on failure (and final); live progress via SSE; results UI; execution time separate from model time.
- Out: feedback loop (T-015).

## Acceptance criteria
- [ ] Execution refused without G3 approval on the exact version
- [ ] A deliberately failing case shows its real failure (not hidden)

## Definition of Done
Standard (see [CLAUDE.md](../../CLAUDE.md)).

## Explain it (code-defense prep)
_To be written on completion._
