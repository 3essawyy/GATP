# PLAN-005: LLM gateway (for T-005)

- **Task:** [T-005](../tasks/T-005-llm-gateway.md)
- **Status:** Executed
- **Date:** 2026-11-04

## Approach
Implement ADR-003 as described in [ADR-016](../architectureDecisionRecords/ADR-016-llm-gateway-design.md): httpx providers (Gemini, Ollama, fake) and one `complete_structured` call that handles templates, the cache, backoff, fallback, validation with one repair retry, and logging of every attempt through a new `LlmCallRepository` in the store. A migration (`0002`) adds `template_version` to `llm_calls`.

## Steps
1. Settings `GATP_LLM_*`, `GATP_GEMINI_*`, `GATP_OLLAMA_*`; `.env.example`.
2. Store: `llm_calls.py` repository; migration `0002_llm_call_template_version`.
3. `providers.py`, `templates.py`, `gateway.py`, `check.py` (+ `poe llm-check`).
4. Tests: gateway behavior with `FakeProvider`; provider wire formats with `httpx.MockTransport`.
5. Docs: ADR-016, SG-003, LLD, TC-105, task doc.

## Tests to add
| Test | Proves |
|---|---|
| `test_llm_gateway.py` | Logged fields, `reused` marking, cache off, repair retry, semantic check, schema rejection → fallback → error, backoff timings, rate-limit fallback, unavailable → fallback, untrusted framing, template version bump |
| `test_llm_providers.py` | Gemini/Ollama request bodies, usage/model-version parsing, 429/5xx/400 mapping, unreachable/missing model |

## Risks / open questions
| Item | Mitigation / decision |
|---|---|
| Google docs host blocked in the sandbox → can't verify current free-tier model/limits | Configurable model; `poe llm-check` lists the models the key can use; verification recorded in SG-003 §6 |
| No key in this session | Fake provider for all automated tests; live check deferred to a new session |

## Deviations (filled after execution)
- Manual live checks against Gemini and Ollama (an acceptance criterion) are deferred: no key in this session, and Ollama is unreachable in the sandbox. Recorded in T-005 and SG-003 §6.
