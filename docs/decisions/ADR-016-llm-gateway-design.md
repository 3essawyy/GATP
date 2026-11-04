# ADR-016: LLM gateway design: plain-HTTP providers, validated JSON, per-attempt logging, fake provider

- **Status:** Accepted
- **Date:** 2026-11-04
- **Session:** S004
- **Related:** REQ-G3, REQ-P1-4, REQ-Q7, REQ-Q8–Q10, T-005, TC-105; refines [ADR-003](ADR-003-llm-providers.md); module llm-gateway

## Context
ADR-003 chose Gemini Flash (free tier) as primary and Ollama as fallback, but left open the model ID, the call/validation/logging mechanics, and how to develop and test without a key. The cloud sandbox can't reach Ollama's model registry or Google's docs host, and CI must never call a paid or rate-limited API.

## Decision
- **Providers are thin `httpx` clients**, not vendor SDKs:
  - Gemini `models/{model}:generateContent` with `responseMimeType: application/json` + `responseJsonSchema`.
  - Ollama `/api/chat` with `format: <json schema>`.
  - Each request is one readable JSON body, and the dependency surface stays small.
- **Default models:**
  - `gemini-2.5-flash`. Free-tier limits as quoted from Google's rate-limit page via search, 2026-11-04: 10 RPM / 250k TPM / 250 RPD. **Not yet verified against a live key.** `uv run poe llm-check` lists the models the key can use and makes one call. The first session with the key runs it, and SG-003 records the result.
  - Ollama `qwen2.5-coder:3b`.
  - Both are configurable via `GATP_GEMINI_MODEL` / `GATP_OLLAMA_MODEL`.
- **`complete_structured(template_id, inputs, schema, page_data=, check=)`** is the only call API:
  1. **Render** a versioned `PromptTemplate`. Page data is JSON inside `<untrusted_page_data>`, a closing tag inside the data is escaped, and system rules say the data is not instructions.
  2. **Cache:** an identical request (template id+version, rendered text, schema) with a successful fresh answer is **reused**. The reuse is logged as its own row with `cache=reused`.
  3. **Ask providers in order.** Retryable errors (429, 5xx, transport) back off exponentially (`GATP_LLM_BACKOFF_S`, doubling, `GATP_LLM_MAX_RETRIES`). "Unavailable" (no key, Ollama down, model not pulled) skips straight to the next provider.
  4. **Validate** with Pydantic plus an optional semantic `check` (e.g. "every element id exists in the snapshot"). On failure there is **one repair retry** that includes the error text. If that fails too, the next provider is tried, and if none succeeds `LLMOutputError` is raised.
  5. **Log every attempt** (success, invalid output, rate limit, unavailable) to `llm_calls`: provider, model, model version, template id + version, tokens (provider-reported, or estimated at ~4 chars/token and flagged), latency, cache, status, error, raw response.
- **`fake` provider:** a deterministic, scriptable provider for unit tests and CI. As `GATP_LLM_PRIMARY=fake` it produces minimal schema-valid answers for offline UI work. Its rows always say `provider=fake`.

## Alternatives considered
| Option | Why not |
|---|---|
| `google-genai` / `ollama` SDKs | Extra dependencies; harder to show exactly what is sent; mocking via HTTP is simpler |
| Free-form text + regex parsing | Not reliably groundable; structured output + schema validation is required by HLD §5 |
| Cache inside the provider | The cache must be visible in the usage log (`reused`) and work across providers |
| Unlimited repair retries | Burns free-tier quota; one retry, then fail visibly |

## Consequences
- Prompt changes require a version bump (the registry rejects an edited template with the same version), so usage rows stay attributable.
- Real-model checks (TC-105 manual part, TC-111) need a key and a session started after the key was added.
- Token counts for Ollama and fake are provider-reported or estimated and are labelled as such; the UI must show the label (T-019).
