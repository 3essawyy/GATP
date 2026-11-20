# Module: codegen

- **Owner:** TBD
- **Status:** Implemented (T-013)
- **Code:** `backend/src/gatp/codegen/`
- **Tasks:** T-013
- **ADRs:** ADR-006, ADR-008

## Responsibility
Turns an **approved** test plan version into pytest-playwright code using the Page Object Model, then validates it before it can be approved for execution (G2).

## Output layout ([ADR-021](../../architectureDecisionRecords/ADR-021-deterministic-codegen.md))
```
pages/<page>_page.py   # class: PATH, verified locators of cited elements, open() = setup steps + goto
tests/test_plan.py     # one test_tc_NN_* per approved case; docstring/comments cite expectation ids + basis
conftest.py            # base_url (GATP_BASE_URL), browser launch args (headed unless GATP_HEADLESS=1)
```
Example (from the fixture site): `self.title_error_alert = page.locator("#title-error")` and `expect(add_page.title_error_alert).to_have_text('Title is required.')  # TC-01.x1 [requirement]`.

## Files
| File | Contents |
|---|---|
| `render.py` | `render(plan, elements, origin, plan_number, plan_version_id, setups)` → `GeneratedFile`s; mapping of step actions and expectation kinds to Playwright calls |
| `validate.py` | `validate(files, allowed_locators)` → `StaticReport` (syntax, locator, structure, safety findings) |
| api `code_service.py` | `generate`, `run_validation` (static + runner `recount` + runner `collect`), `latest_report_for_current` |

## Validation pipeline
1. `ast.parse` every file.
2. Every `page.get_by_*(…)` / `page.locator(…)` in page objects must equal a verified (usable, non-positional) candidate of a scoped element or an approved setup-step locator. Tests may not create locators.
3. Safety: imports limited to `re`, `os` (environ only), `pytest`, `playwright.sync_api`, `pages`; no `eval`/`exec`/`open`/`subprocess`/`os.system`/`page.evaluate`/`route`.
4. Live recount in the runner (with each page's setup steps): every snapshot locator must count exactly 1.
5. `pytest --collect-only` in the runner sandbox (`collect` job).

The report is stored with the exact code version ids (`validation_reports`, migration `0006`). G2 needs a passing report for the version being approved.

## Weakening guard for test edits (T-015, [ADR-023](../../architectureDecisionRecords/ADR-023-feedback-and-weakening-guard.md))
`guard.py`: `code_weakenings(path, approved, edited)` compares each test function with the last G2-approved version of the file: function removed, `expect(...)`/`assert` gone or changed, newly skipped/xfail. The API turns findings into `weakening` clarifications on step `code` (Accept / Restore the approved file), which block G2.

## Tests
`test_codegen.py`: G1 required; generated files and content; validation (static, recount, collect) passes; G2 only after validation; edit → new version, approval and report no longer apply; injected invented locator caught and blocks G2; static unit checks; **generated test really runs and passes against fixture v1**.

## Known limitations
- One test file per plan (all cases); page objects expose locators, not higher-level action methods.
- `collect` imports test modules (after static safety checks) in a process sandbox (scrubbed environment, sandbox working directory). Bubblewrap is used for approved test runs (`run_tests`), not for `collect`.
