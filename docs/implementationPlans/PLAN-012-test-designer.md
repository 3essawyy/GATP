# PLAN-012: Collaborative test design + G1 (for T-012)

- **Task:** [T-012](../tasks/T-012-test-designer.md)
- **Status:** Executed
- **Date:** 2026-11-04

## Approach
Define the plan as structured, validated data that T-013 can render ([ADR-020](../architectureDecisionRecords/ADR-020-test-plan-contract.md)). Give expectations something real to check by recording observable regions in the inspector. Wire assumptions and questions into clarifications that block G1 and update the plan when answered. Build a plan editor screen, and extend the walkthrough.

## Steps
1. Inspector: observable regions (`o<n>`, `interactive=false`).
2. Gateway: `ProviderRequest.template_id`, `OFFLINE_EXAMPLES` for the `fake` provider.
3. `test_designer/plan.py`: schema, template, validation, normalisation, propose/revise, offline example.
4. API: `context.py` (approved scope, shared with insight), `plan_service.py` (store, sync clarifications, apply answers), routes `/plan` (propose, get, edit), G1 rule in `workflow.py`, answer hook.
5. UI: `PlanPage` (cases, steps with element labels, expectations with basis/confirmed, inline edits, delete, revise with feedback, approve G1); region badge in findings.
6. Tests + walkthrough + docs.

## Tests to add
| Test | Proves |
|---|---|
| `test_api_plan.py` | G0 required; grounded proposal with stable ids; assumption + question clarifications; plan blocked; G1 only after confirmations, on the latest version; corrected value → requirement; edit → new version, approval lost, invalid edits rejected; actions on regions rejected (model output); offline example valid |
| `test_inspector.py::test_observable_regions_for_expected_results` | Regions recorded with verified locators |

## Risks / open questions
| Item | Mitigation / decision |
|---|---|
| Model returns invalid plans | Validation + repair retry + clear 502; nothing stored |
| Tester edits remove an assumption | Its clarification is closed as `superseded` |

## Deviations (filled after execution)
- Added `id` to the attributes sent to the model: without it, similar regions (`#title-error`, `#author-error`) couldn't be told apart (found by the tests).
