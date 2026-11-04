# Decisions (ADRs)

Never delete or rewrite an accepted ADR. To change a decision, add a new ADR and mark the old one `Superseded by ADR-NNN`. Template: [_TEMPLATE.md](_TEMPLATE.md).

| ID | Title | Status | Date |
|---|---|---|---|
| [ADR-001](ADR-001-team-workflow-and-docs.md) | Team workflow and documentation structure | Accepted | 2026-11-04 |
| [ADR-002](ADR-002-tech-stack.md) | Tech stack: FastAPI + thin React/Vite/TS | Accepted | 2026-11-04 |
| [ADR-003](ADR-003-llm-providers.md) | LLM providers (Gemini Flash + Ollama) and usage logging | Accepted | 2026-11-04 |
| [ADR-004](ADR-004-runner-isolation.md) | Runner isolation: separate restricted host process | Accepted | 2026-11-04 |
| [ADR-005](ADR-005-storage-and-versioning.md) | SQLite + artifacts; immutable versions | Accepted | 2026-11-04 |
| [ADR-006](ADR-006-locator-strategy.md) | Locator ranking + live uniqueness check | Accepted | 2026-11-04 |
| [ADR-007](ADR-007-maintenance-matching.md) | Deterministic matching; LLM explains; ambiguity → clarification | Accepted | 2026-11-04 |
| [ADR-008](ADR-008-generated-tests-python-pom.md) | Generated tests: pytest-playwright + POM | Accepted | 2026-11-04 |
| [ADR-009](ADR-009-testing-strategy-and-fixture-site.md) | Own fixture site v1/v2 + pytest + CI | Accepted | 2026-11-04 |
| [ADR-010](ADR-010-phase1-scope-frontload.md) | Phase 1 front-loads Phase 2 | Accepted | 2026-11-04 |
| [ADR-011](ADR-011-bonus-deferred.md) | Bonus decided after Phase 1 feedback | Accepted (deferred) | 2026-11-04 |
| [ADR-012](ADR-012-backend-and-dev-tooling.md) | Backend and dev tooling: uv, ruff, mypy strict, poethepoet, single package | Accepted | 2026-11-04 |
| [ADR-013](ADR-013-frontend-libraries.md) | Frontend libraries: npm, ESLint+Prettier, Mantine, TanStack Query, openapi-typescript/fetch, Monaco | Accepted | 2026-11-04 |

## Open decisions (to become ADRs)
| Topic | Decide in |
|---|---|
| Exact Gemini model ID + verified free-tier limits | T-005 |
| DB access layer + migrations tool | T-004 |
| Core ↔ runner job protocol (HTTP vs queue vs stdin/stdout) | T-006 |
| LLM-vs-template split in code generation | T-013 |
| Match weights / threshold / margin | T-017 |
