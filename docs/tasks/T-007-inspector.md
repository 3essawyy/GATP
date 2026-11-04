# T-007: Inspector — elements, attributes, ranked locators, uniqueness, fingerprints

- **Status:** Done
- **Phase:** P1
- **Target:** W+1
- **Modules:** inspector, runner, store, api (converter)
- **Requirements:** REQ-P1-2, REQ-Q1
- **Depends on:** T-006
- **Plan:** [PLAN-007](../implementationPlans/PLAN-007-inspector.md)
- **ADRs:** [ADR-018](../decisions/ADR-018-inspection-setup-and-usability.md)
- **TCs:** TC-108 (Pass), TC-107 (automated part)
- **Evidence:** [docs/samples/](../samples/README.md)
- **Session:** [S004](../sessions/2026-11-04-S004-full-build-run.md)
- **Branch / PR:** `claude/serene-johnson-xtbl4s` → squash-merged to `main`

## Goal
Produce the InspectionSnapshot described in the [inspector LLD](../modules/inspector/README.md) per ADR-006.

## Scope
- In: interactive-element detection; role/accessible name/label/attributes/text/dom path/bbox/nearby text; locator candidates in priority order with live counts and `usable`; fingerprint; full-page screenshot; scope include/exclude; persistence via store.
- Out: shadow DOM/iframes (documented limitation).

## Acceptance criteria
- [x] On fixture site v1, every interactive element found (checked against fixture README): 3 on sign-in, 4 on the book list, 7 on add-book (`test_inspector.py`)
- [x] Non-unique locators marked unusable; elements without unique locator flagged (duplicate-button page test)
- [x] Sample snapshot JSON saved for the Phase 1 submission (`docs/samples/`)

## Explain it (code-defense prep)

**What.** Given a page the runner has opened, the inspector lists every interactive element. For each one it records what was observed (tag, role, accessible name, label, attributes, position, nearby text, line in the served HTML) and a ranked list of Playwright locators. Each locator is **tested on the live page**, and the best one that's provably correct becomes the default. Elements without a safe locator, a name or a visible label are flagged.

**Why:**
- **Grounding:** everything later in GATP (test design, code generation, maintenance) must be grounded in what was actually on the page (REQ-P1-2).
- **Proven locators:** locators must be validated, including uniqueness (REQ-Q1), so a locator can never come from the model or from guesswork, only from this verified list.

**How it works:**
1. **Extraction:** `page.evaluate(extract.js)` runs a read-only script in the page. It selects interactive elements (links, buttons, form fields, interactive ARIA roles, click handlers, focusable elements). For each it computes the role (an explicit `role` or the implicit one, e.g. `<select>` → combobox) and an accessible name (aria-labelledby → aria-label → `<label>` → title → placeholder, or the text for buttons/links). It also collects attributes, a DOM path, the bounding box and nearby text, and keeps the elements in `window.__gatpEls`.
2. **Candidates:** `candidate_specs()` builds candidates in Playwright's recommended order: role+name, label, test id, placeholder, short text, CSS `#id`, CSS `[name]`, then a positional DOM path.
3. **Verification:** `verify()` resolves each candidate with Playwright and counts its matches. If exactly one, it asks the page whether that match **is** element *i*. Only then is the candidate `usable`. So if our name computation is ever wrong, the role locator simply shows as unusable (e.g. count 0) instead of pointing at the wrong thing.
4. **Default and flags:** the default is the first usable non-positional candidate. With none, the element is flagged `no_unique_locator` and must be clarified by the tester. Other flags: `no_accessible_name`, `weak_accessible_name` (e.g. "⎋"), `no_visible_label` (placeholder-only fields), `hidden`, `disabled`.
5. **Fingerprints:** each element's fingerprint (role, name, label, test id, form, position, nearby text, …) is what maintenance compares after a rescan.
6. **In the runner:** the `inspect` job first runs tester-approved setup steps (e.g. sign in), so protected pages can be inspected. It reports client-side redirects and saves a full-page screenshot plus the served HTML. That HTML gives `source_line`, the "linked to source" evidence.

**Likely examiner questions:**
- *How do you know the chosen locator is right?* It was executed on the live page: it matched exactly one element, and the page confirmed that element is the inspected one. Both facts are stored as evidence (count, `targets_element`).
- *What happens with two identical "Delete" buttons?* `get_by_role("button", name="Delete")` counts 2, so it's unusable. Only a positional CSS path is unique, and that's never chosen automatically, so the element is flagged and GATP will ask the tester (REQ-Q1).
- *Does inspection change the page?* No. The extraction script only reads the DOM. Setup steps (fill, click) run only when the tester configured and approved them.
- *What isn't covered?* Shadow DOM, iframes, and elements that appear only after interaction (unless setup steps open them). These are documented limitations.
- *Where is "linked to source"?* Each element has `source_line` (the line of its start tag in the served HTML, which is stored as a file) and a bbox for highlighting on the screenshot.
