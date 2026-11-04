# SG-004: Demo script

- **Audience:** presenter (team), examiner
- **Last verified:** 2026-11-04 by `uv run poe ui-walkthrough` (the same steps, automated) at the T-011 commit
- **Phase 2 sequence:** added in T-021

Setup first: [SG-001](SG-001-setup-and-run.md). For a real model, put your Gemini key in `.env` and run `uv run poe llm-check` **before** the demo ([SG-003](SG-003-models.md)).

## Phase 1 demo (≈ 6 minutes)

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
| 6 | Add page `…/add.html`, open **Before inspecting**, add 4 steps: goto `index.html`; fill label `Username` = `tester`; fill label `Password` = `secret123`; click test_id `login-submit` → **Save steps** → **Inspect /add.html** | Protected pages are reached by tester-approved steps (data, not code). |
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
`uv run poe ui-walkthrough --video --out walkthrough` records the same flow (no narration) to a `.webm` file. A copy is in `docs/submission/phase1/`.
