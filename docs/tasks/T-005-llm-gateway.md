# T-005: LLM gateway — Gemini + Ollama, structured output, usage log

- **Status:** Todo
- **Phase:** P1
- **Target:** W+1
- **Modules:** llm-gateway
- **Requirements:** REQ-G6, REQ-G7, REQ-P1-4, REQ-Q7, REQ-Q9, REQ-Q10
- **Depends on:** T-004
- **Plan:** PLAN-005 (to write)
- **TCs:** TC-105
- **Branch / PR:** `feat/T-005-llm-gateway`

## Goal
One provider-agnostic, logged, schema-validated way to call models (ADR-003).

## Scope
- In: verify and pin current Gemini Flash free-tier model + limits (web check, record in ADR); Gemini + Ollama providers; `complete_structured`; JSON schema validation + one repair retry; backoff + fallback; cache with `reused` marking; versioned prompt templates; `LLMCall` logging; untrusted-data prompt framing.
- Out: feature prompts (owned by feature tasks).

## Acceptance criteria
- [ ] Unit tests with a fake provider: logging fields, cache marking, fallback path, schema rejection
- [ ] Manual check against real Gemini and local Ollama (recorded in task notes)
- [ ] `.env.example` and SG-003 (model config) written

## Definition of Done
Standard (see [CLAUDE.md](../../CLAUDE.md)).

## Explain it (code-defense prep)
_To be written on completion._
