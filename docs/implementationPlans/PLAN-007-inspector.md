# PLAN-007: Inspector (for T-007)

- **Task:** [T-007](../tasks/T-007-inspector.md)
- **Status:** Executed
- **Date:** 2026-11-04

## Approach
- **In-page extraction:** a single read-only script `extract.js` collects interactive elements and their context.
- **Python side:** builds ADR-006 candidates, verifies each live (count + identity), picks a non-positional default, flags weak elements, maps source lines and fingerprints.
- **Runner:** the `inspect` job gains scope + setup steps ([ADR-018](../decisions/ADR-018-inspection-setup-and-usability.md)).
- **Store:** keeps all evidence (migration `0003`); the api converts results into snapshots.

## Steps
1. `inspector/extract.js`, `models.py`, `inspect.py`.
2. Runner: `SetupStep`, `InspectJob.scope/setup`, `_inspect` (setup, redirect check, served HTML, screenshot + HTML files).
3. Store: `elements.details`, `locator_candidates.spec`/`targets_element`; `LocatorDTO.unique` requires `targets_element`.
4. `api/inspections.py` converter.
5. Tests (TC-107 automated part, TC-108) + sample snapshots in `docs/samples/`.

## Tests to add
| Test | Proves |
|---|---|
| `test_inspector.py` | Element lists on all fixture pages match `fixtures/README.md`; best locators; source lines; flags; setup steps; redirect; scope; duplicates unusable + flagged; persistence |

## Risks / open questions
| Item | Mitigation / decision |
|---|---|
| Original response body lost on client redirect | Fetch the served HTML for the final URL with `page.request` |
| Accessible-name approximation | Live verification makes errors safe |

## Deviations (filled after execution)
- Added the `positional` marker and `weak_accessible_name` / `no_visible_label` flags after the first real run on the fixture site showed brittle defaults and unflagged poor labels.
