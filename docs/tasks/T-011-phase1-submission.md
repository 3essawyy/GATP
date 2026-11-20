# T-011: Phase 1 submission pack

- **Status:** Done. Tag `phase1` set 2026-11-20 on `ef03bd6`; the real Gemini run is done (2026-11-20); the narrated demo video is the only item left. (`phase1-rc` was never pushed: see S004.)
- **Phase:** P1
- **Target:** before W9
- **Modules:** docs (+ small UI fix, `.env.example`)
- **Requirements:** REQ-P1-S, REQ-P1-1, REQ-P1-D
- **Depends on:** T-010
- **Plan:** [PLAN-011](../implementationPlans/PLAN-011-phase1-submission.md)
- **Deliverables:** [docs/submission/phase1/](../submission/phase1/README.md): `GATP-phase1-design.pdf`, `phase1-walkthrough.webm`, `usage-evidence.json`, `DEFENSE.md`
- **TCs:** TC-101 Pass, TC-102 Pass, TC-103…TC-110 Pass, TC-111 Pass (real Gemini run 2026-11-20)
- **Session:** [S004](../sessions/2026-11-04-S004-full-build-run.md)

## Goal
Everything the Phase 1 submission requires, verified.

## Acceptance criteria
- [x] All Phase 1 TCs pass and are recorded in TCs/README, including TC-111 with a real Gemini run (2026-11-20)
- [x] No secrets in the repo (scan clean); `.env.example` complete (enforced by `test_env_example.py`)
- [x] Code-defense rehearsal material: [DEFENSE.md](../submission/phase1/DEFENSE.md). The rehearsal itself is a team activity (checklist in that file).

## Verification (real system)
- **TC-102 Run 2:** a clean Ubuntu container following SG-001 literally, through a real headed inspection.
  - **Found:** the SG-001 health badge was missing on the start page. **Fixed**, and the walkthrough now asserts it.
- **Secret scan:** clean.
- **`.env.example` completeness check:** found 4 undocumented settings. **Fixed**, and a test now enforces it.
- **Screen recording of the walkthrough (headed, Xvfb):** the frames show the runner's own Chromium window opening over the GATP UI during inspection.
- **PDF:** first build had a diagram split over three pages. **Fixed** (diagrams capped to one page).

## Remaining before the real submission (team)
1. ~~Add a Gemini key, run `llm-check`, re-export usage evidence with the real model.~~ **Done 2026-11-20.** Command: `GATP_LLM_PRIMARY=gemini uv run poe ui-walkthrough --phase1-only --out walkthrough` (the harness used to force `fake`; it now honors `GATP_LLM_PRIMARY`, default `fake`). Evidence in `docs/submission/phase1/`.
2. Record the narrated live demo following [SG-004](../SystemGuides/SG-004-demo-script.md).
3. Fill in the component owners' names and rehearse [DEFENSE.md](../submission/phase1/DEFENSE.md).
4. Tag `phase1` on the submitted commit.

## Explain it (code-defense prep)
**What.** The submission is the repository plus `docs/submission/phase1/`:
- **Design PDF:** a cover page mapping each brief item to evidence, followed by the HLD.
- **Recording:** a screen recording of the full Phase 1 flow.
- **Usage evidence:** the model-call log with timings.
- **Defense sheet.**

**Why.** REQ-P1-S lists exactly these items. Generating them from the running system, rather than writing them by hand, means the evidence can't drift from the code.

**How.**
- `uv run poe pdf-phase1` renders Markdown with pandoc, draws Mermaid diagrams in Chromium and prints to PDF.
- `uv run poe ui-walkthrough --record` drives the real UI in a headed browser on an X display while ffmpeg records the screen, then exports the usage log.

**Likely questions:**
- *Is the demo video staged?* It's the automated walkthrough against the real processes. The runner's separate browser window is visible in it, and the same script runs as a test.
- *Where is the model evidence?* `usage-evidence.json` and the UI usage card. It comes from a real Gemini run on 2026-11-20 (`gemini-3.5-flash`); the narrated demo video is the remaining step.
