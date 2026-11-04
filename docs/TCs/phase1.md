# Phase 1 acceptance TCs

Status tracked in [README.md](README.md).

### TC-101 — Design document covers all required elements
- **Proves:** REQ-P1-1, REQ-P1-S
- **Steps:** Review the Phase 1 design doc.
- **Expected:** Component diagram; data flow covering web UI, model integration, inspection/state storage, isolated runner; approval gates; validation; resource assumptions; path inspection → generation → execution → maintenance; how later phases use inspection results.

### TC-102 — Clean setup from docs
- **Proves:** REQ-P1-S, REQ-P2-6
- **Steps:** On a fresh clone/machine follow SG-001 only.
- **Expected:** api, runner, frontend and fixture site start; no undocumented step; no secrets needed beyond `.env.example` keys.

### TC-103 — Fixture site v1/v2
- **Proves:** REQ-G9 (simulated)
- **Steps:** Serve v1, then v2.
- **Expected:** Pages load; differences match `fixtures/README.md` exactly.

### TC-104 — Store versioning
- **Proves:** REQ-G8, REQ-P2-5
- **Steps:** Automated tests in store.
- **Expected:** Versions immutable; restore creates N+1 (`author=restore`); diff output correct; snapshot round-trip identical.

### TC-105 — LLM gateway
- **Proves:** REQ-G6, REQ-Q9, REQ-Q10
- **Steps:** Automated tests with fake provider.
- **Expected:** All log fields set; `tokens_source` correct; cached call marked `reused`; fallback used on primary failure; invalid JSON rejected.

### TC-106 — Runner restrictions
- **Proves:** REQ-Q5, REQ-Q6
- **Steps:** Submit unknown job type; inspect a non-allowlisted URL; load fixture page that requests an external origin.
- **Expected:** Rejected / rejected / external request aborted and logged.

### TC-107 — Inspection with visible browser
- **Proves:** REQ-P1-2
- **Steps:** Enter fixture v1 login URL in UI; start inspection.
- **Expected:** Visible browser opens; findings list interactive elements with labels/attributes/candidate locators; each finding linked to source page URL and screenshot highlight.

### TC-108 — Locator ranking and uniqueness
- **Proves:** REQ-P1-2, REQ-Q1
- **Steps:** Automated inspection on fixture page with duplicate-label elements.
- **Expected:** Candidates in priority order with counts; count≠1 marked unusable; element with no unique locator flagged.

### TC-109 — Gates and approvals
- **Proves:** REQ-G5
- **Steps:** Automated API tests.
- **Expected:** Gated actions fail without approval; editing an approved version invalidates approval; open clarification blocks step.

### TC-110 — Human interaction
- **Proves:** REQ-P1-3
- **Steps:** Enter testing goal; select elements; exclude a region / refine scope.
- **Expected:** Selection and scope stored and reflected in findings and in what is sent to the model.

### TC-111 — Feasibility model call
- **Proves:** REQ-P1-4, REQ-P1-D
- **Steps:** With elements selected, request summary / next action.
- **Expected:** Response references only snapshot elements; UI and log show model, version, setup (provider), input/output tokens (source labelled), response time; model time separate from inspection time.
