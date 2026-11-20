# PLAN-016: Rescan + snapshot diff + change flags (for T-016)

- **Task:** [T-016](../tasks/T-016-rescan-diff.md)
- **Status:** Executed
- **Date:** 2026-11-04

## Approach
[ADR-024](../architectureDecisionRecords/ADR-024-rescan-matching-rules.md): rescan all approved pages, match deterministically (`maintainer/match.py`), store a rescan with per-page change sets, and show the flags with per-field evidence on a Maintain page. No repairs (T-017).

## Steps
1. `maintainer/match.py` (`El`, `score`, `match_page`, `classify`). Tuned against real v1/v2 inspections (scratch experiment: FXC-1 0.85 clear; FXC-2 0.81/0.69 split → ambiguous).
2. Store: `Rescan` model, `change_sets.rescan_id`, migration 0007, `RescanRepository`, ORM immutability.
3. Runner: `SetupStepError` with the failing step number (`data.failed_setup_step`), 10 s timeout for setup actions.
4. API: `maintain_service.py` (references from plan + setup, rescan, read-only setup retry, page summaries), `routes/maintain.py`, `maintain` workflow step.
5. Fixtures: `SiteServer.switch(version)` (same origin), test fixture `site_switchable`; smoke harness `switch_site()`.
6. UI: `MaintainPage` (rescan, setup alert, per-page counts, element accordion with candidates + breakdown).
7. Tests + walkthrough screen 19.

## Tests to add
| Test | Proves |
|---|---|
| `test_maintain.py::test_scoring_units` | Synthetic fingerprints: unchanged by locator, clear rename with breakdown, split → ambiguous, missing, text change kept, identical score 1.0 |
| `…::test_rescan_without_changes` | v1 → v1: new snapshots, nothing used changed, step approved |
| `…::test_rescan_v1_to_v2_flags_clear_and_ambiguous` | Real v1 → v2 on the same origin: FXC-1 clear (used by setup step 4), add page compared via the read-only retry, FXC-2 ambiguous with both candidates, HTML change flagged, step needs approval, stored setup untouched |

## Deviations (filled after execution)
- Added the read-only setup retry. Without it, FXC-1 breaks the add page's sign-in, so FXC-2 could never be observed in one rescan.
- Locators are shown in the generated code's form (double quotes) and compared in normalised AST form.
