# Module: codegen

- **Owner:** TBD
- **Status:** Planned
- **Code:** `backend/src/gatp/codegen/`
- **Tasks:** T-013
- **ADRs:** ADR-006, ADR-008

## Responsibility
Turns an **approved** test plan version into pytest-playwright code using the Page Object Model, then validates it before it can be approved for execution (G2).

## Output layout
```
pages/<page>_page.py      # class with locators (from snapshot only) + action methods
tests/test_<feature>.py   # one test function per approved case_id, docstring cites case_id
conftest.py               # base URL from approved target
```

## Validation pipeline
1. `ast.parse` every file (syntax).
2. Locator check: every locator in page objects must equal a snapshot locator with `usable=true`; otherwise flag.
3. Re-count locators on the live page via runner before execution (stale-snapshot guard).
4. `pytest --collect-only` in the runner sandbox.
Validation report is stored with the code version and shown in review.

## Known limitations
LLM-vs-template split decided in PLAN-013.
