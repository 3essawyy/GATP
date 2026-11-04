# T-012: Collaborative test design + plan approval (G1)

- **Status:** Todo
- **Phase:** P2
- **Target:** W+3
- **Modules:** test-designer, api, web-ui
- **Requirements:** REQ-P2-1, REQ-G4, REQ-Q2
- **Depends on:** T-010
- **Plan:** PLAN-012 (to write)
- **TCs:** TC-201, TC-202
- **Branch / PR:** `feat/T-012-test-designer`

## Goal
Grounded test case proposals the tester can edit, clarify, and approve (see [test-designer LLD](../modules/test-designer/README.md)).

## Scope
- In: requirements input; case generation schema with `basis` per expected result; clarification requests for assumptions; plan editor UI; versioned `test_plan` artifact; G1 approval bound to version.
- Out: code (T-013).

## Acceptance criteria
- [ ] Every step references a snapshot element ID
- [ ] Assumption-based expectations cannot be approved until confirmed
- [ ] Edits create new versions; approval invalidated by edits

## Definition of Done
Standard (see [CLAUDE.md](../../CLAUDE.md)).

## Explain it (code-defense prep)
_To be written on completion._
