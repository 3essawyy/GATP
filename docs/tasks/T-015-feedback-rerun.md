# T-015: Feedback → revise → approved rerun

- **Status:** Done
- **Phase:** P2
- **Target:** W+4
- **Modules:** api, test-designer, codegen, web-ui
- **Requirements:** REQ-P2-3, REQ-P2-D1, REQ-Q3
- **Depends on:** T-014
- **Plan:** [PLAN-015](../implementationPlans/PLAN-015-feedback-rerun.md)
- **ADRs:** [ADR-023](../decisions/ADR-023-feedback-and-weakening-guard.md)
- **TCs:** TC-207 Pass
- **Session:** [S004](../sessions/2026-11-04-S004-full-build-run.md)

## Goal
Tester feedback on results drives a revision (case and/or code) and an approved rerun, without weakening intent.

## Acceptance criteria
- [x] Demo step "provide feedback; revise and rerun" works end to end (UI walkthrough screens 16–18; `test_feedback_on_failed_run_revises_and_reruns`)
- [x] Revisions that remove or loosen assertions are flagged, never silent: an Accept/Restore decision blocks G1/G2, and free text is refused

## Verification (real system)
- **Walkthrough on the real UI, runner and bwrap sandbox:**
  - Run #1 fails 0/2, with badges "failed at TC-01.x2 / TC-02.x2".
  - Feedback → revision v5 by the model.
  - Two orange "Weakened check" decisions; G1 disabled; model notes explain the removals.
  - Accept both → G1 → regenerate → validate → G2 → new G3 → run #2 **passed 2/2**, and the step shows done.
- **Found and fixed:**
  - The Plan page didn't show the model's notes, so the reason for a removal was invisible. Added the "Model notes" alert.
  - CI on T-014: Playwright looked for browsers under the sandbox HOME. Fixed in T-014 with an explicit `PLAYWRIGHT_BROWSERS_PATH`.
- **Tests:** `test_feedback.py` covers model revision from a run, tester plan edit + Restore, test-code edit + Restore, and units.

## Explain it (code-defense prep)
**What.** After a run, the tester writes what is wrong. GATP sends the feedback and the failures to the model, which proposes a revised plan (a new version).
- If the revision removes, loosens or changes a check that the tester approved, GATP raises a "weakened check" decision. The tester must **Accept** it or **Restore** the approved check.
- The same applies when the tester edits a test file and drops an `expect`, or adds `skip`.
- The rerun needs G1, G2 and a new G3 again.

**Why.**
- REQ-P2-3 / the demo sequence require "provide feedback; revise and rerun".
- REQ-Q3 and the brief require that assertions are never weakened and intent never changed just to make a test pass. A model asked to fix a failing test is tempted to delete the failing check, so a human must see and decide on every such change.

**How it works:**
1. **Failure → expectation.** Generated assertion lines end with `# TC-01.x2 [basis]`. Pytest marks the failing line with `>`, so `failed_expectations()` finds which expected result failed.
2. **Revision.** `POST /plan/propose {feedback, run_id}` puts the run's failures into the page data (untrusted: the messages contain page text) and asks for a revision. The result is a new plan version.
3. **Guard.** `plan_weakenings(approved, revised)` compares with the newest **G1-approved** version, not just the previous one, so step-by-step weakening can't slip through. `code_weakenings` does the same per test function against the newest **G2-approved** file.
4. **Decision.** Each finding is a `weakening` clarification on step plan/code, which blocks the gate. Answers are only Accept (recorded with name and time) or Restore (new version with the approved check/file back). Undone findings become superseded.
5. **Rerun.** G1 → regenerate (deterministic) → validate → G2 → new G3 (one run per approval) → run.

**Likely examiner questions:**
- *Can the model make a failing test pass by deleting the assertion?* It can propose that, but GATP flags every removed or changed check compared with the approved plan, and G1 is blocked until a named tester accepts or restores it. "ok" isn't accepted as an answer.
- *What if the tester edits the code directly?* Same guard on `tests/` files against the approved version: removed asserts, removed tests and new skip/xfail are flagged before G2.
- *Why compare against the approved version and not the previous one?* The tester signed the approved version. Comparing with the previous version would let several small edits weaken a test without anyone seeing the total.
- *Why did the offline demo remove the checks?* With the fake provider there is no model. Its revision deliberately drops the failing checks to show the guard. The notes say this, and a real model is told to correct checks instead.
- *Is a real bug distinguishable from a wrong test?* That's the tester's call. The feedback box says so, and keeping the test (not revising) is always possible.
