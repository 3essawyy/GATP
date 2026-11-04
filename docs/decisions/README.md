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
| [ADR-012](ADR-012-backend-and-dev-tooling.md) | Backend and dev tooling: uv, ruff, mypy strict, poethepoet, single package | Accepted (platform part superseded by ADR-014) | 2026-11-04 |
| [ADR-013](ADR-013-frontend-libraries.md) | Frontend libraries: npm, ESLint+Prettier, Mantine, TanStack Query, openapi-typescript/fetch, Monaco | Accepted | 2026-11-04 |
| [ADR-014](ADR-014-linux-only-platform.md) | Linux-only platform (WSL2 for Windows users) | Accepted | 2026-11-04 |
| [ADR-015](ADR-015-db-access-sqlalchemy-alembic.md) | DB access: SQLAlchemy 2 + Alembic; immutability enforced twice | Accepted | 2026-11-04 |
| [ADR-016](ADR-016-llm-gateway-design.md) | LLM gateway: httpx providers, validated JSON, repair retry, per-attempt log, fake provider | Accepted | 2026-11-04 |
| [ADR-017](ADR-017-runner-unix-socket-jobs.md) | Runner transport: typed HTTP jobs on a private Unix socket | Accepted | 2026-11-04 |
| [ADR-018](ADR-018-inspection-setup-and-usability.md) | Inspection setup steps; usable = unique **and** targets the element; positional CSS never default | Accepted | 2026-11-04 |
| [ADR-019](ADR-019-gates-on-versions-computed-workflow.md) | Approvals bind to immutable versions; workflow state computed | Accepted | 2026-11-04 |
| [ADR-020](ADR-020-test-plan-contract.md) | Test plan as structured grounded data; observable regions; offline examples | Accepted | 2026-11-04 |

## Open decisions (to become ADRs)
| Topic | Decide in |
|---|---|
| Verify Gemini model + limits with a live key (`poe llm-check`) | first session with the key |
| LLM-vs-template split in code generation | T-013 |
| Match weights / threshold / margin | T-017 |
