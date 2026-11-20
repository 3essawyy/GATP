# Phase 1 submission: blockers and what is already done

Snapshot of 2026-11-20 (updated after B1). Sources: [T-011](../../tasks/T-011-phase1-submission.md), [tasks README](../../tasks/README.md), [HLD §12](../../architecture/HLD.md), [REQ-P1](../../RefrenceDocs/REQ-requirements.md). This file is a status summary; the linked docs stay the source of truth.

## Blockers (what is left before submitting)

| # | Blocker | Rubric / item | Needs | Done when |
|---|---|---|---|---|
| B1 | ~~Real-model run.~~ **Done 2026-11-20:** `uv run poe llm-check` passes with `gemini-3.5-flash` (provider version `gemini-3.6-flash`, 136 in / 10 out tokens, ~30 to 40 s latency). Default model changed from the retired `gemini-2.5-flash`. | REQ-P1-4 (1 pt) | none | Done: see [SG-003](../../SystemGuides/SG-003-models.md) §6 |
| B2 | **Re-export evidence with the real model.** `GATP_LLM_PRIMARY=gemini uv run poe ui-walkthrough --out walkthrough`, fill [SG-003](../../SystemGuides/SG-003-models.md) §6, refresh `usage-evidence.json`. | REQ-P1-4, REQ-P1-S | B1 | Evidence shows real model, version, tokens, latency; TC-111 moves from partial to Pass |
| B3 | **Narrated live demo.** Record it following [SG-004](../../SystemGuides/SG-004-demo-script.md). The committed `.webm` is an automated backup, and its frames show the runner's own Chromium window. | REQ-P1-D | B2 (so the demo uses the real model) | Video exists and matches the demo sequence |
| B4 | **Component owners.** Replace `TBD` in [modules/README](../../modules/README.md) with names. | Code defense | Team decision | All 9 modules have an owner |
| B5 | **Defense rehearsal.** Each owner rehearses their component using [DEFENSE.md](DEFENSE.md). | Code defense | B4 | Checklist in DEFENSE.md ticked |
| B6 | **Final tag.** Tag `phase1` on the submitted commit. | REQ-P1-S | B1 to B5 | Tag exists on the submitted commit |

Critical path: B2 → B3 (B1 is done). B4 → B5 can run in parallel.

### Things to verify (not confirmed by me)
- T-011 says `phase1-rc` was tagged, but `git tag -l "phase1*"` in this clone returns nothing. The tag may be unpushed, fetched elsewhere, or missing. Check before tagging `phase1`.
- The exact Week 9 deadline date is not in the repo (the tasks README only gives relative weeks). Confirm it with the instructor or TA.
- The offline `fake` provider evidence may not count as a "meaningful model call" for the 1-pt feasibility item. B1 and B2 exist for that reason.

## Already done

| Rubric item | Pts | Status | Evidence |
|---|---|---|---|
| Architecture and system design | 4 | Done | [HLD](../../architecture/HLD.md), [system diagram](../../architecture/GATP-system-design.drawio), [design PDF](GATP-phase1-design.pdf), [ADRs](../../decisions/README.md), TC-101 Pass |
| Working page inspection | 3 | Done | Visible Chromium in a separate runner; elements, attributes, ranked and live-verified locators; TC-106 to TC-108 Pass; [samples](../../samples/) |
| Basic human interaction | 2 | Done | Goal, element selection, region include/exclude, G0 scope approval; TC-109, TC-110 Pass |
| Feasibility evidence | 1 | Partial | Grounded model call implemented and logged (TC-111 automated part passes); real-model run pending (B1, B2) |
| Demo | none | Backup only | [phase1-walkthrough.webm](phase1-walkthrough.webm); narrated demo pending (B3) |

### Submission package contents
- Design doc: [GATP-phase1-design.pdf](GATP-phase1-design.pdf) (cover page mapping each brief item to evidence, then the HLD).
- Runnable code and setup: [SG-001](../../SystemGuides/SG-001-setup-and-run.md), verified on a clean Ubuntu 24.04 container (TC-102).
- Model config without secrets: [SG-003](../../SystemGuides/SG-003-models.md), `.env.example` (completeness enforced by `test_env_example.py`).
- Sample structured inspection output: [samples](../../samples/).
- Usage and timing evidence: [usage-evidence.json](usage-evidence.json) (offline provider for now).
- Defense sheet: [DEFENSE.md](DEFENSE.md).

### Build tasks (all Done)
T-001 docs scaffold, T-002 repo skeleton and CI, T-003 fixture site, T-004 store, T-005 LLM gateway (live check pending key), T-006 runner, T-007 inspector, T-008 API core, T-009 inspection UI, T-010 grounded LLM call (real run pending key), T-011 submission pack.

### Fixes found during verification
SG-001 health badge missing on the start page (fixed, walkthrough asserts it); 4 undocumented settings in `.env.example` (fixed, test enforces it); PDF diagram split across three pages (fixed); secret scan clean.

### Beyond Phase 1 scope
Per [ADR-010](../../decisions/ADR-010-phase1-scope-frontload.md), Phase 2 work was front-loaded: T-012 to T-015 are Done, T-016 is in review, T-017 to T-021 are Todo, and T-022 (bonus) is blocked ([ADR-011](../../decisions/ADR-011-bonus-deferred.md)). None of it is graded in Phase 1.
