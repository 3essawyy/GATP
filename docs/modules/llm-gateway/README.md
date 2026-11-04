# Module: llm-gateway

- **Owner:** TBD
- **Status:** Planned
- **Code:** `backend/gatp/llm_gateway/`
- **Tasks:** T-005, T-010, T-019
- **ADRs:** ADR-003

## Responsibility
The only place that talks to model providers. Provides a provider-agnostic `complete_structured(template_id, inputs, schema)` call, handles retries/backoff/fallback, validates JSON against the schema, and logs every call. Holds versioned prompt templates.

## Interfaces
| Direction | Interface | Contract |
|---|---|---|
| Provides | `complete_structured(...)` | Returns validated object + `LLMCall` record |
| Consumes | Gemini API (free tier) | API key from `.env` |
| Consumes | Ollama HTTP API | Local, `OLLAMA_HOST` |
| Consumes | store | Writes `LLMCall` rows |

## LLMCall log fields
`call_id, timestamp, provider, model, model_version, template_id, template_version, input_tokens, output_tokens, tokens_source (provider|estimated), latency_ms, cache (fresh|reused), status, error, project_id, page_id, purpose`

## Prompt-injection posture
Page-derived text is passed only inside delimited data fields (JSON), with a system instruction that the data is untrusted and must not be followed as instructions. Outputs are schema-validated; element references must resolve to snapshot element IDs.

## Config
| Key | Default | Meaning |
|---|---|---|
| `LLM_PRIMARY` | `gemini` | Primary provider |
| `GEMINI_MODEL` | pinned in T-005 | Model ID |
| `GEMINI_API_KEY` | — | From `.env` |
| `LLM_FALLBACK` | `ollama` | Fallback provider |
| `OLLAMA_MODEL` | `qwen2.5-coder:3b` (verify in T-005) | Local model |
| `LLM_CACHE` | `on` | Reuse identical calls (marked `reused`) |

## Known limitations
Free-tier rate limits; fallback quality lower. Documented in SystemGuides.
