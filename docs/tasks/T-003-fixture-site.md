# T-003: Fixture site v1/v2

- **Status:** Done
- **Phase:** P1
- **Target:** W+0
- **Modules:** fixtures (outside the `gatp` package)
- **Requirements:** REQ-G9, REQ-P2-D1, REQ-P2-D2
- **Depends on:** T-002
- **Plan:** [PLAN-003](../implementationPlans/PLAN-003-fixture-site.md)
- **TCs:** TC-103 (Pass)
- **Docs:** [fixtures/README.md](../../fixtures/README.md), [SG-001 § Fixture site](../SystemGuides/SG-001-setup-and-run.md#fixture-site-bookshelf)
- **Session:** [S004](../sessions/2026-11-04-S004-full-build-run.md)
- **Branch / PR:** `claude/serene-johnson-xtbl4s` → squash-merged to `main`

## Goal
Our own small website and a modified version to develop and demo the full flow against before the instructor's site exists (ADR-009).

## Scope
- In: `fixtures/site-v1/` with ≥3 pages (login, form with validation, list/search) using a mix of labels, roles, test-ids and some poorly labelled elements; `fixtures/site-v2/` with **one clear locator change** and **one ambiguous change**; a local server script serving either version on a fixed port; `fixtures/README.md` listing intended behaviors and every v1→v2 change.
- Out: real backend logic beyond what pages need (simple JS is fine).

## Acceptance criteria
- [x] Both versions served with one command each (`uv run poe fixtures v1|v2`)
- [x] README documents expected behaviors (FX-1…FX-6, used as "requirements" in demos) and each change with its intended maintenance outcome (FXC-1 repair, FXC-2 clarification, FXC-3 no repair)

## Explain it (code-defense prep)

**What:**
- **The site:** "BookShelf", three static pages (sign-in, book list with search/filter, add-book form with validation) plus one `app.js`. Its state lives in `localStorage`.
- **Two versions:** `site-v1/` is the baseline. `site-v2/` is a full copy with three documented edits:
  - **FXC-1:** the sign-in button is renamed.
  - **FXC-2:** "Save" is split into "Save draft" and "Publish".
  - **FXC-3:** the footer version text changes.
- **The server:** `fixtures/serve.py` serves either version on `127.0.0.1:8090`.

**Why:**
- **Changes under our control:** the maintenance features (T-016/T-017) need a page that changes in a controlled way, with one case that has an obvious answer and one that doesn't. That's exactly what the brief's demo sequence asks for (REQ-P2-D1/D2).
- **Static on purpose:** there's no backend to explain, nothing to install, and every element is visible in the HTML that GATP inspects.
- **Two full copies:** rather than generating v2 from v1, we keep both trees in full, so `diff -r` *is* the change list. A test fails if anyone changes either version without updating the documented list.

**How it works:**
- **Sign-in:** `index.html` calls `initLogin()`. On submit it compares the input with the fixed account (`tester`/`secret123`). On a match it stores the user in `localStorage` and navigates to the list. Otherwise it writes the error into a `role="alert"` paragraph.
- **List:** `books.html` calls `initList()`, which redirects to sign-in when nobody is signed in. It renders the books from `localStorage` (seeded with 5 on first use) and re-renders on every search keystroke or genre change. The result count is in an `aria-live` region.
- **Add form:** `add.html` calls `initAdd()`. `validateBook()` returns one error per invalid field, and those appear in each field's `role="alert"` span. A valid book is appended and stored, and a one-time notice is saved so the list can show `Book "…" saved.`. In v2, `event.submitter.dataset.draft` tells the two buttons apart.
- **No caching:** `serve.py` subclasses `SimpleHTTPRequestHandler` and adds `Cache-Control: no-store`. Without it, stopping v1 and starting v2 on the same port could show cached v1 pages and break the rescan demo.

**Tests (TC-103):**
- `test_fixture_site.py` drives a real Chromium through FX-1…FX-6 and FXC-1/FXC-2.
- `test_fixture_server.py` checks version selection and the no-store header.
- `test_fixture_diff.py` diffs the two trees line by line and compares the result with the documented changes.

**Likely examiner questions:**
- *Why is FXC-1 "clear" but FXC-2 "ambiguous"?* After FXC-1 there is still exactly one submit button in the sign-in form, in the same place with the same role. Only its name and test-id changed, so one candidate clearly wins. After FXC-2 the old "Save" is gone and *two* new submit buttons sit in its place. Both could be what the test meant, so the right behavior is to ask the tester (REQ-Q4).
- *Why include badly labelled elements?* The inspector must rank locators and flag weak ones (ADR-006). The icon-only logout button and the placeholder-only Year input show that GATP warns instead of inventing a good locator.
- *Isn't localStorage a problem for repeatable tests?* Each Playwright browser context starts with empty storage, so every test starts from the 5 seed books.
- *How do you know v2 contains only the documented changes?* `test_fixture_diff.py` fails on any undocumented difference.
