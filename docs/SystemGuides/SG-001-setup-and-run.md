# SG-001: Setup and run (api, runner, frontend)

- **Audience:** tester | developer | examiner
- **Last verified:** 2026-11-04 on Linux (cloud container, Python 3.12 via uv, Node 22) at the T-002 merge commit. **Not yet verified on Windows/macOS**; that happens during [TC-102](../TCs/phase1.md#tc-102--clean-setup-from-docs).
- **Fixture site:** added in T-003 (this guide gains a section then).

Every command below runs from the **repository root**, works the same in PowerShell, cmd, bash and zsh, and needs no Make.

## Prerequisites
| Tool | Version | Install |
|---|---|---|
| Git | any | https://git-scm.com |
| **uv** | ≥ 0.5 | Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` · macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **Node.js** | ≥ 22.12 (includes npm) | https://nodejs.org (LTS) |

You don't need to install Python yourself: uv downloads Python 3.12 automatically (pinned in `.python-version`).

## Steps
1. Clone and enter the repo:
   ```bash
   git clone https://github.com/3essawyy/GATP.git
   ```
   ```bash
   cd GATP
   ```
2. Install the Python environment (creates `.venv`, installs exact versions from `uv.lock`):
   ```bash
   uv sync
   ```
3. Install frontend dependencies:
   ```bash
   uv run poe web-install
   ```
4. Download the Chromium build Playwright uses (needed from T-006 on; on Linux add `--with-deps` if system libraries are missing):
   ```bash
   uv run poe browsers
   ```
5. Optional: copy `.env.example` to `.env` and adjust. All keys have defaults; no secrets are needed yet.
6. Start the three processes, **each in its own terminal**:
   ```bash
   uv run poe api
   ```
   ```bash
   uv run poe runner
   ```
   ```bash
   uv run poe web
   ```
7. Open http://localhost:5173.

| Process | Command | Address | Stop |
|---|---|---|---|
| API (FastAPI, auto-reload) | `uv run poe api` | http://127.0.0.1:8000 (docs at `/docs`) | Ctrl+C |
| Runner (stub until T-006) | `uv run poe runner` | none (logs only) | Ctrl+C |
| Frontend (Vite dev server) | `uv run poe web` | http://localhost:5173 | Ctrl+C |

`uv run poe` with no task lists every available task.

## Verify it worked
- The top-right badge in the UI shows **API ok · v0.1.0** (green). If the API is stopped it turns red: **API unreachable**.
- http://127.0.0.1:8000/api/health returns `{"status":"ok","app":"GATP","version":"0.1.0"}`.
- The runner terminal prints `runner ready (no jobs yet; job protocol arrives in T-006)`.

## Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` | uv not on PATH after install | Open a new terminal (Windows: sign out/in), or follow the installer's PATH hint |
| `npm: command not found` / `npm ERR! engine` | Node missing or < 22.12 | Install Node 22 LTS |
| Vite: `Port 5173 is already in use` | Another dev server running | Stop it; the port is fixed (`strictPort`) so the documented URL stays valid |
| Badge says **API unreachable** | API not running, or on another port | Start `uv run poe api`; if you changed the port, set `GATP_API_URL` for the frontend too |
| `[Errno 98/10048] address already in use` on 8000 | Old API process still running | Stop it, or set `GATP_API_PORT` in `.env` and `GATP_API_URL` for Vite |
| PowerShell blocks the uv installer | Execution policy | Use the exact command above (`-ExecutionPolicy ByPass`) |
