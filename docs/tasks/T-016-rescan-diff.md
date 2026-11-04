# T-016: Rescan + snapshot diff + change flags

- **Status:** Todo
- **Phase:** P2
- **Target:** W+5
- **Modules:** maintainer, api, web-ui
- **Requirements:** REQ-P2-4, REQ-G8
- **Depends on:** T-007, T-014
- **Plan:** PLAN-016 (to write)
- **TCs:** TC-208
- **Branch / PR:** `feat/T-016-rescan-diff`

## Goal
On user request, re-inspect the page and flag what changed relative to the snapshot the tests were built on (ADR-007).

## Scope
- In: rescan endpoint (new immutable snapshot); fingerprint similarity scoring; classification unchanged / clear match / ambiguous / missing / new; ChangeSet persisted; change flags UI.
- Out: applying repairs (T-017).

## Acceptance criteria
- [ ] Fixture v1→v2: clear change classified as clear match; ambiguous change classified ambiguous
- [ ] Unit tests for scoring on synthetic fingerprints

## Definition of Done
Standard (see [CLAUDE.md](../../CLAUDE.md)).

## Explain it (code-defense prep)
_To be written on completion._
