# ADR-004: Runner isolation model

- **Status:** Accepted
- **Date:** 2026-11-04
- **Session:** S001
- **Related:** REQ-P1-2, REQ-P2-3, REQ-Q5, REQ-Q6, REQ-Q7; modules runner, inspector

## Context
Browser automation and generated tests must run separately from the core app in a restricted process or container with controlled filesystem access, limited to the approved target, with no unrestricted host commands. The browser must be **visible** during demos.

## Decision
A **separate runner process on the host**:
- Own entrypoint (and its own Python environment if needed); started separately from the FastAPI app.
- Accepts only **typed jobs** (`inspect`, `run_tests`) over a local protocol; no arbitrary command execution, no shell.
- Each job gets a **fresh sandbox working directory**; only approved generated files are written into it; outputs (results, screenshots, traces) are copied into `artifacts/`.
- **Target allowlist:** Playwright request routing aborts requests to origins outside the approved target(s).
- Launches **headed Chromium** so the tester sees the browser.
- Timeouts per job and per test.

## Alternatives considered
| Option | Why not |
|---|---|
| Docker + noVNC | Strongest isolation but heavier setup and demo; may be added later behind the same interface |
| Run Playwright inside the API process | Violates REQ-Q5 |

## Consequences
- Process isolation is weaker than a container; limitations must be documented honestly.
- The job interface is designed so a Docker backend could be added without changing callers.
- Generated tests are Python code: they are only run after G2/G3 approval and after AST + locator validation.
