# ADR-023: Feedback from runs drives plan revisions; weakened checks always need an explicit decision

- **Status:** Accepted
- **Date:** 2026-11-04
- **Session:** S004
- **Related:** REQ-P2-3, REQ-P2-D1, REQ-Q3, T-015, TC-207; builds on [ADR-020](ADR-020-test-plan-contract.md), [ADR-022](ADR-022-approved-execution-sandbox.md)

## Context
After a run, the tester must be able to give feedback, have the case and/or code revised and rerun with approval. The brief forbids weakening assertions or changing test intent just to make a test pass. A model asked to "fix" a failing test may simply remove or loosen the failing check.

## Decision
- **Feedback path:** the Run page sends free-text feedback plus the run id to `POST /plan/propose {feedback, run_id, test_ids}`.
  - The API adds the run's failures to the model's **untrusted page data** (`run_results`): test id, outcome, message (page text, so data) and the **failing expectation ids**.
  - Failing ids are recovered from the stack: generated assertions end with `# <expectation id> [basis]` and pytest marks the failing line with `>`.
  - The revision is a new plan version (author `model`, reason "revised by model from run #N: …").
- **Guard against the last approved version.** The baseline is the newest **G1-approved** plan version (for code: the newest **G2-approved** version of each `tests/` file). Before the first approval, nothing is guarded.
  - **Plan:** an expected result removed, its kind/element/value changed (classified as *loosened* for known weaker pairs, otherwise *changed*), or a whole case removed. The same check under a new id is not a weakening.
  - **Code (tester edits):** a test function removed, an `expect(...)`/`assert` no longer present, or a test newly skipped / xfail. Generated files follow the G1-approved plan and are guarded at plan level.
- **Each finding becomes a clarification** of kind `weakening` on step `plan` or `code`.
  - It blocks G1/G2, like every open clarification.
  - It has exactly two answers: **Accept this change** (recorded with the tester's name and time) or **Restore the approved version**.
    - Plan: the approved check or case goes back, with its confirmation.
    - Code: the approved file comes back as a new version.
  - Free-text answers are refused (422), so nobody can wave a weakening through with "ok".
  - Findings that disappear (undone, or a new version approved) are resolved as superseded. Accepted findings are not asked again.
- **The rerun goes through the normal gates:** G1 for the revised plan, regenerate, validate, G2, then a **new G3** (ADR-022: one run per approval).

## Alternatives considered
| Option | Why not |
|---|---|
| Forbid the model from removing checks | Sometimes the check *is* wrong (FXC-2 style ambiguity); the tester must be able to decide |
| Diff shown, no blocking | "Never silent" needs a recorded decision, not just a visible diff |
| Compare with the previous version instead of the approved one | A chain of small edits could weaken step by step; the approved version is what the tester signed |

## Consequences
- **Revisions that only remove checks:** the offline (fake) provider's revision removes the failing checks, because no model is available. The demo therefore shows the guard firing, and the plan notes say so.
- **Steps are not guarded:** changes to test steps (e.g. removing a click) are not classified as weakening. They are visible in the new version and need G1. This is noted in SG-006.
