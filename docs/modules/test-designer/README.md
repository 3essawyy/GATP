# Module: test-designer

- **Owner:** TBD
- **Status:** Planned
- **Code:** `backend/gatp/test_designer/`
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

## Known limitations
TBD.
