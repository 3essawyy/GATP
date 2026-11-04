# PLAN-015: Feedback → revise → approved rerun (for T-015)

- **Task:** [T-015](../tasks/T-015-feedback-rerun.md)
- **Status:** Executed
- **Date:** 2026-11-04

## Approach
[ADR-023](../decisions/ADR-023-feedback-and-weakening-guard.md): run failures (with failing expectation ids) feed a model revision as untrusted data. A guard compares every new plan / edited test file with its last approved version and raises `weakening` clarifications (Accept / Restore) that block the gate. The rerun reuses G1 → generate → validate → G2 → new G3.

## Steps
1. `test_designer/guard.py` (plan findings + restore), `codegen/guard.py` (AST per test function).
2. `api/guard_sync.py` (raise / supersede / accepted keys, approved baseline). Hooks in `plan_service.store_plan`, `store_confirmed`, generic artifact edit/restore (`code_service.on_artifact_changed`) and after generate; answers through `apply_answer` / `apply_code_answer`; free text refused.
3. `run_service.failed_expectations`. `POST /plan/propose` accepts `run_id`, `test_ids`, and `propose_plan(run_results=…)` passes them in. Offline revision for the fake provider.
4. UI: run feedback box, "failed at TC-…" badges, weakening banners (two buttons, no free text), plan notes.
5. Tests, walkthrough screens 16–18, smoke.

## Tests to add
| Test | Proves |
|---|---|
| `test_feedback.py::test_feedback_on_failed_run_revises_and_reruns` | The demo step end to end. The failure maps to `TC-01.x1`, run results go to the model as page data, the changed check is flagged, "ok" is refused, Accept → G1 → G2 → new G3 → passed |
| `…::test_removed_check_is_flagged_and_can_be_restored` | A tester edit that drops a check is flagged; Restore brings it back confirmed |
| `…::test_weakened_test_code_is_flagged_before_g2` | Removing an `expect` from the test file blocks G2; Restore brings back the approved file |
| `…::test_guard_units` | Loosened vs changed, same check under a new id, case removal + restore, skip markers, failing-line parsing, offline revision |

## Deviations (filled after execution)
- Found while reviewing the walkthrough screenshots: the model's plan notes (where it explains removals) weren't shown. Added a "Model notes" alert on the Plan page.
- Found in CI on T-014's PR: inside the sandbox Playwright looked for browsers under the sandbox HOME. Fixed in T-014 (`PLAYWRIGHT_BROWSERS_PATH`).
