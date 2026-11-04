# SG-001: Setup and run (api, runner, frontend, fixture site)

- **Audience:** tester | developer | examiner
- **Platform:** **Linux** (Ubuntu 24.04 reference; Windows users run it inside **WSL2 Ubuntu**). See [ADR-014](../decisions/ADR-014-linux-only-platform.md).
- **Last verified:** 2026-11-04, clean `ubuntu:24.04` container, non-root user with sudo, at the T-002 follow-up commit. See the [TC-102 run log](../TCs/TC-102-runs.md).

Run every command from the **repository root** unless the step says otherwise.

## Prerequisites
| Tool | Version | Why |
|---|---|---|
| git, curl, ca-certificates | any | clone, installers |
| **uv** | ≥ 0.5 | Python + dependencies (ADR-012) |
| **Python** | 3.12 | uv uses the system `python3.12` if present (Ubuntu 24.04 ships it), otherwise downloads it |
| **Node.js** | ≥ 22.12 (includes npm) | frontend |

## Steps
1. Install base packages:
   ```bash
   sudo apt-get update && sudo apt-get install -y git curl ca-certificates
   ```
2. Install **uv**, using one of these:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   or, from PyPI through Ubuntu's pipx:
   ```bash
   sudo apt-get install -y pipx && pipx install uv && pipx ensurepath
   ```
   Then open a new terminal (or `source ~/.bashrc`) so `uv` is on `PATH`, and check it with `uv --version`.
3. Install **Node.js 22** with nvm (no sudo needed):
   ```bash
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
   ```
   ```bash
   source ~/.nvm/nvm.sh && nvm install 22
   ```
   Check it with `node --version` (it must print v22.12 or newer).
4. Clone and enter the repo:
   ```bash
   git clone https://github.com/3essawyy/GATP.git && cd GATP
   ```
5. Install the Python environment (creates `.venv`, installs exact versions from `uv.lock`):
   ```bash
   uv sync
   ```
6. Install frontend dependencies:
   ```bash
   uv run poe web-install
   ```
7. Install Chromium and its system libraries for Playwright. It's needed from T-006 on and asks for your sudo password for the libraries:
   ```bash
   uv run poe browsers
   ```
8. Optional: `cp .env.example .env` and adjust. All keys have defaults; no secrets are needed yet.
9. Start the three processes, **each in its own terminal**:
   ```bash
   uv run poe api
   ```
   ```bash
   uv run poe runner
   ```
   ```bash
   uv run poe web
   ```
10. Open http://localhost:5173.

| Process | Command | Address | Stop |
|---|---|---|---|
| API (FastAPI, auto-reload) | `uv run poe api` | http://127.0.0.1:8000 (docs at `/docs`) | Ctrl+C |
| Runner (browser jobs) | `uv run poe runner` | Unix socket `data/runner/runner.sock` (no port) | Ctrl+C |
| Frontend (Vite dev server) | `uv run poe web` | http://localhost:5173 | Ctrl+C |

`uv run poe` with no task lists every available task.

### Fixture site (BookShelf)
Our own test website, documented in [fixtures/README.md](../../fixtures/README.md). In a fourth terminal:
```bash
uv run poe fixtures v1
```
It serves on http://127.0.0.1:8090/ (sign in with `tester` / `secret123`). For the maintenance demo, stop it with Ctrl+C and start the modified version on the same URL:
```bash
uv run poe fixtures v2
```

## Verify it worked
- The Projects page shows two green badges at the top right: **Runner ready** and **API ok · v0.1.0**. If the API is stopped the badge turns red (**API unreachable**); if the runner is not running it shows **Runner offline**.
- `curl http://127.0.0.1:8000/api/health` returns `{"status":"ok","app":"GATP","version":"0.1.0"}`.
- The runner terminal prints `runner ready on unix socket data/runner/runner.sock, headed (visible browser)`. A Chromium window opens whenever GATP inspects a page.
- http://127.0.0.1:8090/ shows "Sign in to BookShelf", and the footer says "v1" (or "v2").

## Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| `uv: command not found` | `~/.local/bin` not on PATH yet | `source ~/.bashrc` or open a new terminal |
| `node: command not found` in a new terminal | nvm not loaded | `source ~/.nvm/nvm.sh` (the nvm installer adds this to `~/.bashrc`) |
| `npm ERR! engine` / Vite refuses to start | Node < 22.12 | `nvm install 22` |
| Vite: `Port 5173 is already in use` | Another dev server running | Stop it; the port is fixed (`strictPort`) so the documented URL stays valid |
| Badge says **API unreachable** | API not running, or on another port | Start `uv run poe api`; if you changed the port, also set `GATP_API_URL` for the frontend |
| `address already in use` on 8000 | Old API process still running | `fuser -k 8000/tcp`, or set `GATP_API_PORT` in `.env` and `GATP_API_URL` for Vite |
| `poe browsers` fails on missing libraries | No sudo rights | Ask an admin to run `sudo $(uv run which playwright) install-deps chromium` |
| `poe browsers` can't download Chromium (blocked network) | Corporate/sandbox proxy | Point `GATP_CHROMIUM_EXECUTABLE` in `.env` at an existing Chromium binary |
| Fixture: `Address already in use` on 8090 | Other version still running | Stop it first (Ctrl+C), or `python fixtures/serve.py v2 --port 8091` |
| WSL2: browser window doesn't appear | WSLg missing | Use Windows 11 / recent WSL (`wsl --update`) |
| Runner fails with `Missing X server or $DISPLAY` | No desktop session (SSH/server) | Run it under a virtual display: `xvfb-run -a uv run poe runner` (`sudo apt-get install -y xvfb`) |
| UI says the runner is unavailable | Runner not started, or started with another `GATP_RUNNER_SOCKET` | Start `uv run poe runner` with the same `.env` as the API |
