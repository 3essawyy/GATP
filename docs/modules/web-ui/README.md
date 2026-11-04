# Module: web-ui

- **Owner:** TBD
- **Status:** In progress
- **Code:** `frontend/`
- **Tasks:** T-002 (scaffold), T-009, UI parts of T-010, T-012…T-019
- **ADRs:** ADR-002, ADR-013

## Responsibility
Presents every workflow step and collects human input and approvals. Contains **no business logic**: it never decides validity, never computes diffs or scores, never builds prompts. It renders what the API returns and sends user intent back.

## Interfaces
| Direction | Interface | Contract |
|---|---|---|
| Consumes | api (JSON) | Generated TS client from OpenAPI (`src/api/`) |
| Consumes | api (SSE) | Live run/inspection progress events |

## Screens (planned, full product)
| Screen | Purpose | REQ |
|---|---|---|
| Project / URL | Enter target URL, start inspection | REQ-P1-2 |
| Findings | Element table + screenshot, link to source page, include/exclude, select | REQ-P1-2, P1-3 |
| Goal & requirements | Testing goal, requirement notes, clarification answers | REQ-P1-3, Q2 |
| Test plan | Edit cases, see evidence + assumption flags, approve (G1) | REQ-P2-1 |
| Code review | Page objects + tests in read/edit editor, validation report, approve (G2) | REQ-P2-2 |
| Run | Approve execution (G3), live progress, results, screenshots, failure details, feedback | REQ-P2-3 |
| Maintenance | Rescan, change flags, repair proposals with evidence, clarifications, approve (G4) | REQ-P2-4 |
| History | Versions, diffs, restore (G5) | REQ-P2-5 |
| Usage panel | Per-call tokens/latency, fresh vs reused, averages; test time shown separately | REQ-P2-5, Q8–Q10 |

## Internal design
Libraries ([ADR-013](../../decisions/ADR-013-frontend-libraries.md)): Vite + React 19 + TS 5.9, Mantine (components), TanStack Query (server state), openapi-fetch + openapi-typescript (generated client), React Router. Code is edited in a plain monospace editor (Monaco dropped, [ADR-021](../../decisions/ADR-021-deterministic-codegen.md)).

Layering inside `frontend/src/`. Each layer only calls the one below it:

| Layer | Files | Rule |
|---|---|---|
| Components | `App.tsx`, `components/*` | Render data from hooks, send user intent; no `fetch`, no business rules |
| Query hooks | `api/queries.ts` | One hook per endpoint (`useHealth`, …); sets cache keys, polling, invalidation |
| Client | `api/client.ts` | `createClient<paths>({ baseUrl: '/' })`; re-exports schema types under friendly names |
| Generated | `api/schema.d.ts` (from `openapi.json`) | **Never edited by hand**: `uv run poe gen-client` |

Dev networking: the client uses relative `/api/...` URLs and Vite proxies them to `http://127.0.0.1:8000` (`GATP_API_URL` overrides), so the browser sees one origin.

Implemented (T-002): `HealthBadge` shows *Checking API…* / green *API ok · vX* / red *API unreachable* using `useHealth` (polls every 10 s).

## Implemented (T-009)
| Route | Screen | Talks to |
|---|---|---|
| `/` | `ProjectsPage`: list + create (name, start URL → origin) | `listProjects`, `createProject` |
| `/projects/:id` | `ProjectLayout`: header (project, origin, tester name, runner + API badges), step nav with **API-computed** status per step, open clarifications banner (answer buttons), SSE subscription | `getProject`, `getWorkflow`, `listClarifications`, `answerClarification`, `projectEvents` |
| `…/inspect` | `InspectPage`: add pages; per page tab: setup-steps editor, include/exclude regions, Inspect/Re-inspect (live "browser is open" state, browser time, blocked requests), screenshot with element boxes ⇄ findings table (flags, best locator, all candidates with usable/count), source-line modal | `listPages`, `addPage`, `setPageSetup`, `inspectPage`, `listSnapshots`, `getSnapshot`, `getFile` |
| `…/scope` | `ScopePage`: goal, notes, per-page element checkboxes (default all included), Save scope → version N, Approve G0 as <tester> | `getScope`, `saveScope`, `approve` |
| `…/plan` | `PlanPage` (T-012): propose/revise plan, cases with steps (element labels) and expectations (basis, confirmed), inline edits, delete, approve G1 | `getPlan`, `proposePlan`, `editPlan`, `approve` |
| `…/code` | `CodePage` (T-013): generate, validation report (static findings, recount table, collected tests), file tabs with editor (edit = new version), approve G2 | `getCode`, `generateCode`, `validateCode`, `approveCode`, `editArtifact` |

Components: `FindingsTable`, `ScreenshotView` (bbox overlay scaled to the screenshot), `SourceModal`, `SetupStepsEditor` (every field has an accessible label), `StatusBadge`, `RunnerBadge`, `HealthBadge`, `ErrorAlert` (shows the API's `detail`), `useTesterName` (localStorage).

## "No business logic in the UI" checklist (reviewed for T-009)
- [x] Workflow/gate status: only displayed from `GET /workflow`; the UI never decides whether a step is done.
- [x] Approve buttons send the **version id the API returned**; validity (latest version, right gate, no open clarification) is checked by the API, and its error is shown verbatim.
- [x] Locator usability, flags, default locator: shown from the snapshot; nothing is computed in TS.
- [x] Scope: the UI sends the unticked element keys as `exclude`; validation (keys exist, snapshot belongs to project) happens in the API.
- [x] Only presentation logic in TS: bbox → percentage position, date formatting, splitting the comma-separated region inputs.

## Verification
`uv run poe ui-walkthrough` starts the real fixture site, runner, API and Vite, then drives the full Phase 1 flow in a browser and saves a screenshot per step (evidence: [docs/samples/phase1-walkthrough/](../../samples/phase1-walkthrough/)). It fails on any page error.

## Known limitations
- Setup-step values (e.g. test passwords) are shown in plain text in the editor; use test accounts only (ADR-018).
- The production bundle is >500 kB (Mantine); acceptable for a local tool.
- No routing for individual snapshots/history yet (T-018).
