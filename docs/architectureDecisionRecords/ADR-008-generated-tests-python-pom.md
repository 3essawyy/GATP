# ADR-008: Generated tests — Python, pytest-playwright, Page Object Model

- **Status:** Accepted
- **Date:** 2026-11-04
- **Session:** S001
- **Related:** REQ-P2-2, REQ-P2-3, REQ-Q3; modules codegen, runner

## Context
Generated tests must be executable Playwright tests using POM, syntax-validated, locator-verified, and reviewable.

## Decision
- Generated tests use **Python + pytest-playwright**.
- Structure per project: `pages/<page>_page.py` (page objects: locators + actions) and `tests/test_<feature>.py` (test functions using page objects and `expect` assertions).
- Each test function maps to one approved test case ID; the case ID appears in the docstring for traceability.
- Validation before G2: Python `ast` parse, locator verification against the snapshot, pytest `--collect-only` in the runner.
- Assertions come from approved expected results; they are never weakened to obtain a pass.

## Alternatives considered
| Option | Why not |
|---|---|
| TypeScript @playwright/test | Adds Node toolchain to the runner; Python keeps one language |

## Consequences
- Runner needs pytest + pytest-playwright installed in its environment.
- Generation is template-guided: the LLM fills structured content (steps, assertions) and code is rendered from it where practical to keep output valid. Exact split decided in PLAN-013.
