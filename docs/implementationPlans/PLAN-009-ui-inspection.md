# PLAN-009: UI for the Phase 1 journey (for T-009)

- **Task:** [T-009](../tasks/T-009-ui-inspection.md)
- **Status:** Executed
- **Date:** 2026-11-04

## Approach
A thin React UI ([ADR-013](../decisions/ADR-013-frontend-libraries.md)) with React Router: a project list, then a project workspace with step navigation whose statuses come from `GET /workflow`. Inspect and Scope are the Phase 1 screens. Data access goes through typed TanStack Query hooks over the generated client, and SSE events refresh queries. A Playwright script (`poe ui-walkthrough`) verifies the real stack.

## Steps
1. `react-router` 8; client type aliases + `unwrap()` error helper; hooks for every endpoint; `useProjectEvents` (SSE).
2. Components: findings table, screenshot overlay, source modal, setup-steps editor, badges.
3. Pages: Projects, ProjectLayout (+ clarifications banner), Inspect, Scope.
4. `scripts/ui_walkthrough.py` + `poe ui-walkthrough`; review the screenshots; fix what they show.
5. Docs: web-ui LLD (+ no-logic checklist), TCs, task doc.

## Tests to add
| Test | Proves |
|---|---|
| `poe ui-walkthrough` | The full Phase 1 flow works in a browser against real processes; no page errors |
| `test_scope_is_null_before_first_save` | API change made for the UI |

## Risks / open questions
| Item | Mitigation / decision |
|---|---|
| UI logic creeping in | Checklist in the web-ui LLD |

## Deviations (filled after execution)
- The client is now generated with `--default-non-nullable false`, so fields with defaults are optional in request bodies.
- `GET /scope` returns `null` instead of 404 (found by the walkthrough: noisy console errors).
