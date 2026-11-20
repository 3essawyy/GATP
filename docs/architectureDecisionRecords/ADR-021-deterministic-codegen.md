# ADR-021: Deterministic code generation, validation report bound to versions, setup steps in page objects

- **Status:** Accepted (supersedes the Monaco part of [ADR-013](ADR-013-frontend-libraries.md))
- **Date:** 2026-11-04
- **Session:** S004
- **Related:** REQ-P2-2, REQ-Q1, REQ-Q3, REQ-Q6, T-013, TC-203, TC-204; builds on [ADR-008](ADR-008-generated-tests-python-pom.md), [ADR-018](ADR-018-inspection-setup-and-usability.md), [ADR-020](ADR-020-test-plan-contract.md)

## Context
ADR-008 left the LLM-vs-template split to PLAN-013. The approved plan (ADR-020) already holds every step and expectation as data that cites verified elements. Running the first generated test for real showed that pages behind a sign-in need the inspection's setup steps in the test too.

## Decision
- **Split: 0 % model, 100 % templates.** The model's work ends with the approved plan. `codegen/render.py` deterministically renders:
  - `pages/<page>_page.py`: one class per page, holding only the verified default locators of cited elements. Its `open()` replays the page's tester-approved **setup steps** (ADR-018), then navigates.
  - `tests/test_plan.py`: one `test_tc_NN_*` per case. Its docstring lists each expectation's id and basis, and each assertion is commented with its id.
  - `conftest.py`: `base_url` (`GATP_BASE_URL`) and browser launch args (headed unless `GATP_HEADLESS=1`; optional Chromium path).
  Versions are authored `generator` and record the plan version they came from.
- **Validation before G2:**
  1. **Static:** syntax; every locator call in page objects equals a verified snapshot candidate or an approved setup-step locator; tests may not create locators; restricted imports and calls (no `subprocess`, `eval`, `open`, `os.system`, …).
  2. **Live recount** in the runner, per page and with the page's setup steps: every snapshot locator must match exactly 1.
  3. **`pytest --collect-only`** in a fresh runner sandbox with a scrubbed environment (new typed `collect` job).
- **Reports** are stored with the exact code version ids they cover. **G2 requires a passing report for that version.** Any edit creates a new version, which the old report doesn't cover.
- **Editor:** a plain monospace editor replaces Monaco. `@monaco-editor/react` loads Monaco from a CDN by default, which breaks local/offline use, and bundling Monaco adds significant weight. Diffs use GATP's own side-by-side rows (T-018).

## Alternatives considered
| Option | Why not |
|---|---|
| Model writes the Python code | Agreed against in S004: invented locators and syntax errors would be caught only after the fact |
| Recount setup-step locators on the target page | They act on other pages (sign-in); their successful execution during inspection is the evidence |
| Monaco bundled locally | Heavy worker setup for a feature a textarea covers; can be revisited |

## Consequences
- Every assertion in code traces to an approved expectation, and every locator to inspection evidence or an approved setup step.
- `collect` imports the test modules. Static safety checks run first and the sandbox environment is scrubbed; stronger confinement (bubblewrap) comes with execution (T-014/T-020).
