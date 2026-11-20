# GATP: Phase 1 submission

**Course:** Generative AI for Software Testing (Fall 2026) · **Phase 1:** Architecture and guided inspection · **Release:** tag `phase1-rc` (final tag `phase1` at submission) · **Repository:** https://github.com/3essawyy/GATP

GATP is a human-in-the-loop web testing assistant. It inspects a page in a visible, isolated browser and turns what it observes into grounded, reviewable inputs for testing. A human approves every consequential step. This document is the short design document requested by REQ-P1-S. The full high-level design follows it (component diagram, data flow, approval gates, validation, resource assumptions, and how later phases use inspection results).

## What to look at

| Brief item (REQ-P1-S) | Where |
|---|---|
| Short design doc: component diagram, data flow, approval gates, resource assumptions, path inspection → generation → execution → maintenance | This PDF: the HLD that follows (§2 components, §3 data flow, §4 gates, §5 validation, §6 later phases, §9 resources, §12 status) |
| Runnable code + dependencies + setup | Repository; [SG-001 Setup and run](../../SystemGuides/SG-001-setup-and-run.md) (verified on a clean Ubuntu 24.04 machine, [TC-102 log](../../TCs/TC-102-runs.md)) |
| Model configuration (no secrets) | [SG-003 Models](../../SystemGuides/SG-003-models.md), [`.env.example`](../../../.env.example) |
| Short demo | [SG-004 Demo script](../../SystemGuides/SG-004-demo-script.md); recorded walkthrough [phase1-walkthrough.webm](phase1-walkthrough.webm) (backup; the team records the narrated live demo) |
| Sample structured inspection output | [inspection-bookshelf-v1-add-book.json](../../samples/inspection-bookshelf-v1-add-book.json) (+ [login](../../samples/inspection-bookshelf-v1-login.json)) |
| Model usage / timing evidence | [usage-evidence.json](usage-evidence.json) (every logged call: provider, model, version, tokens and their source, model latency, browser time, fresh/reused, exact request) and the [UI usage card](../../samples/phase1-walkthrough/08-model-insight.png) |

## Phase 1 rubric map
| Rubric (pts) | How GATP meets it | Evidence |
|---|---|---|
| Architecture & design (4) | Separate runner process on a private Unix socket; thin UI over a FastAPI orchestrator; store with immutable versions; LLM gateway; 19 ADRs | HLD (this PDF), [ADRs](../../decisions/README.md), TC-101 |
| Page inspection (3) | Visible Chromium in the runner; interactive elements with role, name, label, attributes, nearby text; ranked locators **verified live** (unique **and** targets the element); flags for weak elements; screenshot highlight + source line | TC-106, TC-107, TC-108; [screenshots](../../samples/phase1-walkthrough/) |
| Human interaction (2) | Pages + sign-in setup steps, region include/exclude, element selection, testing goal, notes; scope approved at G0; edits create new versions and reopen the gate; clarifications block their step | TC-109, TC-110 |
| Feasibility evidence (1) | Grounded model call on the **approved** in-scope elements only; element ids validated; observations vs assumptions + questions; usage logged | TC-111 |

## Early Phase 2 work vs graded Phase 1 scope
Following [ADR-010](../../decisions/ADR-010-phase1-scope-frontload.md), some Phase 2 foundations are already built: versioned artifacts with diff and restore (API), gates G1–G5 in the data model, and the typed runner job protocol. They aren't part of the Phase 1 grade. The Phase 2 screens (test design, code generation, execution, maintenance, history, usage panel) are not in this submission.

## Known limitations
See [SG-006 Limitations](../../SystemGuides/SG-006-limitations.md). The model evidence ([usage-evidence.json](usage-evidence.json)) comes from a **real Gemini run** (`gemini-3.5-flash`, 2026-11-20): about 70 s per call on the free tier, so expect slow answers in the demo. The Ollama fallback has not been exercised from the walkthrough yet.

## Status and blockers
What is done and what is still open before submitting: [BLOCKERS-AND-STATUS.md](BLOCKERS-AND-STATUS.md).

## Team and code defense
Component owners: [modules/README](../../modules/README.md). Defense preparation: [DEFENSE.md](DEFENSE.md) (likely questions per component, from each task's *Explain it* section).
