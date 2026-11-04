# T-020: Security hardening + tests

- **Status:** Todo
- **Phase:** P2
- **Target:** W+6
- **Modules:** runner, llm-gateway, api
- **Requirements:** REQ-Q5, REQ-Q6, REQ-Q7
- **Depends on:** T-014
- **Plan:** PLAN-020 (to write)
- **TCs:** TC-213
- **Branch / PR:** `feat/T-020-security`

## Goal
Prove the isolation and injection defenses work.

## Scope
- In: fixture page containing prompt-injection text (must be treated as data); tests for allowlist blocking, sandbox filesystem confinement, job-type restriction, timeouts; generated-code checks rejecting imports like `os`/`subprocess` beyond an allowlist; limitations section in SG docs.
- Out: container isolation (documented as future work).

## Acceptance criteria
- [ ] Injection page does not change assistant behavior; evidence recorded
- [ ] All security tests in CI

## Definition of Done
Standard (see [CLAUDE.md](../../CLAUDE.md)).

## Explain it (code-defense prep)
_To be written on completion._
