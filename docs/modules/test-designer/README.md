# Module: test-designer

- **Owner:** TBD
- **Status:** Implemented (insight T-010, test plans T-012)
- **Code:** `backend/src/gatp/test_designer/`
- **Tasks:** T-012
- **ADRs:** ADR-003, ADR-020, ADR-006

## Responsibility
Proposes test cases grounded in the selected snapshot elements and the tester's goal/requirements. Separates **observations** (from the page) from **assumptions** (business rules), and raises clarification requests where expected behavior can't be established. Produces a versioned `test_plan` artifact for G1 approval.

## Test plan (T-012, [ADR-020](../../architectureDecisionRecords/ADR-020-test-plan-contract.md))
`plan.py`: the `TestPlan` / `TestCase` / `PlanStep` / `Expectation` schema, template `test_plan` v1, `validate_plan()`, `normalise()` (stable expectation ids, confirmation rules), `propose_plan()` (proposal, or revision with feedback), and the offline example used by the `fake` provider.

```json
{"id": "TC-01", "title": "Title is required", "priority": "high",
 "steps": [{"action": "goto", "value": "http://127.0.0.1:8090/add.html"},
           {"action": "fill", "element_id": "s2.e3", "value": "Frank Herbert"},
           {"action": "click", "element_id": "s2.e6"}],
 "expected": [{"id": "TC-01.x1", "kind": "text_equals", "element_id": "s2.o2",
               "value": "Title is required.", "basis": "requirement",
               "evidence": "FX-5: Title required", "confirmed": false}],
 "open_questions": []}
```

**Lifecycle (api `plan_service.py`):**
1. Propose: `POST /api/projects/{id}/plan/propose` (requires G0) stores a `test_plan` version with `author=model`.
2. Clarifications are synced: one per unconfirmed assumption (options *Confirm* / *Remove this expectation* / a corrected value) and one per open question. Both block G1.
3. Each answer creates a new version (`author=user`).
4. Tester edits go through `PUT /plan`, are validated, and create a new version.
5. Revise with feedback: `POST /plan/propose {feedback}`.
6. G1 approval requires no open clarifications and no unconfirmed assumptions.

## Revisions from run feedback and the weakening guard (T-015, [ADR-023](../../architectureDecisionRecords/ADR-023-feedback-and-weakening-guard.md))
- `propose_plan(..., run_results=…)`: a run's failures (test id, message, failing expectation ids) go to the model as **untrusted page data**. The template tells it to correct checks, not drop them.
- `guard.py`: `plan_weakenings(approved, revised)` → removed / loosened / changed expectations and removed cases, compared with the last **G1-approved** version. `restore()` puts the approved check or case back.
- Offline (fake provider) revision drops the failing checks and says so in `notes`. It exists to demonstrate the guard.

## Implemented so far: Phase 1 insight (T-010)
`insight.py`: template `insight` v1; `Insight` schema (summary, element notes, next actions with `basis: observed | assumption`, assumptions, questions); `scoped_elements(scope, snapshots)` applies the approved scope's include/exclude and builds untrusted element records with qualified ids `s<snapshot>.e<n>`; `check_ids()` rejects ids that were not sent; `request_insight()` calls the gateway. Exposed by `POST /api/projects/{id}/insight` (requires G0). Tests: `test_api_insight.py`.

## Known limitations
- Plan quality depends on the model; the offline example plan only demonstrates the flow.
- Test data values are chosen by the model or the tester; only expected results need a basis.
