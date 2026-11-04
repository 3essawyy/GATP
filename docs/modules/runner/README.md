# Module: runner

- **Owner:** TBD
- **Status:** Implemented (transport, inspect stub, recount; T-006)
- **Code:** `backend/src/gatp/runner/` (separate entrypoint, separate process)
- **Tasks:** T-006, T-014
- **ADRs:** ADR-004, ADR-008, ADR-012, ADR-017

## Responsibility
A restricted, separately started process that executes only typed jobs from the api: `inspect` (opens a visible browser, calls inspector) and `run_tests` (executes approved, validated test code). Enforces the target allowlist and a fresh sandbox working directory per job. No shell access, no arbitrary commands.

## Interfaces
| Direction | Interface | Contract |
|---|---|---|
| Provides | HTTP on a Unix socket (`GATP_RUNNER_SOCKET`, 0600) | `GET /health`; `POST /jobs` with `{"job": Job}` → `JobResult`; 422 if the job is invalid |
| Provides | `RunnerClient` (`runner/client.py`) | Used by the api only (import contracts) |
| Consumes | inspector | `LocatorSpec` + `resolve()` (T-006), extraction (T-007) |

## Job contract
| Job (`type`) | Input | Output (`JobResult.data` / `files`) | Since |
|---|---|---|---|
| `inspect` | `url`, `allowlist`, `timeout_s` | `title`, `final_url` / `screenshot` (full extraction in T-007) | T-006 |
| `recount` | `url`, `allowlist`, `locators: [LocatorSpec]` | `counts: [int]` (same order) | T-006 |
| `collect` | code version files | pytest collection report | T-013 |
| `run_tests` | code version files, test IDs, `base_url`, `allowlist` | per-test status, duration, error, screenshots | T-014 |

Every `JobResult` has `job_id`, `type`, `status` (`ok`/`failed`), `duration_ms` (browser/test time, separate from model time), `blocked_requests`, `files` (artifact-relative paths), `data` and `error`.

## Files
| File | Contents |
|---|---|
| `jobs.py` | Pydantic job models (discriminated union, `extra="forbid"`, URL-in-allowlist validator), `JobResult`, `BlockedRequest` |
| `executor.py` | `JobExecutor`: one worker thread, sandbox per job, runs `inspect` / `recount` |
| `browser.py` | `open_page()` (headed unless configured otherwise, service workers blocked), `Allowlist` route handler |
| `sandbox.py` | `job_sandbox()` → `data/sandbox/job-<id>/` (0700, deleted afterwards); `Sandbox.keep()` copies outputs to `artifacts/jobs/<id>/` |
| `server.py` | FastAPI app (`/health`, `/jobs`) |
| `main.py` | `gatp-runner`: binds the 0600 socket in a 0700 dir, runs uvicorn on it |
| `client.py` | `RunnerClient`, `RunnerUnavailableError`, `RunnerRejectedError` |

## Restrictions (enforced)
- **Jobs:** typed only, no shell or code endpoint. An unknown job type or extra field gets HTTP 422.
- **Target:** the URL must be on an allowlisted origin, or the job is rejected before running.
- **Network:** requests to other origins are aborted (`blockedbyclient`) and listed in `blocked_requests`.
- **Files:** a fresh 0700 sandbox per job, removed afterwards; only explicitly kept files reach `artifacts/`.
- **Access:** the socket is 0600 in a 0700 directory, and there's no TCP port.
- **Timeouts:** per job (`timeout_s`, default 30 s, max 600 s), applied as Playwright's default timeout.
- **Browser:** headed Chromium. `GATP_RUNNER_HEADLESS=true` only in CI. `GATP_RUNNER_SLOW_MO_MS` slows actions down for demos.

## Config
| Key | Default | Meaning |
|---|---|---|
| `GATP_RUNNER_SOCKET` | `data/runner/runner.sock` | Unix socket path |
| `GATP_RUNNER_HEADLESS` | `false` | CI only |
| `GATP_RUNNER_SANDBOX_DIR` | `data/sandbox` | Per-job sandboxes |
| `GATP_RUNNER_JOB_TIMEOUT_S` | `60` | Default job timeout used by the api |
| `GATP_RUNNER_SLOW_MO_MS` | `0` | Slow motion for demos |
| `GATP_CHROMIUM_EXECUTABLE` | empty | Use a specific Chromium binary |

## Tests
`test_runner_jobs.py`, `test_runner_browser.py`, `test_runner_process.py` (TC-106).

## Known limitations
- Process isolation, not a container. The runner shares the OS user with the api; test-code confinement (bubblewrap) arrives with `run_tests` in T-014/T-020.
- One job at a time (by design: one visible browser).
