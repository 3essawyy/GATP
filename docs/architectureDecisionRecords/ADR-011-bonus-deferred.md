# ADR-011: Bonus feature — decide after Phase 1 feedback

- **Status:** Accepted (decision deferred)
- **Date:** 2026-11-04
- **Session:** S001
- **Related:** Bonus (≤1 pt); task T-022

## Context
Up to 1 bonus point for creative, useful work beyond the requirements, using only allowed models/resources.

## Decision
Choose the bonus direction **after Week 9 feedback**. Shortlist:

| Candidate | Problem it solves |
|---|---|
| Element coverage map | Shows which inspected elements are exercised by approved tests; highlights gaps |
| Accessibility audit (axe-core) | Surfaces a11y findings per page; offered as optional extra test cases |
| Playwright traces in results | Step-by-step failure investigation inside the UI |
| UI self-test (dogfooding) | GATP's own React UI tested with Playwright |

## Consequences
When chosen, supersede this ADR with a new ADR recording the choice, and plan it as T-022.
