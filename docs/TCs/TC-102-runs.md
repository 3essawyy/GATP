# TC-102 run log: clean setup from SG-001

Definition: [phase1.md § TC-102](phase1.md#tc-102--clean-setup-from-docs). Guide under test: [SG-001](../SystemGuides/SG-001-setup-and-run.md). Platform: [ADR-014](../architectureDecisionRecords/ADR-014-linux-only-platform.md).

## Run 1: 2026-11-04 (S003, after T-002)

- **Machine:** clean `ubuntu:24.04` Docker image, host networking, non-root user `tester` with passwordless sudo.
- **Commit:** `claude/serene-johnson-xtbl4s` @ `bffd77d`, cloned from GitHub inside the container.
- **Baseline added by the tester (not SG-001 steps):** `sudo`, the user account, and this cloud sandbox's egress-proxy CA (`UV_SYSTEM_CERTS=1`, `NODE_EXTRA_CA_CERTS`, `HTTPS_PROXY`). A normal machine doesn't need these.
- **Scope:** api, runner, frontend. The fixture site doesn't exist yet (T-003).

| SG-001 step | Result | Evidence |
|---|---|---|
| 1 apt base packages | Pass | |
| 2 uv (pipx route) | Pass | `uv 0.13.7`, installed with system Python 3.12.3 |
| 2 uv (curl astral.sh route) | Not tested | `astral.sh` blocked by the sandbox network policy |
| 3 Node 22 via nvm | Pass | `v22.23.4` |
| 4 clone | Pass | |
| 5 `uv sync` | Pass | Used Ubuntu's Python 3.12 (no download) |
| 6 `uv run poe web-install` | Pass | |
| 7 `uv run poe browsers` | Not testable here | Chromium CDN blocked by the sandbox (`Download failure`). The same command passes in CI on ubuntu-latest (backend job, PR #1). |
| 8 `.env` | Pass | |
| 9 start api / runner / web | Pass | `runner ready …` logged; `/api/health` OK direct and via the Vite proxy |
| 10 UI | Pass | Chromium (host) on http://localhost:5173 shows **API ok · v0.1.0** |

**Findings:** no undocumented step, and no secret needed. SG-001 needed no changes.

**Status:** Pass for api/runner/frontend. **Remaining for full Pass:** the fixture site section (T-003), then a final run in T-011.

## Run 2: 2026-11-04 (S004, T-011, full scope incl. fixture site and a real inspection)

- **Machine:** clean `ubuntu:24.04` container as in Run 1; cloned `main` at the T-010 merge (`9742f41`).
- **Extra sandbox-only items:** Chromium cannot be downloaded in this sandbox. Following the SG-001 troubleshooting row, the host's Chromium is mounted read-only and set via `GATP_CHROMIUM_EXECUTABLE`. The container has no desktop, so `xvfb` is installed and the runner is started with `xvfb-run` (also an SG-001 troubleshooting row).

| SG-001 step | Result | Evidence |
|---|---|---|
| 1–6 | Pass | as in Run 1 |
| 7 `poe browsers` | Partial | System libraries installed; Chromium download blocked by the sandbox (passes in CI) |
| 8 `.env` | Pass | |
| 9 fixture site + runner + api + web | Pass | `/api/health` via the Vite proxy OK; runner `available: true, headless: false`; fixture serves "Sign in to BookShelf" |
| 10 real use | Pass | `POST /projects` → `POST /pages/1/inspections`: elements `Username, Password, Sign in`, browser time 2187 ms (headed Chromium on Xvfb) |

**Finding:** SG-001 "Verify it worked" pointed at a health badge that, since T-009, only appeared inside a project. **Fixed:** the Projects page now shows *Runner ready* + *API ok*, SG-001 is updated, and the UI walkthrough asserts it.

**Status:** **Pass** (all of SG-001, incl. the fixture site). The only sandbox-specific deviation is the Chromium download, which CI covers.
