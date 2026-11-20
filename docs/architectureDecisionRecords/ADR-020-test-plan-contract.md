# ADR-020: Test plan as structured, grounded data; observable regions; offline examples

- **Status:** Accepted
- **Date:** 2026-11-04
- **Session:** S004
- **Related:** REQ-P2-1, REQ-Q1, REQ-Q2, REQ-Q3, T-012, TC-201, TC-202; builds on [ADR-006](ADR-006-locator-strategy.md), [ADR-016](ADR-016-llm-gateway-design.md), [ADR-019](ADR-019-gates-on-versions-computed-workflow.md); modules test-designer, inspector, api

## Context
In S004 we agreed that code generation renders templates from the model's *structured* steps (T-013), so the test plan format is the contract between design and code. Meaningful expected results (REQ-Q3) need things to check, such as error messages and notices, which aren't interactive elements. Assumptions must be confirmed before G1 (REQ-Q2). Offline demos need the plan step to work without a model key.

## Decision
- **Plan schema** (`test_designer/plan.py`): `TestPlan{cases[TestCase{id, title, priority, preconditions, steps[PlanStep], expected[Expectation], open_questions}]}`.
  - **Steps:** `goto` (a scoped page URL) or `fill | select | check | uncheck | click | press` on an **interactive** element id with a usable locator.
  - **Expectations:** a kind (`visible | hidden | text_equals | text_contains | value_equals | url_contains | count_equals | enabled | disabled | checked`), an element/region id (not for `url_contains`), a value, `basis ∈ requirement | observation | assumption`, evidence, and `confirmed`.
- **Validation** (`validate_plan`) runs on model output (semantic `check`: repair retry, then 502) and on every tester edit (422):
  - ids exist in the approved scope;
  - steps never act on regions;
  - the action fits the element (fill a text input, select a `<select>`, …);
  - the element has a unique locator;
  - values and evidence are present;
  - the first step is `goto`.
- **Observable regions:** the inspector also records alert/status/live regions, dialogs, headings and tables as `o<n>` elements with verified locators. They can be checked but never acted on.
- **Expectation ids** (`TC-01.x2`) are assigned by GATP and stay stable across versions. The model can never set `confirmed`: an unchanged expectation keeps its confirmation, a changed one loses it.
- **Clarifications:**
  - Each unconfirmed assumption and each open question becomes a clarification on step `plan`, which blocks G1.
  - Answers create a **new plan version**: *Confirm*, *Remove this expectation*, or a corrected value. A corrected value becomes `basis=requirement`, with the tester's name as evidence.
  - Clarifications whose expectation disappears are closed as `superseded`.
- **G1** additionally requires no unconfirmed assumptions in the approved version.
- **Offline examples:** templates may register a deterministic example generator (`OFFLINE_EXAMPLES`) that the `fake` provider uses. It builds a small, valid plan from the page data it was sent and is labelled "Offline example (fake provider)". It exists only so the UI and the walkthrough work without a key; it is never a substitute for a model.

## Alternatives considered
| Option | Why not |
|---|---|
| Free-text test cases | Can't be validated or turned into code without the model inventing locators |
| Let the model write Playwright code directly | Rejected in S004 (codegen from structured steps) |
| Assert on arbitrary page text without regions | Ungrounded; error messages would have no verified locator |

## Consequences
- Codegen (T-013) maps each step/expectation kind to a template line using the element's verified default locator.
- Inspection lists contain more elements (regions). The UI marks them "region (for expected results)".
