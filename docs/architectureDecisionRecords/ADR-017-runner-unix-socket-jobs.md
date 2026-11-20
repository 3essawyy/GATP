# ADR-017: Runner transport: typed HTTP jobs on a private Unix socket

- **Status:** Accepted
- **Date:** 2026-11-04
- **Session:** S004
- **Related:** REQ-Q5, REQ-Q6, T-006, TC-106; refines [ADR-004](ADR-004-runner-isolation.md), [ADR-014](ADR-014-linux-only-platform.md); modules runner, api

## Context
ADR-004 requires the runner to be a separately started process that accepts only typed jobs. The transport was left open (HTTP vs queue vs stdin/stdout). With Linux-only support (ADR-014), Unix domain sockets are available.

## Decision
- **Transport:** the runner is a small FastAPI app (`GET /health`, `POST /jobs`) served by uvicorn **only on a Unix domain socket** (`GATP_RUNNER_SOCKET`, default `data/runner/runner.sock`). The runner binds the socket itself and sets it to **0600** inside a **0700** directory. uvicorn would otherwise chmod its own socket to 0666. There is **no TCP port**.
- **Jobs:** a Pydantic discriminated union on `type`. Today that's `inspect` and `recount`; `collect` and `run_tests` come in T-013/T-014. `extra="forbid"` everywhere. An unknown type or field, or a URL outside the job's `allowlist`, is rejected with HTTP 422 before any code runs.
- **Locators:** jobs carry structured `LocatorSpec` data (`strategy`, `value`, `name`, `exact`), never code strings. The runner builds Playwright locators from that data.
- **Execution:** each job runs on the executor's single worker thread, which serializes jobs (one visible browser at a time). It gets a fresh `0700` sandbox directory that is deleted afterwards, and kept outputs are copied to `artifacts/jobs/<job_id>/`.
- **Network:** `context.route("**/*")` aborts every request whose origin is outside the allowlist (only `data:`/`blob:`/`about:` are exempt) and records it in `JobResult.blocked_requests`. Service workers are blocked so they can't bypass routing.
- **Browser:** Chromium is **headed by default**. `GATP_RUNNER_HEADLESS=true` is for CI only, and the cloud sandbox uses `xvfb-run`.
- **API client:** `gatp.runner.client.RunnerClient` (httpx over the socket). It serializes only, leaving validation to the runner, and raises `RunnerUnavailableError` / `RunnerRejectedError`.

## Alternatives considered
| Option | Why not |
|---|---|
| Localhost TCP + token | Opens a port anyone on the machine can try; needs secret handling |
| Subprocess per job (stdin/stdout) | Runner would no longer be "started separately" (ADR-004); slower browser start per call is similar anyway |
| Job queue in SQLite | Runner would need the store, which import contracts forbid; polling latency |

## Consequences
- Synchronous request/response is enough for inspect/recount. Long `run_tests` jobs (T-014) may add progress events; the API relays them to the UI via SSE.
- Socket permissions are the access control, so the runner must run as the same OS user as the API.
- Tests run the runner as a real subprocess and check the socket mode.
