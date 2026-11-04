# ADR-018: Inspection setup steps and the locator usability rule

- **Status:** Accepted
- **Date:** 2026-11-04
- **Session:** S004
- **Related:** REQ-P1-2, REQ-Q1, T-007, TC-107, TC-108; refines [ADR-006](ADR-006-locator-strategy.md); modules inspector, runner

## Context
- **Signed-in pages:** pages behind a sign-in (BookShelf `books.html`, `add.html`, and most real sites) redirect when opened in a fresh browser. A project has many pages (agreed in S004), so inspection must be able to reach them.
- **Gaps in ADR-006:** ADR-006 says a locator is usable if `count == 1`. That misses two cases:
  1. A unique match on the *wrong* element.
  2. Positional CSS paths, which are always unique but break on any layout change.

## Decision
- **Setup steps:**
  - An `inspect` job may carry tester-approved setup steps before the page is opened: `goto`, `fill`, `click`, `select`, with targets as `LocatorSpec` data.
  - `goto` URLs must be on the job's allowlist.
  - Steps are stored and shown to the tester; they are data, never code.
- **Usability rule:**
  - A candidate is **usable** only if it matches exactly one element **and** that element is the inspected one. The second part is checked in the page by identity against `window.__gatpEls[i]`.
  - Positional DOM-path CSS is recorded as evidence (`positional: true`) but is **never the default**.
  - An element whose only usable candidate is positional is flagged `no_unique_locator` and needs tester clarification before it's used in tests.
- **Redirects:** after navigation the runner waits for client-side redirects, reports `final_url`, and refuses redirects outside the allowlist.

## Alternatives considered
| Option | Why not |
|---|---|
| Reuse a saved browser storage state | Opaque blob, harder to review and replay; steps are explicit and repeatable |
| Ask the LLM to log in | Ungrounded, uses credentials in prompts, not deterministic |
| Treat positional CSS as a normal default | Silently produces brittle tests; the brief wants weak locators flagged |

## Consequences
- The UI (T-009) needs a small "steps before inspecting" editor, saved per page.
- Credentials typed into setup steps are stored in the project DB. This is a documented limitation; use test accounts only.
