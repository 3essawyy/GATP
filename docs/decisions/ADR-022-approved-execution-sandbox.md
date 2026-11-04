# ADR-022: Approved execution: G3 bound to exact code + target, bubblewrap sandbox, allowlist plugin

- **Status:** Accepted
- **Date:** 2026-11-04
- **Session:** S004
- **Related:** REQ-G5, REQ-P2-3, REQ-Q3, REQ-Q5, REQ-Q6, REQ-Q8, T-014, TC-205, TC-206; refines [ADR-004](ADR-004-runner-isolation.md), [ADR-017](ADR-017-runner-unix-socket-jobs.md)

## Context
Approved tests are real Python code running a real browser. The brief requires execution only after explicit approval, in a restricted process limited to the approved target, with real failures kept visible. S004 agreed on bubblewrap plus limits.

## Decision
- **G3 approves a subject**, not a file: `{code_version_ids, target, tests}`.
  - The API refuses a G3 whose subject differs from the current G2-approved code versions and the project origin.
  - A run re-checks the subject, so a code edit after G3 invalidates the approval.
  - **Each approval authorises one run**, and every rerun needs a new G3.
- **`run_tests` job** (runner): writes the approved files plus GATP's pytest plugin into a fresh sandbox (with its own `pytest.ini`), then runs `pytest` with junit XML and a screenshot for every test.
- **Isolation (`GATP_RUNNER_ISOLATION=bwrap`, default):** bubblewrap.
  - The filesystem is read-only.
  - GATP's `data/` and `artifacts/` folders, `.env` and `~/.ssh`, `~/.config`, … are hidden.
  - Only the sandbox directory (re-bound at its own path) is writable.
  - New PID/IPC/UTS namespaces, `--die-with-parent`, and a cleared environment (no API keys).
  - `process` is a documented, weaker fallback for machines without bubblewrap. Each run records which isolation it used.
- **Network:** the runner's `gatp_run_plugin` adds origin-allowlist routing to every test browser context; other requests are aborted and recorded. Static validation (ADR-021) already bans `subprocess`, `os.system`, `eval`, `page.route` … in generated code.
- **Results:**
  - Per test: outcome, duration, the assertion message (Playwright shows expected vs actual), a stack excerpt and a screenshot (`test-failed-1.png` on failure).
  - Per run: total test time (kept separate from model time), isolation and blocked requests.
  - Failures are stored and shown as-is; nothing rewrites code or assertions.
- **Step status:** the workflow's `run` step shows `failed` when the last run failed.

## Alternatives considered
| Option | Why not |
|---|---|
| Docker per run | Heavier setup on the demo machine; visible browser needs X forwarding |
| Network namespace (`--unshare-net`) | Would also cut the approved target on localhost; routing allowlist + static bans used instead |
| Approve once, run many times | Brief: "explicit approval before … any run or rerun" |

## Consequences
- **Setup:** bubblewrap is a prerequisite (SG-001). Ubuntu 24.04 needs `kernel.apparmor_restrict_unprivileged_userns=0` for unprivileged bwrap; CI sets it.
- **Live progress:** progress is start/finish events over SSE; per-test streaming is not implemented.
