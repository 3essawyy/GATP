# ADR-010: Phase 1 scope — front-load Phase 2

- **Status:** Accepted
- **Date:** 2026-11-04
- **Session:** S001
- **Related:** REQ-P1-*, REQ-P2-*; all tasks

## Context
The brief advises planning the full workflow from the start and developing Phase 2 components early. The team chose to build as much of Phase 2 as possible before Week 9.

## Decision
- Phase 1 delivers the full Phase 1 rubric **plus** as much of Phase 2 as fits before Week 9, in dependency order (see [tasks/README](../tasks/README.md)).
- Phase 1 rubric items are **never** put at risk by Phase 2 work: tasks T-002…T-011 come first; Phase 2 tasks start only once the Phase 1 demo path works end to end.
- Work is planned in **relative weeks**; calendar dates are filled in later.

## Alternatives considered
| Option | Why not |
|---|---|
| Rubric only, then Phase 2 | Compresses Phase 2 into 4 weeks |
| Rubric + Phase 2 skeletons | Was the recommendation; user chose more ambitious scope |

## Consequences
- **Risk:** Week 9 feedback may require rework of already-built Phase 2 parts. Mitigation: keep module boundaries clean and record every assumption as an ADR so rework is targeted.
- The Phase 1 submission must clearly separate what's graded for Phase 1 from early Phase 2 work.
