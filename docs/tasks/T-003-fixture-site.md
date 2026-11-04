# T-003: Fixture site v1/v2

- **Status:** Todo
- **Phase:** P1
- **Target:** W+0
- **Modules:** fixtures
- **Requirements:** REQ-G9, REQ-P2-D1, REQ-P2-D2
- **Depends on:** T-002
- **Plan:** PLAN-003 (to write)
- **TCs:** TC-103
- **Branch / PR:** `test/T-003-fixture-site`

## Goal
Our own small website and a modified version to develop and demo the full flow against before the instructor's site exists (ADR-009).

## Scope
- In: `fixtures/site-v1/` with ≥3 pages (login, form with validation, list/search) using a mix of labels, roles, test-ids and some poorly labelled elements; `fixtures/site-v2/` with **one clear locator change** and **one ambiguous change**; a local server script serving either version on a fixed port; `fixtures/README.md` listing intended behaviors and every v1→v2 change.
- Out: real backend logic beyond what pages need (simple JS is fine).

## Acceptance criteria
- [ ] Both versions served with one command each
- [ ] README documents expected behaviors (used as "requirements" in demos) and each change with its intended maintenance outcome (repair vs clarification)

## Definition of Done
Standard (see [CLAUDE.md](../../CLAUDE.md)).

## Explain it (code-defense prep)
_To be written on completion._
