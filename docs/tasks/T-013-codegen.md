# T-013: POM code generation, validation, review (G2)

- **Status:** Todo
- **Phase:** P2
- **Target:** W+3
- **Modules:** codegen, runner, web-ui
- **Requirements:** REQ-P2-2, REQ-Q1, REQ-Q3
- **Depends on:** T-012
- **Plan:** PLAN-013 (to write — must decide LLM-vs-template split, ADR)
- **TCs:** TC-203, TC-204
- **Branch / PR:** `feat/T-013-codegen`

## Goal
Executable pytest-playwright POM code from an approved plan, validated and reviewable (ADR-008, [codegen LLD](../modules/codegen/README.md)).

## Scope
- In: page objects from snapshot locators only; tests per case ID; AST validation; locator verification + live recount; pytest collect-only in runner; validation report; code review UI (editor; user edits create versions and re-validate); G2 approval.
- Out: execution (T-014).

## Acceptance criteria
- [ ] Generated code for fixture v1 passes all validation steps
- [ ] An injected invented locator is caught and reported
- [ ] Code versions linked to the plan version they came from

## Definition of Done
Standard (see [CLAUDE.md](../../CLAUDE.md)).

## Explain it (code-defense prep)
_To be written on completion._
