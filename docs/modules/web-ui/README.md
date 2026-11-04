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

## Screens (planned)
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
Libraries ([ADR-013](../../decisions/ADR-013-frontend-libraries.md)): Vite + React 19 + TS 5.9, Mantine (components), TanStack Query (server state), openapi-fetch + openapi-typescript (generated client), Monaco later (T-013). Routing is chosen in T-009.

Layering inside `frontend/src/`. Each layer only calls the one below it:

| Layer | Files | Rule |
|---|---|---|
| Components | `App.tsx`, `components/*` | Render data from hooks, send user intent; no `fetch`, no business rules |
| Query hooks | `api/queries.ts` | One hook per endpoint (`useHealth`, …); sets cache keys, polling, invalidation |
| Client | `api/client.ts` | `createClient<paths>({ baseUrl: '/' })`; re-exports schema types under friendly names |
| Generated | `api/schema.d.ts` (from `openapi.json`) | **Never edited by hand**: `uv run poe gen-client` |

Dev networking: the client uses relative `/api/...` URLs and Vite proxies them to `http://127.0.0.1:8000` (`GATP_API_URL` overrides), so the browser sees one origin.

Implemented (T-002): `HealthBadge` shows *Checking API…* / green *API ok · vX* / red *API unreachable* using `useHealth` (polls every 10 s).

## Known limitations
TBD.
