# Modules (low-level design)

One folder per module; `README.md` inside is its LLD (template: [_TEMPLATE.md](_TEMPLATE.md)). The LLD describes the module as built on `main`; update it in the same PR as the code (Definition of Done).

| Module | Responsibility | Owner | Status | Tasks |
|---|---|---|---|---|
| [web-ui](web-ui/README.md) | Thin React UI for every workflow step | TBD | Implemented (inspection T-009; Phase 2 screens T-012 to T-016) | T-009, T-012…T-019 (UI parts) |
| [api](api/README.md) | FastAPI JSON/SSE API, workflow state machine, approval gates, clarifications | TBD | Implemented (core T-008; plan, code, run, maintain routes T-012 to T-016) | T-008 + all features |
| [inspector](inspector/README.md) | Element extraction, locator ranking + uniqueness, fingerprints | TBD | Implemented (T-007) | T-007 |
| [store](store/README.md) | SQLite schema, immutable versioning, artifacts | TBD | Implemented (core T-004; history UI T-018 todo) | T-004, T-018 |
| [llm-gateway](llm-gateway/README.md) | Gemini/Ollama providers, structured output, usage log | TBD | Implemented (T-005, T-010; usage panel T-019 todo) | T-005, T-010, T-019 |
| [test-designer](test-designer/README.md) | Grounded test case proposals, assumptions, clarifications | TBD | Implemented (T-010, T-012) | T-012 |
| [codegen](codegen/README.md) | POM code generation + validation | TBD | Implemented (T-013) | T-013 |
| [runner](runner/README.md) | Restricted process: inspection + test execution, visible browser | TBD | Implemented (T-006, T-014) | T-006, T-014 |
| [maintainer](maintainer/README.md) | Rescan diff, match scoring, repairs, clarifications | TBD | Rescan + matching implemented (T-016); repairs planned (T-017) | T-016, T-017 |

> **Owners:** assign one team member per component at kickoff and replace `TBD` (4 members, 9 modules — suggested grouping: ① inspector + runner, ② llm-gateway + test-designer, ③ codegen + maintainer, ④ api + store + web-ui).

## Dependency direction
`web-ui → api → {test-designer, codegen, maintainer} → {llm-gateway, store}`; `api → runner → inspector`. Lower layers never import upper layers. `store` and `llm-gateway` import nothing from feature modules. Enforced by import-linter contracts in `pyproject.toml` (checked by `backend/tests/test_architecture.py`; see [SG-002](../SystemGuides/SG-002-developer-workflow.md#module-boundaries)).
