# Module: inspector

- **Owner:** TBD
- **Status:** Implemented (T-007)
- **Code:** `backend/src/gatp/inspector/` (runs **inside the runner process**)
- **Tasks:** T-007
- **ADRs:** ADR-004, ADR-006, ADR-007

## Responsibility
Given an open page (supplied by the runner), extract every interactive element with its observed labels and attributes, generate ranked candidate locators, count each on the live page, compute an element fingerprint, and return an `InspectionSnapshot` (plus a full-page screenshot). It never interprets page text as instructions.

## Locator specs (implemented in T-006)
`inspector/locators.py`: `LocatorSpec(strategy, value, name, exact)` with strategies `role` > `label` > `test_id` > `placeholder` > `text` > `css` (`STRATEGY_RANK`, ADR-006). `resolve(page, spec)` builds the Playwright locator; `spec.to_python("self.page")` renders the expression shown to users and used in generated page objects. Locators travel as this data, never as code strings.

## Output: `InspectionResult` (`inspector/models.py`)
Real example: [docs/samples/inspection-bookshelf-v1-add-book.json](../../samples/inspection-bookshelf-v1-add-book.json) (+ `.png`).

| Field | Meaning |
|---|---|
| `url` / `final_url` / `title` | Requested URL, URL after client-side redirects, page title |
| `scope` | `include`/`exclude` CSS container selectors used |
| `html_sha256` | Hash of the served HTML (the HTML itself is a job file `html`) |
| `elements[]` | One `InspectedElement` per interactive element, below |

`InspectedElement`:

| Field | Meaning |
|---|---|
| `key` | `e1`, `e2`, … in document order (stable within the snapshot) |
| `tag`, `role`, `name`, `text`, `label` | Observed tag, implicit/explicit ARIA role, computed accessible name, visible text, `<label>` text |
| `attributes` | Whitelisted attributes (`id`, `name`, `type`, `data-testid`, `placeholder`, `href`, `aria-*`, `title`, …) |
| `dom_path` | Structural CSS path (stops at the nearest `#id`) |
| `bbox` | Page coordinates for the screenshot highlight |
| `visible`, `enabled`, `nearby_text`, `form`, `index_in_form` | Context used as evidence and in fingerprints |
| `source_line` | Line of the start tag in the served HTML; `null` if the element was created by script |
| `locators[]` | Candidates in ADR-006 order, each with `spec`, `expression`, live `count`, `targets_element`, `usable`, `positional` |
| `default_locator` | Index of the best usable **non-positional** candidate, or `null` |
| `flags` | `no_unique_locator`, `no_accessible_name`, `weak_accessible_name`, `no_visible_label`, `hidden`, `disabled` |
| `fingerprint` | Tag, role, name, text, label, type, id, name attr, test id, placeholder, href, form, index in form, nearby text, DOM path, centre point (input to maintenance, T-016) |

## Algorithm
1. **Extract (in page, read-only):** `extract.js` selects interactive elements: links, buttons, inputs (not hidden), selects, textareas, `summary`, interactive ARIA roles, `[onclick]`, positive `tabindex`, `contenteditable`. Include/exclude scope filters are applied. For each element it computes the implicit role and a simplified accessible name (aria-labelledby → aria-label → `<label>` → button value → title → placeholder; text content for buttons/links), plus attributes, DOM path, bbox, visibility and nearby text. The elements stay in `window.__gatpEls`.
2. **Candidates:** `candidate_specs()` builds candidates in order: role+name, label (or aria-label), test id, placeholder, text (short link/button text only), CSS `#id`, CSS `tag[name=…]`, then the positional DOM path. Duplicates are dropped.
3. **Verify live:** each candidate is resolved with Playwright and `count()`ed. If the count is 1, `locator.evaluate(el => el === window.__gatpEls[i])` proves that it targets **this** element. `usable = count == 1 and targets_element`. An incorrectly computed accessible name therefore produces an *unusable* candidate, never a wrong one.
4. **Default + flags:** the default is the first usable non-positional candidate. With none, the element is flagged `no_unique_locator` and the tester must clarify before it's used (ADR-006).
5. **Source lines:** each start tag (without its closing `>`/`/>`) is searched for in the served HTML that the runner fetched for the final URL.

## Runner integration
The runner's `inspect` job runs optional tester-approved **setup steps** (`goto`, `fill`, `click`, `select` with `LocatorSpec`; `goto` URLs must be allowlisted), opens the URL, waits for client-side redirects, rejects redirects outside the allowlist, fetches the served HTML, calls `inspect_page()`, and keeps `page.png` (full page) + `page.html` as job files. The api turns the result into a store snapshot with `gatp.api.inspections.to_snapshot_in()` (details, specs and `targets_element` are persisted; migration `0003`).

## Tests
`test_inspector.py` (TC-108 and the automated part of TC-107): exact element lists and best locators on all three BookShelf pages, source lines, flags for poorly labelled elements, sign-in via setup steps, redirect reporting, scope include/exclude, duplicate buttons/labels → unusable + `no_unique_locator`, persistence round trip.

## Known limitations
- Shadow DOM and iframes are not traversed (their contents are not listed).
- The accessible name is a simplified computation; the live check makes mistakes harmless (they show as unusable candidates) but can cause a good role locator to be missed.
- Elements created after interactions (menus, dialogs) are only seen if the setup steps open them first.
- `source_line` is `null` for script-generated elements (e.g. table rows).
