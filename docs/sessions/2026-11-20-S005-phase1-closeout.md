# Session S005 — 2026-11-20 — Phase 1 close-out (real-model evidence, docs audit, tag)

- **Tasks touched:** T-005, T-010, T-011 (plus a T-014 bug fix)
- **Branches / PRs:** #18 default Gemini model, #19 bwrap symlink fix, #20 real-model evidence + harness fix, #21 diagram overlap fix, #22 SG-004 demo-script fixes, #23 docs audit fixes, #24 Classroom assets + this log. Tag `phase1` on `ef03bd6` (the #23 merge).

## Done
- **Real Gemini run (B1, B2).** `gemini-2.5-flash` returned HTTP 404 (retired), so the default is now `gemini-3.5-flash` (provider version `gemini-3.6-flash`) and `GATP_LLM_TIMEOUT_S` is 120 s. A real insight call: 2,433 in / 1,437 out tokens (provider-reported), 69.3 s, then the identical request `reused`. TC-111 is Pass. Evidence: `docs/submission/phase1/usage-evidence.json`, the UI usage card screenshot, SG-003 §6.
- **WSL setup.** Ubuntu 24.04 on WSL2 now has bubblewrap, Xvfb, ffmpeg, uv, Node 22 and Playwright Chromium (system packages were installed with `wsl -u root`; `sudo` needs a password). The repo is cloned at `~/GATP` in WSL with a copy of `.env`.
- **Two bugs found and fixed while producing the evidence.**
  - bwrap could not hide `~/.aws` when it is a symlink (WSL links it to `/mnt/c/...`), so every approved run failed. Fix: resolve secret dirs before mounting (#19, with a regression test).
  - The e2e harness forced `GATP_LLM_PRIMARY=fake`, so the documented real-model walkthrough could never run. It now reads the environment (default still `fake`), and `ui-walkthrough` has `--phase1-only` (#20).
- **Correction.** An early walkthrough run was reported as "real Gemini" but used the fake provider because of the harness bug above. Only `llm-check` and the final `--phase1-only` run used real Gemini.
- **Docs audit.** Six read-only agents (one per folder group); every finding was re-checked against the repo. 22 verified items fixed in #23 (status tables, module index, runner/API LLDs, entry READMEs). Historical records (ADR bodies, sessions, "Explain it"/"Verification") were left alone.
- **Diagram.** `docs/architecture/GATP-system-design.drawio` (components, data flow, gates, validation, resources, inspection → maintenance path) with edge overlaps fixed; PNG export in the Classroom assets.
- **SG-004** now documents `--record`, the ~70 s model wait and the 2026-11-20 verification.
- **Tag `phase1`** (annotated, pushed) on `ef03bd6`. `phase1-rc` never existed, despite what T-011's original text claimed.

## Decisions (with ADR links)
- Default Gemini model is `gemini-3.5-flash`. Recorded as an update note in [ADR-016](../decisions/ADR-016-llm-gateway-design.md); no new ADR.
- The tag marks the whole repository. What goes to Classroom is a curated pack, not the repo (see `docs/submission/phase1/ClassroomAssets/`). The demo video is a Drive link and is not committed.
- Containerizing the runner was considered and not pursued: the brief allows "a restricted runner process or container", and the process-plus-bubblewrap design already meets it.
- "19 Phase 1 ADRs" (ADR-001 to 019) is kept as a Phase 1 snapshot; ADR-020 to 024 are early Phase 2.

## Open items / blockers
- **Narrated demo video (the only Phase 1 deliverable still open).** Check SG-004 step 9 by hand first (a second scope save gives version 2 and resets the approval); the automated walkthrough does not cover it. Only the offline-provider backup `.webm` is committed.
- **Ollama fallback unverified from WSL.** The model `qwen2.5-coder:3b` is pulled on the Windows host and the server runs there, but WSL was not confirmed to reach `127.0.0.1:11434`. A Gemini 503 or timeout therefore fails the call.
- **Full walkthrough with the real model fails at a Phase 2 step.** The T-015 weakening-guard step expected deterministic fake-model output (`clarification-weakening` never appeared). Not investigated further. T-012's real-model run is therefore still to do; its status line says so.
- **Gemini latency.** About 30 to 70 s per call on the free tier, with occasional 503s on some models (`gemini-3.8-flash`, `gemini-flash-latest` timed out). Narrate through the wait in the demo.
- **Owners** in `docs/modules/README.md` are still `TBD`. The brief does not require them; they matter only for the code discussion.
- **Classroom submission contents** are still to be decided by the team (design PNG and usage evidence are staged; the PDF and sample JSON are optional).

## Next steps (in order)
1. Record the narrated demo (SG-004, steps 1 to 13); upload to Drive.
2. Decide what goes on Classroom: design PNG, usage evidence, source zip, repo link at tag `phase1`, video link (and optionally the design PDF and sample inspection JSON).
3. Phase 2: T-017 repairs, T-018 history UI, T-019 usage panel, T-020 hardening; re-run the full walkthrough against the real model and fix the T-015 step.
4. Try the Ollama fallback from WSL (set `GATP_OLLAMA_HOST` if needed) and record it in SG-003 §6.

## Notes for next session
- The tag was set before the video. The video and these Classroom files are not part of the tag.
- To rebuild the source zip: `git archive --format=zip --prefix=GATP/ -o GATP-phase1-source.zip phase1`.
- To run the stack in WSL: `uv run poe fixtures v1`, `runner`, `api`, `web` from `~/GATP` (UI at http://localhost:5173).
- Real-model evidence command: `GATP_LLM_PRIMARY=gemini xvfb-run -a -s "-screen 0 1440x900x24" uv run poe ui-walkthrough --headed --phase1-only --out DIR`.
