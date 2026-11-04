# Module: runner

- **Owner:** TBD
- **Status:** In progress
- **Code:** `backend/src/gatp/runner/` (separate entrypoint, separate process)
- **Tasks:** T-006, T-014
- **ADRs:** ADR-004, ADR-008, ADR-012

## Responsibility
A restricted, separately started process that executes only typed jobs from the api: `inspect` (opens a visible browser, calls inspector) and `run_tests` (executes approved, validated test code). Enforces the target allowlist and a fresh sandbox working directory per job. No shell access, no arbitrary commands.

## Job contract (draft)
| Job | Input | Output |
|---|---|---|
| `inspect` | `url`, `scope`, `allowlist` | InspectionSnapshot + screenshot |
| `recount` | `url`, locators | counts per locator |
| `collect` | code version files | pytest collection report |
| `run_tests` | code version files, test IDs, `base_url`, `allowlist` | per-test status, duration, error, screenshot paths |

## Restrictions
- Sandbox: `tmp/run-<id>/` created per job, deleted after artifacts are copied.
- Network: Playwright `route("**/*")` aborts non-allowlisted origins; blocked attempts are logged.
- Timeouts: per job and per test (config).
- Browser: headed Chromium locally; headless in CI.
- Execution time is recorded separately from model time (REQ-Q8).

## Implemented so far (T-002 stub)
`gatp-runner` (`runner/main.py`) is a separately started process that configures logging, logs `runner ready`, and idles until SIGINT/SIGTERM (`run(stop: threading.Event)` is the testable core). It opens **no network port and accepts no jobs**, so T-006 can still choose the transport. It shares the project venv with the api (ADR-012); import-linter forbids `runner`/`inspector` from importing `llm_gateway` or `store`.

Tests: `backend/tests/test_runner_stub.py` (in-process start/stop; real subprocess start + SIGTERM on POSIX).

## Known limitations
Process isolation only (no container). Documented in limitations.
