# SG-004: Demo script

- **Audience:** presenter (team), examiner
- **Last verified:** 2026-11-20 by `GATP_LLM_PRIMARY=gemini uv run poe ui-walkthrough --phase1-only` (steps 1 to 8 and 10 to 13, automated, real Gemini, WSL Ubuntu under Xvfb), and by hand in the recorded narrated demo (all 13 steps, headed WSLg window, `gemini-3.5-flash-lite`; S006).
- **Phase 2 sequence:** added in T-021

Setup first: [SG-001](SG-001-setup-and-run.md). For a real model, put your Gemini key in `.env` and run `uv run poe llm-check` **before** the demo ([SG-003](SG-003-models.md)).

Values to type during the recording are collected in [demo-recording-inputs.txt](../submission/phase1/demo-recording-inputs.txt).

## One-command start (Windows → WSL)
From PowerShell in the repo root:
```powershell
.\scripts\demo-up.ps1            # real Gemini model
.\scripts\demo-up.ps1 -Fake      # offline fake provider (the usage card labels it)
.\scripts\demo-up.ps1 -Site v2   # serve the modified site (Phase 2 rescan)
```
It opens a WSL window that supervises the stack and stays open (Ctrl+C or closing it stops everything). On each start it stops the previous supervisor and anything on ports 8000, 8090 and 5173, removes a stale runner socket, starts fixtures, runner, API and web, waits for real health checks (including the UI reaching the runner through the proxy) and then opens http://localhost:5173. Logs go to `data/logs/` in the WSL clone. It loads nvm and drops `/mnt/*` from `PATH`, because a non-interactive WSL shell otherwise picks the *Windows* `npm`. To start over with an empty database, stop the stack, move `data/gatp.sqlite*` aside and start again (the API creates a fresh one; evidence rows are immutable by design, so they cannot be deleted row by row). The four manual terminals below do the same thing.

## Phase 1 demo (≈ 6 minutes, plus the model wait)

**Model wait:** it depends on the model. With `gemini-3.5-flash` step 11 takes about 70 s (measured 69 s on 2026-11-20). With the default `gemini-3.5-flash-lite` it took 4.6 s in the recorded demo (2,419 in / 557 out tokens), then `reused` in 0 ms. Narrate the grounded-call design while it runs (what is sent, what is checked), or run step 11 once before the demo with the same scope and let step 13 show the reuse. The gateway's HTTP timeout is 120 s (`GATP_LLM_TIMEOUT_S`).

**Before you start**, open four terminals at the repo root:
```bash
uv run poe fixtures v1
```
```bash
uv run poe runner
```
```bash
uv run poe api
```
```bash
uv run poe web
```
Then open http://localhost:5173. Both header badges should be green: "Runner ready" and "API ok".

| # | Do | Say (what it proves) |
|---|---|---|
| 1 | Projects → name "BookShelf demo", start URL `http://127.0.0.1:8090/index.html` → **Create** | The start URL's origin becomes the only site the browser may load (allowlist). |
| 2 | Type your name in the header box | It is recorded with every approval. |
| 3 | **Inspect /index.html** | A real Chromium window opens in the **separate runner process** and closes after inspection. GATP never runs the browser inside the API. |
| 4 | Point at the findings: 3 elements with roles/names; click **e3 "Sign in"** | The box lights up on the screenshot. Every candidate locator was **executed on the live page**: "usable" means it matches exactly this element. |
| 5 | Click **line 23** | Each finding links to its line in the HTML the site served. |
| 6 | Add page `…/add.html`, open **Before inspecting**, add 4 steps: goto `http://127.0.0.1:8090/index.html` (**full URL**, a relative one is rejected); fill label `Username` = `tester`; fill label `Password` = `secret123`; click test_id `login-submit` (choose `click`, then `test_id` in the second dropdown) → **Save steps** → **Inspect /add.html** | Protected pages are reached by tester-approved steps (data, not code). |
| 7 | Point at **e4 "Year published"**, flagged *no visible label* | GATP flags weak elements instead of pretending they are fine. |
| 8 | Step **2 · Scope & goal**: goal "Adding a book validates title, author, year and genre"; untick the sign-in elements and the two links → **Save scope** | Version 1 of the scope; the step shows *needs approval*. |
| 9 | Untick one more element → **Save scope** again | Version 2: the edit created a new version, and the approval state starts over. |
| 10 | **Approve scope (G0)** | The human gate. Only now may the inspection be used for design. |
| 11 | **Summarise & suggest next actions** | One grounded model call: only the in-scope elements are sent, and every cited element id is checked. Actions are marked *observed* vs *assumption*, plus questions for the tester. |
| 12 | Show the usage card and **Exactly what was sent** | Model, version, tokens (reported vs estimated), **model time vs browser time**, fresh vs reused, the exact request. |
| 13 | Click **Summarise** again | "reused (cached, no new model call)" (REQ-Q10). |

### If something goes wrong
| Symptom | Recovery |
|---|---|
| "Runner offline" badge | Start `uv run poe runner` (same `.env` as the API) |
| Model error (rate limit / no key) | GATP falls back to Ollama if configured; otherwise set `GATP_LLM_PRIMARY=fake` and explain that the usage card labels it |
| Browser window doesn't show (WSL) | `wsl --update`, or show the screenshots from `docs/samples/phase1-walkthrough/` |

### Backup recording
Records the same flow (no narration) to a `.webm` file. It needs a display, so run it under Xvfb:
```bash
xvfb-run -a -s "-screen 0 1440x900x24" uv run poe ui-walkthrough --record demo.webm
```
Add `GATP_LLM_PRIMARY=gemini` for a real-model recording (default is the offline `fake` provider), and `--phase1-only` to stop after step 13. A copy of the existing backup (offline provider) is in `docs/submission/phase1/`.
