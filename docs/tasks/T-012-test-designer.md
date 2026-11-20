# T-012: Collaborative test design + G1

- **Status:** Done (offline provider verified; real-model run of the plan step still to do)
- **Phase:** P2
- **Target:** W+3
- **Modules:** test-designer, api, web-ui, inspector, llm-gateway
- **Requirements:** REQ-P2-1, REQ-Q1, REQ-Q2, REQ-Q3
- **Depends on:** T-010
- **Plan:** [PLAN-012](../implementationPlans/PLAN-012-test-designer.md)
- **ADRs:** [ADR-020](../architectureDecisionRecords/ADR-020-test-plan-contract.md)
- **TCs:** TC-201 Pass, TC-202 Pass (offline provider; real-model run still to do)
- **Session:** [S004](../sessions/2026-11-04-S004-full-build-run.md)

## Goal
Grounded test case proposals the tester can edit, clarify, and approve (see [test-designer LLD](../modules/test-designer/README.md)).

## Acceptance criteria
- [x] Every step references a snapshot element id (validated: unknown ids, regions as step targets and impossible actions are rejected)
- [x] Assumption-based expectations cannot be approved until confirmed (clarification per assumption; G1 rule)
- [x] Edits create new versions; approval invalidated by edits

## Verification (real system)
`poe ui-walkthrough` now continues into the plan step: propose (offline provider) → 3 clarifications in the banner → Confirm / answer → G1 → edit a title → *needs approval* again (v4 by the tester). Evidence: [phase2-walkthrough/](../samples/phase2-walkthrough/). Review of the screenshots led to:
- clarification questions naming elements (`alert "title-error" (s2.o2) is visible`) instead of raw ids, with correct punctuation;
- no misleading "browser time 0 ms" on the plan's usage card.

`poe smoke` still passes.

## Explain it (code-defense prep)
**What.** On the Test plan step, GATP asks the model for test cases grounded in the approved scope.
- **Steps** act only on inspected interactive elements, by id.
- **Expected results** check elements, regions (error messages, notices, headings) or the URL. Each one says where it comes from: a **requirement** the tester gave, an **observation** on the page, or an **assumption**.
- **Questions:** every assumption and every open question becomes a clarification. The tester answers in the banner (Confirm, Remove, or the correct value), and each answer creates a new plan version.
- **Edits** also create new versions.
- **Approval (G1)** is possible only when nothing is open or unconfirmed, and only for the latest version.

**Why.** The brief asks for cases grounded in inspected elements and the tester's requirements, with meaningful expected results, plus editing, clarification and explicit approval (REQ-P2-1). Assumptions must not silently become expected behaviour (REQ-Q2). The structured format is also what lets T-013 generate code without inventing locators.

**How it works:**
1. `approved_scope()` loads the G0-approved scope, including interactive elements and regions.
2. `propose_plan()` sends the goal, requirements and earlier answers (trusted) plus page data (untrusted) and asks for a `TestPlan`.
3. `validate_plan()` checks every id and action against the scope. Anything wrong triggers the gateway's repair retry, and if that fails nothing is stored.
4. `normalise()` assigns stable expectation ids (`TC-01.x2`) and makes sure the model can never mark anything confirmed.
5. `store_plan()` appends the version and `sync_clarifications()` opens or closes clarifications.
6. When the tester answers, `apply_answer()` turns the answer into a new version: confirmed, removed, or corrected into a requirement credited to the tester.
7. The G1 check in `workflow.py` refuses unconfirmed assumptions.

**Likely examiner questions:**
- *How do you stop the model from inventing elements or behaviour?* Unknown ids, acting on non-interactive regions, and impossible actions are rejected. Behaviour the model believes but nobody stated must be labelled an assumption, and assumptions can't be approved until the tester confirms them.
- *What happens when I edit an approved plan?* A new version is created. G1 pointed to the old version, so the step goes back to *needs approval*. Confirmations survive only for expectations you didn't change.
- *What are o-elements?* Regions the inspector observed, such as error messages, status notices and headings. Expected results check them with verified locators instead of guessing text locations.
- *Is the offline plan a fake result?* It's a clearly labelled example generator, used only when no model is configured, so the workflow can be demonstrated. It's logged as provider `fake`.
