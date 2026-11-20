# T-008: API core — projects/inspections, workflow state, gates, clarifications, TS client

- **Status:** Done
- **Phase:** P1
- **Target:** W+2
- **Modules:** api, store
- **Requirements:** REQ-G2, REQ-G5, REQ-P1-3
- **Depends on:** T-004, T-007
- **Plan:** [PLAN-008](../implementationPlans/PLAN-008-api-core.md)
- **ADRs:** [ADR-019](../architectureDecisionRecords/ADR-019-gates-on-versions-computed-workflow.md)
- **TCs:** TC-109 (Pass), TC-110 (stored part)
- **Session:** [S004](../sessions/2026-11-04-S004-full-build-run.md)
- **Branch / PR:** `claude/serene-johnson-xtbl4s` → squash-merged to `main`

## Goal
The orchestrator backbone: endpoints, state machine, approval and clarification objects (see [api LLD](../modules/api/README.md)).

## Scope
- In: projects/pages/inspections endpoints; scope + selection + goal endpoints; generic `Approval` (bound to exact artifact versions) and `Clarification` models; state machine with guards; SSE progress; regenerate TS client.
- Out: feature-specific endpoints (added by their tasks).

## Acceptance criteria
- [x] Guard tests: gated transitions fail without approval; editing a version invalidates its approval; open clarification blocks its step (`test_api_gates.py`)
- [x] OpenAPI client regenerated and committed (CI stale check)

## Verification (real system)
`uv run poe smoke` starts the fixture site, the runner (socket) and the API as separate processes in a temp dir and walks the flow over HTTP. All 7 steps pass, both headless and headed (`xvfb-run -a uv run poe smoke --headed`):

| Step | Result |
|---|---|
| Create project (origin = allowlist) | PASS |
| Inspect sign-in page via runner socket | PASS: 3 elements, ~1.4 s browser time, screenshot served |
| Add page + sign-in setup steps | PASS |
| Inspect add-book page (signed in) | PASS: 7 elements, Year flagged `no_visible_label` |
| Save scope → `needs_approval` → G0 → `approved` | PASS |
| Edit scope → v2 unapproved, re-approving v1 → 409 | PASS |
| Off-origin page → 422 | PASS |

The smoke run is now part of CI.

### Follow-up (2026-11-20, S006)
`PUT /pages/{id}/setup` raised a plain `ValueError` (an HTTP 500) when a `goto` step had a relative URL such as `index.html`, because the origin check parsed it before validating it. It now returns **422** with `setup url 'index.html' must be a full http(s) URL, e.g. http://127.0.0.1:8090/index.html`. Regression test: `test_setup_goto_not_a_full_http_url_is_422` (`index.html`, `/index.html`, `ftp://…`, `javascript:…`). Found while recording the Phase 1 demo; SG-004 step 6 had also used the relative form.

## Explain it (code-defense prep)

**What.** The API is GATP's orchestrator. It covers:
- **Workspace:** projects (one origin each), pages with optional sign-in setup steps, the tester's goal and requirements.
- **Inspection:** done through the runner, producing immutable snapshots, screenshots and served HTML.
- **Scope (G0):** the tester's selection and exclusions plus the goal, stored as a versioned artifact.
- **Artifacts:** generic versioning with edit, diff and gated restore.
- **Human control:** approvals, clarifications and a computed workflow status.
- **Live updates:** an SSE event stream.

**Why:** the brief makes the human the decision-maker (REQ-G5). Nothing consequential happens without an explicit approval of exactly what will be used. The design makes that rule hard to break by accident.

**How it works:**
- **Startup:** `create_app()` builds `Services` in its lifespan, which migrates the DB (a fresh one is created on first run) and connects the runner client. Domain errors map to HTTP in one table: 404 not found, 409 gate blocked, 422 invalid, 503 runner/model unavailable, 502 inspection/model output failed.
- **Inspection:** `POST /pages/{id}/inspections` builds a typed `InspectJob`. The project origin is the only allowlisted origin, and the page's setup steps run first. It's sent over the runner socket, the result is converted to a snapshot and stored, and the response includes browser time (kept separate from model time).
- **Scope:** `PUT /projects/{id}/scope` validates that each snapshot belongs to the project and that every element key exists, then stores the scope as a new version of the `scope` artifact (only if the content changed).
- **Approval:** `POST /projects/{id}/approvals` must name an exact version id. It's refused if the gate doesn't fit the artifact kind, the version isn't the latest, or the step has an open clarification.
- **Edits close the gate automatically:** versions are immutable, and any edit creates a new unapproved version. No "revoke" code exists to forget.
- **Workflow status:** `GET /projects/{id}/workflow` is computed on each call from the stored facts, so it can never be out of date.

**Likely examiner questions:**
- *What stops code from running tests without approval?* Gated actions call `require_approval(gate, version)` on the exact version they're about to use (T-013/T-014 do this for code and runs). The approval row names that version's id, so an approval for v1 doesn't cover v2.
- *How does editing invalidate an approval?* An edit creates version N+1. Approvals point to version N's id, so N+1 is unapproved by construction, and the step shows `needs_approval` again.
- *What blocks a step besides approvals?* Open clarifications. While one is open for a step, that step's approvals (and actions such as inspection) return 409.
- *How do you know it works outside the unit tests?* `poe smoke` runs the real processes (runner on its socket, API over HTTP, real browser) and walks the flow. It also runs in CI.
- *Why is there no login?* GATP is a single-user local tool bound to 127.0.0.1 (agreed scope). Approvals still record the approver's name.
