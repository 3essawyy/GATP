# SG-003: Model configuration, resources and rate limits

- **Audience:** tester | developer | examiner
- **Last verified:** 2026-11-20 (real Gemini call via `llm-check`, see §6). Real Ollama call: pending (team Linux machine).
- **Design:** [ADR-003](../decisions/ADR-003-llm-providers.md), [ADR-016](../decisions/ADR-016-llm-gateway-design.md), [llm-gateway LLD](../modules/llm-gateway/README.md)

GATP uses only free or local models. Gemini (free tier) is the primary, and a local Ollama model is the fallback. Nothing paid is required.

## 1. Gemini (primary)
1. Create a free API key at https://aistudio.google.com/apikey (Google account, no billing).
2. Put it in `.env` (gitignored, never commit it):
   ```bash
   echo 'GATP_GEMINI_API_KEY=your-key-here' >> .env
   ```
3. Check it:
   ```bash
   uv run poe llm-check
   ```
   Expected: `OK via gemini model=gemini-3.5-flash …` with token counts and latency. The command also lists which Flash models your key can call. If `gemini-3.5-flash` is missing, set `GATP_GEMINI_MODEL` to one that's listed.

Free-tier limits are per Google Cloud project and change over time. Check https://ai.google.dev/gemini-api/docs/rate-limits. When a limit is hit, GATP backs off (2 s, 4 s), then falls back to Ollama, and the usage log shows `rate_limited` rows.

## 2. Ollama (fallback, local)
1. Install it from https://ollama.com/download (Linux: `curl -fsSL https://ollama.com/install.sh | sh`).
2. Pull the default model (~2 GB):
   ```bash
   ollama pull qwen2.5-coder:3b
   ```
3. Make sure it's running (`ollama serve`, usually a background service) on `http://127.0.0.1:11434`.

| Machine | Suggested `GATP_OLLAMA_MODEL` | Notes |
|---|---|---|
| 16 GB RAM, CPU only | `qwen2.5-coder:3b` (default) | ~2 GB RAM; slow but usable as a fallback |
| 16 GB RAM + GPU, or patient | `qwen2.5-coder:7b` | Better JSON quality, ~5 GB, noticeably slower on CPU |

The fallback answers are lower quality than Gemini. GATP still validates them against the same schemas, and invalid answers are rejected rather than used.

## 3. Offline / development: `fake`
`GATP_LLM_PRIMARY=fake` returns minimal schema-valid answers without any network access. Use it only to click through the UI offline: its answers aren't meaningful, and the usage panel labels them `fake`.

## 4. All settings
| Key | Default | Meaning |
|---|---|---|
| `GATP_LLM_PRIMARY` | `gemini` | `gemini` \| `ollama` \| `fake` |
| `GATP_LLM_FALLBACK` | `ollama` | Second provider; empty = none |
| `GATP_GEMINI_API_KEY` | — | Free-tier key (secret, `.env` only) |
| `GATP_GEMINI_MODEL` | `gemini-3.5-flash` | Model ID |
| `GATP_OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama server |
| `GATP_OLLAMA_MODEL` | `qwen2.5-coder:3b` | Local model |
| `GATP_LLM_CACHE` | `true` | Reuse identical successful calls (logged as `reused`) |
| `GATP_LLM_TIMEOUT_S` | `120` | HTTP timeout per call |
| `GATP_LLM_MAX_RETRIES` | `2` | Retries per provider on 429/5xx/network errors |
| `GATP_LLM_BACKOFF_S` | `2` | First backoff, doubling each retry |

## 5. What gets logged (usage evidence)
Each attempt is one row in `llm_calls`: provider, model, model version reported by the provider, prompt template id + version, input/output tokens (`estimated` when the provider doesn't report them), latency in ms, `fresh`/`reused`, status (`ok`, `invalid_output`, `rate_limited`, `unavailable`, `error`), and the raw response. The UI's usage panel (T-010/T-019) shows these rows, with test execution time shown separately.

## 6. Verification record
| Date | Provider / model | Result | By |
|---|---|---|---|
| 2026-11-04 | fake | `poe llm-check` path and 20 gateway/provider tests pass | Claude (S004) |
| 2026-11-20 | gemini / gemini-3.5-flash (provider reports version `gemini-3.6-flash`) | `llm-check` OK: 136 in / 12 out tokens, 40.3 s latency (free tier under load). The old default `gemini-2.5-flash` returned HTTP 404 ("no longer available to new users"); `gemini-3.8-flash` and `gemini-flash-latest` returned 503/timeouts. Default changed to `gemini-3.5-flash`, timeout to 120 s | Claude (user's key) |
| _pending_ | ollama / qwen2.5-coder:3b | Run on the team's Linux machine and record here | team |

## Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| `gemini: GATP_GEMINI_API_KEY is not set` | No key in `.env` | Step 1.2 |
| `ollama: not reachable at …` | Ollama not running | `ollama serve` |
| `model 'qwen2.5-coder:3b' not found` | Model not pulled | `ollama pull qwen2.5-coder:3b` |
| Many `rate_limited` rows | Free-tier quota exhausted | Wait (per-minute/day limits), rely on the fallback, or reuse cached answers |
| `invalid_output` rows | Model returned JSON not matching the schema | The gateway retries once with the error, then falls back, then reports the failure; small local models do this more often |
