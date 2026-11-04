# T-017: Repair proposals, ambiguity clarification, apply (G4), rerun affected

- **Status:** Todo
- **Phase:** P2
- **Target:** W+5
- **Modules:** maintainer, codegen, api, web-ui
- **Requirements:** REQ-P2-4, REQ-P2-D1, REQ-P2-D2, REQ-Q4, REQ-G5
- **Depends on:** T-016
- **Plan:** PLAN-017 (to write — record weights/threshold/margin in an ADR)
- **TCs:** TC-209, TC-210
- **Branch / PR:** `feat/T-017-repairs`

## Goal
Evidence-backed repairs applied only after approval, preserving test intent; clarification for ambiguity.

## Scope
- In: RepairProposal with evidence (attribute diff, score breakdown, screenshots); LLM explanation; clarification UI listing candidates; G4 approval; locator-only code change as new version (`author=repair`); affected-test detection; G3 rerun of affected tests.
- Out: —

## Acceptance criteria
- [ ] Repair diff touches only locators
- [ ] Ambiguous case never auto-resolves; tester choice recorded
- [ ] Affected test passes after approved repair + rerun on fixture v2

## Definition of Done
Standard (see [CLAUDE.md](../../CLAUDE.md)).

## Explain it (code-defense prep)
_To be written on completion._
