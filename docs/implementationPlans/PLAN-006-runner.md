# PLAN-006: Runner process (for T-006)

- **Task:** [T-006](../tasks/T-006-runner-skeleton.md)
- **Status:** Executed
- **Date:** 2026-11-04

## Approach
Replace the T-002 stub with the real runner described in [ADR-017](../decisions/ADR-017-runner-unix-socket-jobs.md): typed jobs → `JobExecutor` (one worker thread, sandbox per job, allowlist routing, headed Chromium) → `JobResult`, served on a private Unix socket. Add `LocatorSpec` in the inspector, since the runner, inspector and codegen all share it.

## Steps
1. Settings `GATP_RUNNER_*`.
2. `inspector/locators.py` (`LocatorSpec`, `resolve`, `to_python`).
3. `runner/jobs.py`, `sandbox.py`, `browser.py`, `executor.py`, `server.py`, `main.py`, `client.py`.
4. Tests (TC-106): job validation, sandbox lifecycle, allowlist blocking against a two-origin page, recount, navigation failure, the real subprocess on a socket (mode 0600, health, inspect, 422 rejections, missing runner).
5. Manual: headed run under `xvfb-run` against the fixture site.
6. Docs: ADR-017, runner LLD, SG-001, TC-106, task doc.

## Tests to add
| Test | Proves |
|---|---|
| `test_runner_jobs.py` | Unknown/extra/disallowed jobs rejected; allowlist normalised; locator rendering; sandbox 0700 + cleanup + confinement |
| `test_runner_browser.py` | Inspect stub works; external script/image aborted and logged (the script never ran); recount counts; failures reported |
| `test_runner_process.py` | Separate process, socket 0600 in 0700 dir, health + inspect over the socket, 422 for unknown/disallowed jobs, clear error if the runner is down |

## Risks / open questions
| Item | Mitigation / decision |
|---|---|
| uvicorn chmods UDS to 0666 | Bind the socket ourselves and pass it via `Server.run(sockets=[…])` |
| Playwright sync API vs. caller's event loop | Dedicated worker thread in `JobExecutor` |

## Deviations (filled after execution)
- A first attempt used `umask(0o177)`. That broke Chromium's own temp directories and was replaced with self-bound sockets.
