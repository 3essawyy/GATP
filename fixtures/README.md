# Fixtures: BookShelf test website (v1 / v2)

Our own small website to develop and demo GATP against until the instructor's site is available ([ADR-009](../docs/architectureDecisionRecords/ADR-009-testing-strategy-and-fixture-site.md), [T-003](../docs/tasks/T-003-fixture-site.md)). Static HTML + vanilla JS; data lives in the browser's `localStorage` (5 seed books), so every reload of a fresh browser context starts clean.

```bash
uv run poe fixtures v1
```
```bash
uv run poe fixtures v2
```
Both serve on http://127.0.0.1:8090/ with `Cache-Control: no-store`, so you can stop v1 and start v2 on the same URL for the rescan demo.

## Pages
| Page | Purpose |
|---|---|
| `index.html` | Sign-in form |
| `books.html` | Book list with search, genre filter, "Add book" link, icon-only logout |
| `add.html` | Add-book form with client-side validation |

## Intended behaviors (use these as "requirements" in demos)
| ID | Behavior |
|---|---|
| FX-1 | Signing in with `tester` / `secret123` opens the book list, shows "Signed in as tester" and lists 5 books ("5 book(s)"). |
| FX-2 | Any other credentials show the alert "Invalid username or password." and stay on the sign-in page. Opening `books.html` or `add.html` while signed out redirects to sign-in. |
| FX-3 | Typing in the search box filters by title **or** author (case-insensitive) and updates the count; no match shows "No books match your search." |
| FX-4 | The genre drop-down filters the list to that genre ("Fiction" → 2 books). |
| FX-5 | Saving the add-book form validates: Title and Author required; Year a whole number between 1450 and the current year; Genre must be chosen. Each error appears under its field; the page does not change. |
| FX-6 | A valid book is saved, the list opens with the notice `Book "<title>" saved.` and the count increases by one. |

## Elements deliberately included for the inspector (ADR-006)
- **Good locators:** `data-testid` (`login-submit`, `book-search`, `add-book-link`, `save-book`), `<label for>` on Username/Password/Title/Author/Genre, roles (`alert`, `status`, `table` named "Books").
- **Poorly labelled:** the logout button is icon-only ("⎋", `title` only, no accessible label); the Year input has a placeholder but no label; the genre filter `<select>` has no label.

## v1 → v2 changes (complete list; checked by `backend/tests/test_fixture_diff.py`)
| ID | File | Change | Intended maintenance outcome |
|---|---|---|---|
| FXC-1 | `index.html` | Sign-in button: text "Sign in" → "Log in"; `data-testid="login-submit"` → `"login-button"`. Same position, still the only submit button in the form. | **Clear locator change → repair.** Exactly one strong candidate (same role/type/form/position); GATP should propose updating the locator with evidence, then rerun after approval. |
| FXC-2 | `add.html` | "Save" (`data-testid="save-book"`) replaced by **two** submit buttons: "Save draft" (`save-draft`, saves with a "Draft" badge) and "Publish" (`publish-book`, saves normally). | **Ambiguous → clarification.** Both buttons are plausible replacements (same form, same role, adjacent). GATP must ask the tester which one the test means and must not pick on its own. |
| FXC-3 | all pages | Footer text "· v1" → "· v2". | **No repair.** A text change on a non-interactive element; may be reported as a low-impact change. |

`app.js` and `style.css` are identical in both versions (the draft badge logic exists in v1 but is never triggered there).
