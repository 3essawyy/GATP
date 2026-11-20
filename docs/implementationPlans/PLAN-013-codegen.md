# PLAN-013: Code generation, validation, review (for T-013)

- **Task:** [T-013](../tasks/T-013-codegen.md)
- **Status:** Executed
- **Date:** 2026-11-04

## Approach
Render code deterministically from the G1-approved plan and verified locators ([ADR-021](../architectureDecisionRecords/ADR-021-deterministic-codegen.md)). Validate statically, then live in the runner (recount + a new `collect` job). Bind reports to exact versions so G2 can require a passing one. Provide a code review page and extend smoke and walkthrough.

## Steps
1. `pytest-playwright` as a runtime dependency (disabled for GATP's own suite).
2. `codegen/render.py`, `codegen/validate.py`.
3. Runner: `setup` on `recount`, `CollectJob` + `runner/collect.py` (sandbox, scrubbed env, timeout).
4. Store: `validation_reports` (migration `0006`), `generator` author.
5. API: `code_service.py`, `/code` routes, G2 rule, workflow ignores retired files.
6. UI: `CodePage`.
7. Tests (incl. a real run of the generated test), smoke + walkthrough steps, docs.

## Tests to add
| Test | Proves |
|---|---|
| `test_codegen.py` | TC-203/TC-204 (see the codegen LLD), plus that the generated test really passes on fixture v1 |
| smoke "plan G1 → code → validate (runner) → G2" | Real processes, `collect` over the socket |

## Risks / open questions
| Item | Mitigation / decision |
|---|---|
| Collection executes module code | Static safety checks first; sandbox with scrubbed env; bubblewrap in T-014/T-020 |

## Deviations (filled after execution)
- **Running the generated test for real** (not planned) exposed that protected pages need the sign-in setup steps. Page objects' `open()` now replays them.
- **Monaco replaced** by a plain editor (ADR-021).
