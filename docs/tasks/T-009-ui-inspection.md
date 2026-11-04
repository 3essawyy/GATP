# T-009: UI — URL, findings linked to source, selection, scope, goal

- **Status:** Done
- **Phase:** P1
- **Target:** W+2
- **Modules:** web-ui (+ small api change)
- **Requirements:** REQ-P1-2, REQ-P1-3, REQ-P1-D
- **Depends on:** T-008
- **Plan:** [PLAN-009](../implementationPlans/PLAN-009-ui-inspection.md)
- **TCs:** TC-107 (Pass), TC-110 (UI + storage Pass; model part in T-010)
- **Evidence:** [docs/samples/phase1-walkthrough/](../samples/phase1-walkthrough/)
- **Session:** [S004](../sessions/2026-11-04-S004-full-build-run.md)
- **Branch / PR:** `claude/serene-johnson-xtbl4s` → squash-merged to `main`

## Goal
The Phase 1 user journey in the browser.

## Scope
- In: URL entry + start inspection with live progress; findings table (role, name, attributes, locators + counts, usable flag) linked to the source page URL and screenshot (bbox highlighted on select); include/exclude/select elements; refine scope; testing goal input.
- Out: Phase 2 screens.

## Acceptance criteria
- [x] Full Phase 1 demo flow possible from the UI on fixture site v1 (`poe ui-walkthrough`: create project → inspect → source → setup steps → inspect add-book → goal/scope → G0)
- [x] No business logic in components (checklist in the [web-ui LLD](../modules/web-ui/README.md))

## Verification (real system) and what it changed
`uv run poe ui-walkthrough` drives the real UI against real processes. I reviewed every screenshot. Findings and fixes:

| Finding (from the walkthrough) | Fix |
|---|---|
| Page went blank after closing the source view (`destroy is not a function`) | In this Chromium `scrollIntoView()` returns a Promise, which my effect returned as its "cleanup". The effect now uses braces |
| After switching a setup step to `fill`, the strategy showed "label" but no locator was stored, so saving would fail | Choosing a non-`goto` action now initialises the locator, so what is shown is what is saved |
| Setup-editor inputs had no accessible names (the issue GATP flags on other sites) | Every field has an `aria-label` ("Step 2 locator value", …) |
| "Add a page" placeholder showed a hard-coded port | Placeholder uses the project's origin |
| Console 404s: `GET /scope` before any scope, and the favicon | `GET /scope` returns `null`; favicon added. The walkthrough ends with **no console errors** |

Final run: all 7 screens OK in ~9 s.

## Explain it (code-defense prep)

**What.** The browser UI for Phase 1:
- **Projects page:** a list, plus creating a project from a start URL.
- **Project workspace:** a step navigation (Inspect, Scope & goal, then Phase 2 steps), each with a status badge.
- **Inspect step:** per page, the setup steps, the inspection button, a screenshot whose element boxes are clickable, and the findings table (flags, best locator, all candidates with live usability, link to the source line).
- **Scope step:** goal, notes, element checkboxes and the G0 approval.

**Why:** the brief's Phase 1 demo is "open page, inspect, display findings; user picks target or goal" (REQ-P1-D), with findings linked to their source (REQ-P1-2) and the human choosing scope (REQ-P1-3). The team chose React for learning value, with a hard rule that it stays thin (ADR-002).

**How it works:**
- **Data:** components never call `fetch`. They use hooks in `api/queries.ts` (TanStack Query), which call the generated, typed `openapi-fetch` client. `unwrap()` turns API errors into exceptions carrying the server's `detail`, and `ErrorAlert` shows that text unchanged.
- **Live updates:** `useProjectEvents` opens an `EventSource` on `/api/projects/{id}/events` and invalidates queries on `inspection_finished`, `scope_saved`, `approved`, …, so the step badges and lists refresh without reloads.
- **Highlighting:** `ScreenshotView` draws a box for each element's `bbox`, converted to percentages of the screenshot's natural size so it scales. Clicking a box or a row selects the same element in both places.
- **Source link:** `source_line` opens `SourceModal`, which loads the stored served HTML (`/api/files/…`) and highlights that line.
- **Scope:** checkboxes are ticked by default. Saving sends the unticked keys as `exclude`, and the API validates and versions them. The G0 button sends the exact version id the API returned. Whether approval is allowed is decided by the API.

**Likely examiner questions:**
- *Where is the logic that decides a step is done?* In the API (`workflow.py`). The UI only displays `GET /workflow`, so there's nothing to defend in TypeScript beyond presentation.
- *How do you know the UI works, not just compiles?* `poe ui-walkthrough` runs it in a real browser against the real API, runner and fixture site, and fails on any page error. Its screenshots are the evidence. It found and fixed five real issues (table above).
- *How is the element highlighted on the screenshot?* The inspector records each element's bounding box in page coordinates when it takes the full-page screenshot. The UI overlays a box at the same relative position.
- *What happens if the runner is down?* The header badge says "Runner offline" (with the start command in a tooltip), and an inspection attempt shows the API's 503 message.
