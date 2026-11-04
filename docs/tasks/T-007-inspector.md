# T-007: Inspector — elements, attributes, ranked locators, uniqueness, fingerprints

- **Status:** Todo
- **Phase:** P1
- **Target:** W+1
- **Modules:** inspector, runner
- **Requirements:** REQ-P1-2, REQ-G8, REQ-Q1
- **Depends on:** T-006
- **Plan:** PLAN-007 (to write)
- **TCs:** TC-107, TC-108
- **Branch / PR:** `feat/T-007-inspector`

## Goal
Produce the InspectionSnapshot described in the [inspector LLD](../modules/inspector/README.md) per ADR-006.

## Scope
- In: interactive-element detection; role/accessible name/label/attributes/text/dom path/bbox/nearby text; locator candidates in priority order with live counts and `usable`; fingerprint; full-page screenshot; scope include/exclude; persistence via store.
- Out: shadow DOM/iframes unless trivial (document as limitation).

## Acceptance criteria
- [ ] On fixture site v1, every interactive element found (checked against fixture README)
- [ ] Non-unique locators marked unusable; elements without unique locator flagged
- [ ] Sample snapshot JSON saved for the Phase 1 submission

## Definition of Done
Standard (see [CLAUDE.md](../../CLAUDE.md)).

## Explain it (code-defense prep)
_To be written on completion._
