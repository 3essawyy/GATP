# Acceptance Test Cases (for GATP itself)

These prove GATP meets the brief. They are **not** the test cases GATP generates for websites. Definitions: [phase1.md](phase1.md), [phase2.md](phase2.md). Template for long TCs: [_TEMPLATE.md](_TEMPLATE.md). Run logs: [TC-102-runs.md](TC-102-runs.md).

Update **Status** with date + commit whenever a TC is run.

## Traceability matrix

| Rubric / requirement | Pts | TCs | Tasks |
|---|---|---|---|
| REQ-P1-1 Architecture & design | 4 | TC-101 | T-001, T-011 |
| REQ-P1-2 Page inspection | 3 | TC-106, TC-107, TC-108 | T-006, T-007, T-009 |
| REQ-P1-3 Human interaction | 2 | TC-110 | T-008, T-009 |
| REQ-P1-4 Feasibility evidence | 1 | TC-111 | T-005, T-010 |
| REQ-P2-1 Collaborative test design | 4 | TC-201, TC-202 | T-012 |
| REQ-P2-2 Test implementation | 4 | TC-203, TC-204 | T-013 |
| REQ-P2-3 Execution & review | 4 | TC-205, TC-206, TC-207 | T-014, T-015 |
| REQ-P2-4 Assisted maintenance | 4 | TC-208, TC-209, TC-210 | T-016, T-017 |
| REQ-P2-5 Versioning & visibility | 2 | TC-211, TC-212 | T-018, T-019 |
| REQ-P2-6 Integration & defense | 2 | TC-102, TC-215 | T-002, T-021 |
| REQ-Q5–Q7 Isolation & injection | — | TC-106, TC-213 | T-006, T-020 |
| REQ-P2-D1/D2 Demo sequence | — | TC-215 | T-021 |

## Index

| ID | Title | Type | Status |
|---|---|---|---|
| TC-101 | Design document covers all required elements | Manual | **Pass** 2026-11-04 (T-011): [phase1 design PDF](../submission/phase1/GATP-phase1-design.pdf) = cover + HLD v0.2 (§2 components, §3 data flow, §4 gates, §5 validation, §6 later phases, §9 resources) |
| TC-102 | Clean setup from README on fresh machine | Manual | **Pass** 2026-11-04 (T-011): clean ubuntu:24.04, full SG-001 incl. fixture site + a real headed inspection ([run log](TC-102-runs.md)) |
| TC-103 | Fixture site v1/v2 serve and differ as documented | Automated | **Pass** 2026-11-04 (T-003): `test_fixture_server.py`, `test_fixture_site.py`, `test_fixture_diff.py` |
| TC-104 | Store versioning immutable; restore creates new version | Automated | **Pass** 2026-11-04 (T-004): `test_store_*.py` |
| TC-105 | LLM gateway logs usage; fallback; cache marked reused | Automated | **Pass** (automated, fake + mocked HTTP) 2026-11-04 (T-005); live Gemini/Ollama check pending |
| TC-106 | Runner blocks non-allowlisted origins and unknown jobs | Automated | **Pass** 2026-11-04 (T-006): `test_runner_*.py` |
| TC-107 | Inspection of URL opens visible browser and lists elements linked to source | Manual | **Pass** 2026-11-04 (T-009): `poe ui-walkthrough` (findings, screenshot highlight, source line) + headed runner under Xvfb (`poe smoke --headed`); repeat on the demo machine |
| TC-108 | Locator candidates ranked; non-unique flagged | Automated | **Pass** 2026-11-04 (T-007): `test_inspector.py` |
| TC-109 | Gates block without approval; edits invalidate approval | Automated | **Pass** 2026-11-04 (T-008): `test_api_gates.py` |
| TC-110 | User sets goal, selects elements, refines scope | Manual | **Pass** 2026-11-04 (T-009/T-010): walkthrough + `test_api_insight.py` (excluded elements absent from the request) |
| TC-111 | Grounded model call with model/version/tokens/latency recorded | Manual | Partial: automated + UI with the fake provider Pass (T-010); **real Gemini run pending key** |
| TC-201 | Proposed cases cite observed elements; assumptions flagged | Automated + Manual | **Pass** 2026-11-04 (T-012): `test_api_plan.py` + walkthrough (offline provider); real-model run pending key |
| TC-202 | Plan edit, clarification, approval (G1) | Manual | **Pass** 2026-11-04 (T-012): walkthrough screenshots 09–11 + `test_api_plan.py` |
| TC-203 | Generated POM code passes syntax + locator validation | Automated | **Pass** 2026-11-04 (T-013): `test_codegen.py` (incl. a real run of the generated test on v1), smoke, walkthrough |
| TC-204 | Invented locator rejected; code reviewable | Automated + Manual | **Pass** 2026-11-04 (T-013): `test_codegen.py` + walkthrough screenshot 13 |
| TC-205 | Execution requires G3; visible browser; results + screenshots | Manual | **Pass** 2026-11-04 (T-014): `test_runs.py`, smoke (real socket, bwrap), walkthrough screenshots 14–15; visible-browser run to repeat on the demo machine |
| TC-206 | Real failure stays visible with details | Automated | **Pass** 2026-11-04 (T-014): `test_runs.py::test_real_failure_stays_visible` + walkthrough screenshot 15 |
| TC-207 | Feedback → revise → approved rerun; no silent assertion weakening | Manual | **Pass** 2026-11-04 (T-015): `test_feedback.py` (4 tests) + walkthrough screens 16–18 |
| TC-208 | Rescan flags v1→v2 changes | Automated | Not run |
| TC-209 | Clear locator change → evidence-backed repair → approve → rerun passes | Manual | Not run |
| TC-210 | Ambiguous change → clarification requested, not auto-resolved | Manual | Not run |
| TC-211 | Version diff and restore | Automated + Manual | Not run |
| TC-212 | Per-call usage + averages; model vs test time separated | Manual | Not run |
| TC-213 | Prompt-injection page treated as data; sandbox confinement | Automated | Not run |
| TC-214 | Bonus feature (TBD) | — | Not defined |
| TC-215 | Full Phase 2 demo sequence end to end | Manual | Not run |
