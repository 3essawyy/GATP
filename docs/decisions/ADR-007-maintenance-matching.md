# ADR-007: Maintenance matching and repairs

- **Status:** Accepted
- **Date:** 2026-11-04
- **Session:** S001
- **Related:** REQ-P2-4, REQ-P2-D1, REQ-P2-D2, REQ-Q4; module maintainer

## Context
After a page change, the assistant must flag changes, propose evidence-backed locator repairs, apply only approved repairs while preserving intent, and ask when matches are ambiguous.

## Decision
- **Deterministic scoring; the LLM only explains.**
- Each element has a **fingerprint**: role, accessible name, label, tag, key attributes (id, name, type, data-testid, placeholder, href), DOM path, nearby text, position/bbox, page.
- On rescan, old elements are matched to new elements by a weighted similarity score.
- Outcomes per referenced element:
  - **Unchanged** — same default locator still unique.
  - **Changed, clear match** — top score ≥ threshold **and** margin over runner-up ≥ margin → propose repair with evidence (old vs new attributes, score breakdown).
  - **Ambiguous** — several candidates close → **clarification request** listing candidates with evidence.
  - **Missing** — no candidate above floor → flag as removed; ask tester.
- Repairs change **only locators** in page objects; test steps and assertions are untouched (intent preserved). Each applied repair creates a new code version (`author=repair`) after G4 approval.
- Only tests affected by repaired elements are proposed for rerun (G3).
- Weights/threshold/margin are config values, tuned against the fixture site v1→v2 and documented.

## Alternatives considered
| Option | Why not |
|---|---|
| LLM decides the match | Hard to justify as evidence-backed; non-deterministic |
| Score + LLM tie-break | Ambiguity should go to the human per brief |

## Consequences
- Fixture site v2 must contain at least one clear locator change and one genuinely ambiguous change.
