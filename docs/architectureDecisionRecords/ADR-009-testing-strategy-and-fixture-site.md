# ADR-009: Testing strategy for GATP and fixture site

- **Status:** Accepted
- **Date:** 2026-11-04
- **Session:** S001
- **Related:** REQ-G9, REQ-P2-D1, REQ-P2-D2, REQ-P2-6

## Context
The instructor's site and its modified version are not available yet. The maintenance flow needs a controlled v1 → v2 change to develop and demo against.

## Decision
- Build our own **fixture site** in `fixtures/site-v1/` and `fixtures/site-v2/`: small, multi-page (e.g., login, form with validation, list/search), static or minimal, served locally.
- `site-v2` contains at least: **one clear locator change** (e.g., renamed id/label on the same element) and **one ambiguous change** (e.g., two similar buttons where one replaced the original).
- GATP tests: **pytest** unit tests per module + integration tests driving the flow against the fixture site; frontend type-check + lint.
- **GitHub Actions CI**: lint, type-check, tests for backend and frontend on every PR.
- Acceptance test cases in `docs/TCs/` trace every rubric line and demo step.

## Alternatives considered
| Option | Why not |
|---|---|
| Public demo sites | No v2 to rescan; can change under us |
| No CI | Weaker evidence of reproducibility |

## Consequences
- Fixture site is a maintained asset with its own README listing the intended v1→v2 changes.
- CI needs browsers installed (`playwright install --with-deps chromium`); headed tests run headless in CI.
