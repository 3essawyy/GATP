# PLAN-011: Phase 1 submission pack (for T-011)

- **Task:** [T-011](../tasks/T-011-phase1-submission.md)
- **Status:** Executed
- **Date:** 2026-11-04

## Approach
Keep content in one place (CLAUDE.md): the HLD is updated to match the implementation and becomes the design doc. A short cover page (`docs/submission/phase1/README.md`) maps every REQ-P1-S item and rubric line to evidence, and `poe pdf-phase1` renders cover + HLD (with Mermaid diagrams) to a PDF. Evidence comes from the real-system scripts.

## Steps
1. HLD v0.2 (transport, flow with G0 + insight, §12 implementation status).
2. `scripts/build_pdf.py` (pandoc + Mermaid + Chromium) + `poe pdf` / `poe pdf-phase1`.
3. Cover page, SG-004 demo script, SG-005 index, SG-006 limitations, DEFENSE.md.
4. Walkthrough: usage-evidence export, reuse check, `--record` (ffmpeg x11grab of the whole display, headed).
5. TC-102 Run 2 (full SG-001 + real inspection in a clean container); secret scan; `.env.example` completeness test.
6. TC statuses, task doc, session log; tag `phase1-rc` after merge.

## Tests to add
| Test | Proves |
|---|---|
| `test_env_example.py` | Every setting documented; no secret value in the example |
| Walkthrough additions | Projects page badges (SG-001 "Verify"); cached second call shown as "reused" |

## Risks / open questions
| Item | Mitigation / decision |
|---|---|
| Playwright's video recorder unavailable in the sandbox (ffmpeg build mismatch) | Record the X display with the system ffmpeg instead; this also captures the runner's own window |
| Big Mermaid diagrams split across pages | SVGs capped to one page height |

## Deviations (filled after execution)
- The real Gemini run is not part of this release (no key in the build environment); this is recorded in the cover page, SG-006 and TC-111.
