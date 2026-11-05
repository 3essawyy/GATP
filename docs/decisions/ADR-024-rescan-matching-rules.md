# ADR-024: Rescan, matching rules and read-only setup retry

- **Status:** Accepted
- **Date:** 2026-11-04
- **Session:** S004
- **Related:** REQ-P2-4, REQ-G8, T-016, TC-208; refines [ADR-007](ADR-007-maintenance-matching.md)

## Context
ADR-007 fixed the approach: deterministic fingerprint scoring, the model only explains, and ambiguity goes to the human. T-016 needed concrete rules that classify the fixture's three changes correctly:
- **FXC-1** (sign-in renamed) must be a clear match;
- **FXC-2** (Save split into Save draft + Publish) must be ambiguous;
- **FXC-3** (footer text) is low impact.

A side effect of FXC-1: the add page's **setup steps** sign in through that button, so a plain rescan of the add page fails.

## Decision
- **Rescan** (`POST /projects/{id}/rescans`, user-requested): every page of the approved scope (G0) is inspected again with its original inspection scope and setup steps. This creates new immutable snapshots.
  - The result is a `rescans` row (migration 0007) and one `change_sets` row per page. Both are write-once (ORM guard).
- **Elements the tests use:** plan step and expectation element ids, plus setup-step locators. A setup-step locator is mapped to the baseline element that has the same usable locator.
- **Matching** (`maintainer/match.py`, pure functions):
  1. **unchanged:** the old default locator is still a usable (unique, verified) candidate in the new snapshot. A different accessible name is reported as a text change.
  2. Other elements are scored only against elements that **appeared** (did not keep an old locator). The score is a weighted fingerprint similarity (15 fields; exact for role/tag/type/form/id/name attribute, fuzzy for name/label/test id/text/path, distance for position). Fields empty on both sides don't count.
  3. **clear_match:** score ≥ 0.70, margin ≥ 0.15 over the runner-up, and **no split**.
     - A split means two or more plausible appeared elements with the same role in the same form. The old element was replaced by several, so the tester must choose.
  4. **ambiguous:** some candidate ≥ 0.45 but not clear.
  5. **missing:** nothing ≥ 0.45.
  - Each result keeps the top 3 candidates with the per-field breakdown (the evidence).
  - **Tuned on the fixture:** FXC-1 scores 0.85 (clear). FXC-2: Save draft 0.81, Publish 0.69, ambiguous by both the split and the margin rule.
- **Read-only setup retry:** if a page fails at setup step *n*, and that step's locator belongs to an element classified clear_match on another rescanned page, the page is inspected **once more, read-only**, with the proposed locator. The page can then still be compared.
  - The result says so (step, old and proposed locator, basis).
  - The stored setup steps and code are untouched: repairs need G4 (T-017).
- **Low-impact changes:** the page HTML hash change is reported per page (FXC-3 footer text). Non-interactive text outside observable regions is not tracked.
- **Workflow step `maintain` (G4):**
  - `todo` before any rescan;
  - `needs_approval` when used elements changed or a page failed;
  - `approved` when nothing used changed;
  - `blocked` by open clarifications (T-017).

## Alternatives considered
| Option | Why not |
|---|---|
| Score margin only | Margin happened to work for FXC-2 (0.12 < 0.15), but a split with one obviously better name would be called "clear"; the brief wants the human to decide when a control was replaced by several |
| Ask the tester to fix the setup before rescanning | Two round trips for one change; the retry is read-only and labelled |
| LLM picks the match | Not reproducible or evidence-backed (ADR-007) |

## Consequences
- Weights and thresholds are constants in `match.py`, tuned on the fixture; the instructor's site may need retuning (SG-006).
- T-017 builds repairs from the stored change sets: proposals for clear matches (G4), clarifications for ambiguous/missing elements, and setup-step repairs.
