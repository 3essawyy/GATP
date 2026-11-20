# Session S006 — 2026-11-20 — Narrated demo, 422 fix, one-command launcher, code-only hand-in

- **Tasks touched:** T-008 (bug fix), T-011 (submission pack, demo)
- **Branches / PRs:** `fix/T-008-setup-goto-422-demo-launcher`, two commits (T-008 fix; T-011 launcher, pack, docs). **Not pushed, no PR yet** (needs the team's go-ahead).

## Done
- **Walked the Phase 1 demo (SG-004 steps 1 to 13) by hand and recorded it.** The presenter ran every step on the real stack in WSL (headed Chromium through WSLg) with `gemini-3.5-flash-lite`. The recording is `ClassroomAssets/Phase1-Demo.mp4` (151 MB, not committed). The model call recorded in `llm_calls`: fresh, 4,639 ms, 2,419 in / 557 out tokens; the second Summarise was `reused`, 0 ms, same request hash (`edf954ef39`), so the cache behaves as step 13 claims. I did not see the screen; step outcomes beyond that database row are the presenter's report.
- **Bug found and fixed (T-008).** `PUT /pages/{id}/setup` returned a 500 when a `goto` step had a relative URL (`index.html`): the origin helper raised a plain `ValueError` before validation. It is now a 422 with a message naming the expected form. SG-004 step 6 had told the presenter to type the relative form, so that is corrected too. Regression test `test_setup_goto_not_a_full_http_url_is_422` (4 inputs).
- **One-command launcher.** `scripts/demo-up.ps1` (Windows) + `scripts/demo-up.sh` (WSL supervisor). It stops anything on 8000/8090/5173 and any old supervisor, removes the stale runner socket, starts fixtures, runner, API and web, waits for real health checks (UI → proxy → runner), then opens http://localhost:5173. Tested with repeated takeovers over a live stack. Documented in SG-004.
- **Database resets (3×).** The presenter re-ran the demo, so the project data was removed each time. Evidence tables are immutable by design (triggers raise `rows are immutable`), so rows cannot be deleted; instead the stack was stopped, `data/gatp.sqlite*` moved aside, and the API created a fresh file on start (it migrates on startup). The two project-less feasibility `llm_calls` rows were copied back each time. Backups remain in the WSL clone's `data/`.
- **Code-only hand-in zip.** The earlier source zip contained `docs/`, `scripts/`, `CLAUDE.md` and task/ADR identifiers in comments. A clean `GATP-source.zip` was built instead: no `docs/`, `scripts/`, `CLAUDE.md`, `.github/`, no `.md` except one self-contained `README.md` (setup, model configuration, run, try-it), and no `ADR-`/`T-NNN`/`TC-NNN`/`REQ-`/`HLD`/`docs/` text in the 171 files. Three subagents stripped the identifiers in parallel (one per code area, no overlapping files); I re-grepped, regenerated `frontend/openapi.json` and `schema.d.ts` (four field descriptions feed the schema), and verified on the cleaned copy: **142 tests pass, mypy strict clean (114 files), ruff clean, eslint, prettier and production build clean**.
- **Hand-in folder** `ClassroomAssets/`: `GATP-source.zip`, `GATP-system-design.png`, `usage-evidence.json`, `inspectionLogs/` (two sample inspection outputs), `Phase1-Demo.mp4`. The design PDF stays in the repo but is not part of the hand-in. A copy-paste sheet for the recording is `docs/submission/phase1/demo-recording-inputs.txt`.
- Docs updated: SG-001 (three troubleshooting rows), SG-004 (launcher, inputs file, model wait by model, verified line), SG-005 and SG-README index rows, `modules/api`, T-008 follow-up note, T-011, tasks README, BLOCKERS-AND-STATUS (B3 done, hand-in contents), sessions README.

## Problems found along the way
- **WSL picks the Windows `npm`.** A non-interactive shell (`wsl -e bash -lc`) does not load nvm, so `poe web` ran `CMD.EXE` on a UNC path and failed. The launcher loads nvm, drops `/mnt/*` from `PATH`, and refuses to start if `node` resolves outside Linux.
- **Second launch killed the first launch's replacement.** The old supervisor saw its services die and ran its own shutdown. Fixed with a pidfile lock that stops and waits for the previous supervisor.
- **CRLF line endings.** The package built from the Windows checkout had CRLF in 68 files, which made prettier fail on untouched files. Normalized to LF in the package. (The Windows working tree still has CRLF; the WSL clone does not.)
- **Pasting four start commands into one terminal** only started the first (each task stays in the foreground), and left a stale runner and API behind. Now covered by the launcher and an SG-001 row.

## Decisions (with ADR links)
- No new ADR. The launcher is a convenience over the existing four tasks (the tasks defined under [ADR-012](../architectureDecisionRecords/ADR-012-backend-and-dev-tooling.md) are unchanged).
- The hand-in is **code only**, and identifiers were stripped **only in the hand-in copy**. The repository keeps its ADR/task references: they are part of the project record and its docs.
- The narrated video is not committed (`.gitignore` now excludes `docs/submission/**/*.mp4`); it is shared as a Drive link.
- Database reset policy: start from a fresh file, never disable the immutability triggers.

## Open items / blockers
- **Hand-in note must explain the two model runs.** `usage-evidence.json` is the `gemini-3.5-flash` run (2,433 in / 1,437 out, 69.3 s). The recorded demo used `gemini-3.5-flash-lite` (2,419 in / 557 out, 4.6 s, then reused). Both are real calls. A re-export of the evidence from the current database would make them match; not done.
- **Source zip is newer than tag `phase1`** (it includes the 422 fix and drops docs). Do not move the pushed tag; if a tag is wanted for the hand-in, add a new one after the PR merges.
- **Branch not pushed, no PR.** The workflow in `CLAUDE.md` squash-merges PRs; that needs the team's go-ahead.
- Carried over from S005: full walkthrough with the real model still fails at the T-015 weakening-guard step (expects deterministic fake output); Ollama fallback unverified from WSL; module owners still `TBD`.
- The zip's identifiers were stripped by script and spot-checked, not diff-reviewed line by line; the full check suite passed on the result.

## Next steps (in order)
1. Upload `Phase1-Demo.mp4` to Drive (anyone with the link can view) and submit the `ClassroomAssets` contents with the model-run note above.
2. Push the branch, open the PR, squash-merge to `main` (with the team's OK).
3. Phase 2: T-017 repairs, T-018 history UI, T-019 usage panel, T-020 hardening; re-run the full real-model walkthrough and fix the T-015 step.
4. Try the Ollama fallback from WSL and record it in SG-003 §6; fill the module owners and rehearse DEFENSE.md.

## Notes for next session
- Start the stack with `.\scripts\demo-up.ps1` from PowerShell (`-Fake` for offline, `-Site v2` for the modified site). It stays in a WSL window; Ctrl+C stops everything.
- Rebuilding the hand-in zip: stage the tracked files minus `docs/`, `scripts/`, `CLAUDE.md`, `.github/`; replace `README.md` with the self-contained one; drop the `smoke`, `ui-walkthrough`, `pdf` and `pdf-phase1` poe tasks; strip identifiers; normalize to LF; regenerate the OpenAPI client; run `uv run poe check` with Linux Node on `PATH`; zip without `.venv`, `node_modules`, `__pycache__`, `data`, `.env`.
- The WSL clone (`~/GATP`) has the three code/doc files copied from the Windows repo by hand; pull the merged branch there rather than copying again.
