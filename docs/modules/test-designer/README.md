# Module: test-designer

- **Owner:** TBD
- **Status:** In progress (Phase 1 insight call, T-010)
- **Code:** `backend/src/gatp/test_designer/`
- **Tasks:** T-012
- **ADRs:** ADR-003, ADR-006

## Responsibility
Proposes test cases grounded in the selected snapshot elements and the tester's goal/requirements. Separates **observations** (from the page) from **assumptions** (business rules), and raises clarification requests where expected behavior can't be established. Produces a versioned `test_plan` artifact for G1 approval.

## Test case shape (draft)
```json
{
  "case_id": "TC-LOGIN-01", "title": "…", "priority": "high",
  "preconditions": ["…"],
  "steps": [{"action": "fill", "element_id": "E-0003", "value": "user@example.com"}],
  "expected": [{"assertion": "url_contains", "value": "/dashboard",
                "basis": "requirement|observation|assumption", "evidence": "REQ note / E-id"}],
  "open_questions": ["…"]
}
```
Any `element_id` not in the snapshot → rejected and regenerated or flagged. Any expected result with `basis=assumption` must be confirmed by the tester before G1.

## Implemented so far: Phase 1 insight (T-010)
`insight.py`: template `insight` v1; `Insight` schema (summary, element notes, next actions with `basis: observed | assumption`, assumptions, questions); `scoped_elements(scope, snapshots)` applies the approved scope's include/exclude and builds untrusted element records with qualified ids `s<snapshot>.e<n>`; `check_ids()` rejects ids that were not sent; `request_insight()` calls the gateway. Exposed by `POST /api/projects/{id}/insight` (requires G0). Tests: `test_api_insight.py`.

## Known limitations
TBD.
