# PLAN-003: Fixture site v1/v2 (for T-003)

- **Task:** [T-003](../tasks/T-003-fixture-site.md)
- **Status:** Executed
- **Date:** 2026-11-04

## Approach
"BookShelf" is a three-page static site (plain HTML + vanilla JS + `localStorage`, no build step), so its behavior is obvious and every element is visible in the page source. `site-v1/` and `site-v2/` are **full copies**, not generated from each other. `diff -r fixtures/site-v1 fixtures/site-v2` shows exactly the changes, and a test asserts that the set of differing files and lines matches what `fixtures/README.md` documents.

`fixtures/serve.py` serves either version on `127.0.0.1:8090` with `Cache-Control: no-store`, so switching v1 → v2 on the same port never shows stale pages. It's wrapped as `uv run poe fixtures v1|v2`.

Elements deliberately cover the inspector's locator cases (ADR-006): `data-testid`, `<label for>`, ARIA roles/names, and **poorly labelled** elements (an icon-only button, a placeholder-only input, an unlabeled select).

## Changes v1 → v2 (also in fixtures/README.md)
| ID | Change | Expected maintenance outcome |
|---|---|---|
| FXC-1 | Login submit button: text "Sign in" → "Log in", `data-testid="login-submit"` → `"login-button"` (same element, the only submit button in the form) | **Clear repair**: a single strong candidate |
| FXC-2 | Add-book "Save" (`data-testid="save-book"`) replaced by two buttons, "Save draft" (`save-draft`) and "Publish" (`publish-book`); drafts show a "Draft" badge in the list | **Ambiguous**: two plausible candidates → clarification |

## Steps
1. `fixtures/site-v1/` (index.html login, books.html list/search, add.html form, app.js, style.css).
2. Copy to `site-v2/` and apply FXC-1 and FXC-2.
3. `fixtures/serve.py` + `poe fixtures` task; ruff/mypy cover `serve.py`.
4. Settings: optional `GATP_CHROMIUM_EXECUTABLE` for environments where Playwright's browser download is unavailable (this cloud sandbox).
5. Tests (TC-103): serve both versions in-process; drive with Playwright (headless in tests): login, search, validation, save; v2 differences; diff-equals-README check.
6. Docs: fixtures/README.md, SG-001 section, TC-103 status, task doc.

## Tests to add
| Test | Proves |
|---|---|
| `test_fixture_server.py` | Serves the requested version, no-store header, rejects unknown versions |
| `test_fixture_site.py` (Playwright) | Documented behaviors FX-1…FX-6 on v1; FXC-1/FXC-2 on v2 |
| `test_fixture_diff.py` | Files differing between v1 and v2 are exactly those listed in the README |

## Risks / open questions
| Item | Mitigation / decision |
|---|---|
| Playwright browser revision mismatch in the sandbox | `GATP_CHROMIUM_EXECUTABLE` override; CI uses the normal download |
| Browser tests slow CI | One shared browser per session (session-scoped fixture) |

## Deviations (filled after execution)
None.
