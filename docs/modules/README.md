# Modules (low-level design)

One folder per module; `README.md` inside is its LLD (template: [_TEMPLATE.md](_TEMPLATE.md)). The LLD describes the module as built on `main`; update it in the same PR as the code (Definition of Done).

| Module | Responsibility | Owner | Status | Tasks |
|---|---|---|---|---|
| [web-ui](web-ui/README.md) | Thin React UI for every workflow step | TBD | In progress (skeleton, T-002) | T-009, T-012…T-019 (UI parts) |
| [api](api/README.md) | FastAPI JSON/SSE API, workflow state machine, approval gates, clarifications | TBD | In progress (skeleton, T-002) | T-008 + all features |
| [inspector](inspector/README.md) | Element extraction, locator ranking + uniqueness, fingerprints | TBD | Planned | T-007 |
| [store](store/README.md) | SQLite schema, immutable versioning, artifacts | TBD | Planned | T-004, T-018 |
| [llm-gateway](llm-gateway/README.md) | Gemini/Ollama providers, structured output, usage log | TBD | Planned | T-005, T-010, T-019 |
| [test-designer](test-designer/README.md) | Grounded test case proposals, assumptions, clarifications | TBD | Planned | T-012 |
| [codegen](codegen/README.md) | POM code generation + validation | TBD | Planned | T-013 |
| [runner](runner/README.md) | Restricted process: inspection + test execution, visible browser | TBD | In progress (skeleton, T-002) | T-006, T-014 |
| [maintainer](maintainer/README.md) | Rescan diff, match scoring, repairs, clarifications | TBD | Planned | T-016, T-017 |

> **Owners:** assign one team member per component at kickoff and replace `TBD` (4 members, 9 modules — suggested grouping: ① inspector + runner, ② llm-gateway + test-designer, ③ codegen + maintainer, ④ api + store + web-ui).

## Dependency direction
`web-ui → api → {test-designer, codegen, maintainer} → {llm-gateway, store}`; `api → runner → inspector`. Lower layers never import upper layers. `store` and `llm-gateway` import nothing from feature modules. Enforced by import-linter contracts in `pyproject.toml` (checked by `backend/tests/test_architecture.py`; see [SG-002](../SystemGuides/SG-002-developer-workflow.md#module-boundaries)).
