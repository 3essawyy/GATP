# ADR-003: LLM providers and usage logging

- **Status:** Accepted
- **Date:** 2026-11-04
- **Session:** S001
- **Related:** REQ-G6, REQ-G7, REQ-P1-4, REQ-P2-5, REQ-Q8–Q10; module llm-gateway

## Context
Only free-tier APIs or local/open-source models are allowed. Live demos must not fail because of a rate limit. Token usage and latency must be visible.

## Decision
- **Primary:** Google **Gemini Flash** via the free tier (long context, structured JSON output, provider-reported token counts). The exact model ID is pinned in T-005 after checking current free-tier availability and limits.
- **Fallback:** **Ollama** local model behind the same interface. Demo machine has 16 GB RAM (GPU unconfirmed) → default to a **~3B coder model** (e.g., `qwen2.5-coder:3b`); a 7B model is an optional, slower setting.
- One `llm-gateway` provider abstraction; provider/model chosen by config, not code.
- Every call is logged: provider, model, prompt template ID, input/output tokens (provider-reported, or flagged `estimated`), latency, `fresh|reused`, success/error.
- Identical requests may be served from a cache; such responses are marked `reused` and shown as such.
- Rate-limit handling: backoff + optional automatic fallback, always visible in the UI.

## Alternatives considered
| Option | Why not |
|---|---|
| Local only | 16 GB RAM machine → small models, weaker quality |
| Groq | Tighter daily limits, shorter context |
| OpenRouter free models | Availability and limits change often |

## Consequences
- API key in `.env` only; `.env.example` documents it.
- Fallback outputs may be lower quality — document this in limitations.
- Ollama model must be pulled during setup (SystemGuide).
