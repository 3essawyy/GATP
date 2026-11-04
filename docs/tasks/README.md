# Tasks — source of truth for status

Update this table in the same PR that changes a task's status. Template: [_TEMPLATE.md](_TEMPLATE.md). Weeks are **relative** (W+0 = week of 2026-11-04); fill calendar dates when known.

Milestones: **M1 = Phase 1 submission (Week 9)** · **M2 = Phase 2 submission (Week 13)**

## Phase 1 path (must not be put at risk — ADR-010)

| ID | Title | Modules | Depends on | Target | Status |
|---|---|---|---|---|---|
| [T-001](T-001-docs-scaffold.md) | Docs scaffold, ADRs, HLD, task breakdown | docs | — | W+0 | Done |
| [T-002](T-002-repo-skeleton-ci.md) | Repo skeleton (backend, frontend, CI, tooling) | all | T-001 | W+0 | Done |
| [T-003](T-003-fixture-site.md) | Fixture site v1/v2 | fixtures | T-002 | W+0 | Done |
| [T-004](T-004-store-core.md) | Store core: schema, repositories, versioning | store | T-002 | W+1 | Todo |
| [T-005](T-005-llm-gateway.md) | LLM gateway: Gemini + Ollama, structured output, usage log | llm-gateway | T-004 | W+1 | Todo |
| [T-006](T-006-runner-skeleton.md) | Runner process: job protocol, sandbox, allowlist, headed browser | runner, api | T-002 | W+1 | Todo |
| [T-007](T-007-inspector.md) | Inspector: elements, attributes, ranked locators, uniqueness, fingerprints | inspector | T-006 | W+1 | Todo |
| [T-008](T-008-api-core.md) | API core: projects/inspections, workflow state, gates, clarifications, TS client | api | T-004, T-007 | W+2 | Todo |
| [T-009](T-009-ui-inspection.md) | UI: URL, findings linked to source, selection, scope, goal | web-ui | T-008 | W+2 | Todo |
| [T-010](T-010-feasibility-llm-call.md) | Grounded LLM summary / next action + usage display | llm-gateway, api, web-ui | T-005, T-009 | W+2 | Todo |
| [T-011](T-011-phase1-submission.md) | Phase 1 submission pack | docs | T-010 | before W9 | Todo |

## Phase 2 (front-loaded as far as possible before Week 9)

| ID | Title | Modules | Depends on | Target | Status |
|---|---|---|---|---|---|
| [T-012](T-012-test-designer.md) | Collaborative test design + G1 | test-designer, api, web-ui | T-010 | W+3 | Todo |
| [T-013](T-013-codegen.md) | POM code generation + validation + review (G2) | codegen, runner | T-012 | W+3 | Todo |
| [T-014](T-014-execution.md) | Approved execution, results, screenshots (G3) | runner, api, web-ui | T-013 | W+4 | Todo |
| [T-015](T-015-feedback-rerun.md) | Feedback → revise → approved rerun | api, test-designer, codegen | T-014 | W+4 | Todo |
| [T-016](T-016-rescan-diff.md) | Rescan + snapshot diff + change flags | maintainer | T-007, T-014 | W+5 | Todo |
| [T-017](T-017-repairs.md) | Repair proposals, ambiguity clarification, apply (G4), rerun affected | maintainer, api, web-ui | T-016 | W+5 | Todo |
| [T-018](T-018-versioning-ui.md) | Version history, diffs, restore (G5) | store, web-ui | T-004, T-013 | W+6 | Todo |
| [T-019](T-019-usage-visibility.md) | Usage panel: per-call metrics, averages, fresh vs reused, test vs model time | llm-gateway, web-ui | T-010, T-014 | W+6 | Todo |
| [T-020](T-020-security-hardening.md) | Security hardening + tests (injection, allowlist, sandbox) | runner, llm-gateway | T-014 | W+6 | Todo |
| [T-021](T-021-phase2-submission.md) | Phase 2 submission pack + demo rehearsal | docs | all | before W13 | Todo |
| [T-022](T-022-bonus.md) | Bonus feature (chosen after P1 feedback) | TBD | T-011 | after W9 | Blocked (ADR-011) |
