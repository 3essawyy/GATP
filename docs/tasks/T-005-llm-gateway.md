# T-005: LLM gateway — Gemini + Ollama, structured output, usage log

- **Status:** Done (Gemini verified 2026-11-20; Ollama check pending on a machine that can reach it)
- **Phase:** P1
- **Target:** W+1
- **Modules:** llm-gateway, store
- **Requirements:** REQ-G3, REQ-P1-4, REQ-Q7, REQ-Q8–Q10
- **Depends on:** T-004
- **Plan:** [PLAN-005](../implementationPlans/PLAN-005-llm-gateway.md)
- **ADRs:** [ADR-016](../architectureDecisionRecords/ADR-016-llm-gateway-design.md)
- **Guides:** [SG-003](../SystemGuides/SG-003-models.md)
- **TCs:** TC-105 (automated Pass; live part pending)
- **Session:** [S004](../sessions/2026-11-04-S004-full-build-run.md)
- **Branch / PR:** `claude/serene-johnson-xtbl4s` → squash-merged to `main`

## Goal
One provider-agnostic, logged, schema-validated way to call models (ADR-003).

## Scope
- In: verify and pin current Gemini Flash free-tier model + limits; Gemini + Ollama providers; `complete_structured`; JSON schema validation + one repair retry; backoff + fallback; cache with `reused` marking; versioned prompt templates; `LLMCall` logging; untrusted-data prompt framing.
- Out: feature prompts (owned by feature tasks).

## Acceptance criteria
- [x] Unit tests with a fake provider: logging fields, cache marking, fallback path, schema rejection
- [x] Manual check against real Gemini: `llm-check` OK on 2026-11-20 (`gemini-3.5-flash`, see SG-003 §6).
- [ ] Manual check against local Ollama from the WSL runner machine. `uv run poe llm-check` is the check, and SG-003 §6 is where the result goes.
- [x] `.env.example` and SG-003 (model config) written

## Notes
- **Model pinning:** Google's docs host is blocked in the cloud sandbox. `gemini-2.5-flash` was the original default (free-tier limits 10 RPM / 250k TPM / 250 RPD, from a search snippet of Google's rate-limit page). On 2026-11-20 it returned HTTP 404 (no longer available to new users), so the default is now `gemini-3.5-flash`, confirmed with `poe llm-check`.
- `poe llm-check` here (no key, no Ollama) reports `gemini: unavailable (key not set)` and `ollama: not reachable`, both logged as `unavailable` rows. That's the expected behavior.

## Explain it (code-defense prep)

**What.** `gatp.llm_gateway` is the only code in GATP that talks to a language model. Feature modules call `gateway.complete_structured("template-id", inputs, SomePydanticModel, page_data=…)` and get back either a validated `SomePydanticModel` instance or an exception. Every attempt is written to the `llm_calls` table.

**Why:**
- **Brief requirements:**
  - Only free or local models (REQ-G3).
  - Visible usage: tokens, latency, fresh vs reused (REQ-Q8–Q10).
  - Grounded outputs.
  - Page text treated as untrusted (REQ-Q7).
- **One gateway:** putting all of this in one place means every feature gets it for free, and there's exactly one thing to defend. That covers caching, rate limits, fallback, validation and logging.
- **Structured JSON validated by Pydantic:** the only way to *guarantee* outputs are usable and grounded. Free text can't be checked.

**How it works (one call):**
1. **Template:** looked up by id. Templates have a version, and the registry refuses a changed prompt with the same version, so every log row names the exact prompt that produced it.
2. **Rendering:** the instructions come from the template. Anything that came from the page is JSON-encoded inside `<untrusted_page_data>…</untrusted_page_data>`. A fake closing tag inside the data is escaped, and the system prompt says that content is data, never instructions.
3. **Cache key:** a SHA-256 over the template id/version, the rendered text and the JSON schema. If an identical request already succeeded, the stored answer is re-validated and returned, and a new row with `cache=reused` is logged, so reuse is visible rather than hidden.
4. **Providers in order** (Gemini, then Ollama):
   - A 429/5xx/network error triggers exponential backoff (2 s, 4 s) and a retry.
   - A missing key or unreachable Ollama goes straight to the next provider.
   - Each failure is logged.
5. **Validation:** the answer must parse into the Pydantic schema and pass the optional `check` (e.g. "all element ids exist").
   - **First failure:** a *repair retry* resends the request with the validation error.
   - **Second failure:** the next provider is tried.
   - **Nothing valid:** `LLMOutputError` with all attempts attached.
6. **Usage logging:** token counts come from the provider (`usageMetadata` for Gemini, `prompt_eval_count`/`eval_count` for Ollama). If a provider doesn't report them, they're estimated at ~4 characters per token and flagged `tokens_estimated`.

**Likely examiner questions:**
- *How do you stop prompt injection from the page?* Page text is only ever data inside a delimited JSON block. Rules in the system prompt say to ignore instructions found there, and outputs are schema-validated with element ids checked against the snapshot. Even a fooled model can't make GATP *do* anything: actions only happen after human approval gates.
- *What if Gemini's free quota runs out during the demo?* Backoff, then automatic fallback to the local Ollama model. Repeated identical requests are served from the cache (`reused`), and the usage panel shows all of it.
- *How do you know the tokens are real?* They're provider-reported where available. Otherwise they're estimated and labelled as such, never presented as exact.
- *How is this tested without an API key?* With a scripted `FakeProvider` (gateway logic) and `httpx.MockTransport` (exact Gemini/Ollama request and response formats). CI never calls a real model.
- *Why not use the official SDKs?* Two plain HTTP calls are easier to read, test and explain, and add no dependencies.
