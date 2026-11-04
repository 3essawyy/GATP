# T-006: Runner process — job protocol, sandbox, allowlist, headed browser

- **Status:** Done
- **Phase:** P1
- **Target:** W+1
- **Modules:** runner, api (client), inspector (`LocatorSpec`)
- **Requirements:** REQ-P1-2, REQ-Q5, REQ-Q6
- **Depends on:** T-002
- **Plan:** [PLAN-006](../implementationPlans/PLAN-006-runner.md)
- **ADRs:** [ADR-017](../decisions/ADR-017-runner-unix-socket-jobs.md)
- **TCs:** TC-106 (Pass)
- **Session:** [S004](../sessions/2026-11-04-S004-full-build-run.md)
- **Branch / PR:** `claude/serene-johnson-xtbl4s` → squash-merged to `main`

## Goal
The isolated process that owns every browser (ADR-004).

## Scope
- In: core↔runner transport (ADR); typed jobs (`inspect` stub, `recount`, later `collect`/`run_tests`); per-job sandbox dir; Playwright routing allowlist with blocked-request log; headed Chromium (headless flag for CI); timeouts; api-side client.
- Out: inspection logic (T-007), test execution (T-014).

## Acceptance criteria
- [x] Runner rejects unknown job types and non-allowlisted URLs (HTTP 422; `test_runner_jobs.py`, `test_runner_process.py`)
- [x] Requests to non-allowlisted origins are aborted and logged (two-origin page in `test_runner_browser.py`: the external script never runs, and the script and image are listed in `blocked_requests`)
- [x] Sandbox dir created per job and cleaned up

Manual check: the runner started **headed** under `xvfb-run` and inspected the fixture site over the socket (`status ok`, screenshot saved, redirect to sign-in observed).

## Explain it (code-defense prep)

**What.** `gatp-runner` is a separate process that owns every browser. It listens on a private Unix socket and accepts only two typed jobs today:
- **`inspect`:** open a page and screenshot it. Element extraction comes in T-007.
- **`recount`:** count how many elements each locator matches.

The API talks to it through `RunnerClient`.

**Why:** the brief requires browser automation and generated tests to run separately from the core app, in a restricted process limited to the approved target, with no arbitrary commands (REQ-Q5, REQ-Q6). The only way in is "submit one of these typed jobs", and each job carries its own allowlist.

**How it works:**
1. **Startup:** `main()` creates `data/runner/` with mode 0700, binds `runner.sock`, chmods it to 0600 and gives the bound socket to uvicorn. Only processes of the same OS user can connect, and there's no network port at all.
2. **Validation:** `POST /jobs` gets `{"job": {...}}`. Pydantic validates it against a discriminated union on `type` with `extra="forbid"`. The URL's origin must be in the job's `allowlist`. Anything else gets **HTTP 422 before any code runs**. There is simply no endpoint that takes code or commands.
3. **Execution:** `JobExecutor.run` hands the job to its single worker thread, so one job runs at a time and one browser window is on screen. The job gets a fresh `data/sandbox/job-<id>/` (0700), and Chromium is launched **headed** with service workers blocked.
4. **Network allowlist:** every request passes through `context.route("**/*")`. Requests outside the allowlist are aborted with `blockedbyclient` and appended to `blocked_requests`. `data:`, `blob:` and `about:` are allowed.
5. **Results:** files the job wants to keep (e.g. the screenshot) are copied to `artifacts/jobs/<id>/`, and the sandbox is deleted. The `JobResult` reports status, duration (browser time, kept separate from model time), blocked requests, file paths and data.
6. **Locators as data:** they arrive as `LocatorSpec` data (`{"strategy": "role", "value": "button", "name": "Sign in"}`), and `resolve()` maps them to Playwright calls. No string is ever evaluated.

**Likely examiner questions:**
- *Can the page under test make the browser talk to other sites?* No. Every request is routed through the allowlist check. The test loads a page that pulls a script and an image from a second origin: both are aborted and logged, and the script's side effect (changing the title) never happens.
- *Can someone send the runner a shell command?* There's no job type for it. `{"type": "shell"}` fails validation (422), as do extra fields. The API only exposes typed jobs.
- *Why a Unix socket and not localhost HTTP?* A TCP port on localhost is reachable by every local user and process. The socket file is 0600 in a 0700 directory, so the OS enforces that only our user can submit jobs, without a token to manage.
- *How is this "isolated" if it's not a container?* It's a separate process with its own entrypoint, a private sandbox directory per job, a network allowlist and typed inputs. Test code itself is additionally confined with bubblewrap when `run_tests` arrives (T-014/T-020). These limits are documented honestly (ADR-004).
- *Why one worker thread?* Two reasons. Playwright's sync API must not share a thread with an event loop. And one job at a time keeps the visible browser understandable for the human watching.
