# Module: web-ui

- **Owner:** TBD
- **Status:** Planned
- **Code:** `frontend/`
- **Tasks:** T-002 (scaffold), T-009, UI parts of T-010, T-012…T-019
- **ADRs:** ADR-002

## Responsibility
Presents every workflow step and collects human input and approvals. Contains **no business logic**: it never decides validity, never computes diffs or scores, never builds prompts. It renders what the API returns and sends user intent back.

## Interfaces
| Direction | Interface | Contract |
|---|---|---|
| Consumes | api (JSON) | Generated TS client from OpenAPI |
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
TBD in T-002/T-009 (routing, data fetching, component libraries).

## Known limitations
TBD.
