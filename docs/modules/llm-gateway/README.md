# Module: llm-gateway

- **Owner:** TBD
- **Status:** Implemented (gateway core, T-005)
- **Code:** `backend/src/gatp/llm_gateway/`
- **Tasks:** T-005, T-010, T-019
- **ADRs:** ADR-003, ADR-016

## Responsibility
The only place that talks to model providers. Provides a provider-agnostic `complete_structured(template_id, inputs, schema)` call, handles retries/backoff/fallback, validates JSON against the schema, and logs every call. Holds versioned prompt templates.

## Interfaces
| Direction | Interface | Contract |
|---|---|---|
| Provides | `complete_structured(...)` | Returns validated object + `LLMCall` record |
| Consumes | Gemini API (free tier) | API key from `.env` |
| Consumes | Ollama HTTP API | Local, `OLLAMA_HOST` |
| Consumes | store | Writes `LLMCall` rows |

## Files
| File | Contents |
|---|---|
| `gateway.py` | `LLMGateway.complete_structured`, `LLMResult`, `LLMOutputError`, `LLMUnavailableError`, `make_provider`, `request_hash`, `estimate_tokens` |
| `providers.py` | `Provider` protocol; `GeminiProvider`, `OllamaProvider` (httpx), `FakeProvider`; error types `RateLimitedError`, `ProviderUnavailableError`, `ProviderError` |
| `templates.py` | `PromptTemplate(id, version, system, user)`, `TemplateRegistry`/`registry`, `UNTRUSTED_RULES`, the `ping` template |
| `check.py` | `uv run poe llm-check` |

## Call sequence (`complete_structured`)
1. Render the template; page data goes JSON-encoded into `<untrusted_page_data>` (closing tag escaped).
2. `request_hash` = SHA-256 of template id + version + rendered system/user + JSON schema.
3. Cache (if on): latest `ok`+`fresh` row with that hash → validate → log a `reused` row → return.
4. For each provider (primary, fallback): call with backoff on retryable errors (log each failure); validate with Pydantic + optional `check`; invalid → log `invalid_output`, **one repair retry** with the error text; still invalid → next provider.
5. Nothing valid → `LLMOutputError`; nothing reachable → `LLMUnavailableError`. Both carry every logged attempt.

## LLMCall log fields (table `llm_calls`)
`id, created_at, project_id, purpose (= template id), template_version, provider, model, model_version, request_hash, input_tokens, output_tokens, tokens_estimated, latency_ms, cache (fresh|reused), status (ok|invalid_output|rate_limited|unavailable|error), error, response`

## Prompt-injection posture
Page-derived text is passed only inside delimited data fields (JSON), with a system instruction that the data is untrusted and must not be followed as instructions. Outputs are schema-validated; element references must resolve to snapshot element IDs.

## Config
| Key | Default | Meaning |
|---|---|---|
| `GATP_LLM_PRIMARY` | `gemini` | Primary provider (`gemini`/`ollama`/`fake`) |
| `GATP_LLM_FALLBACK` | `ollama` | Fallback provider (empty = none) |
| `GATP_GEMINI_API_KEY` | — | From `.env` |
| `GATP_GEMINI_MODEL` | `gemini-3.5-flash` | Model ID (verify with `poe llm-check`) |
| `GATP_OLLAMA_HOST` / `GATP_OLLAMA_MODEL` | `http://127.0.0.1:11434` / `qwen2.5-coder:3b` | Local model |
| `GATP_LLM_CACHE` | `true` | Reuse identical calls (marked `reused`) |
| `GATP_LLM_TIMEOUT_S`, `GATP_LLM_MAX_RETRIES`, `GATP_LLM_BACKOFF_S` | 120, 2, 2 | Timeouts and backoff |

Full guide: [SG-003](../../SystemGuides/SG-003-models.md).

## Tests
`test_llm_gateway.py` (logging fields, cache marking, repair retry, semantic check, backoff, fallback, schema rejection, untrusted framing, template versioning) and `test_llm_providers.py` (Gemini/Ollama request bodies, usage parsing and errors via `httpx.MockTransport`). TC-105.

## Known limitations
- Free-tier rate limits; fallback quality is lower (SG-003).
- Token counts for Ollama/fake may be estimated (~4 chars/token) and are labelled.
- The default Gemini model and its limits are taken from Google's docs as of 2026-11-04 and are not yet verified with a live key (see SG-003 §6).
