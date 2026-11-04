# PLAN-010: Grounded model call + usage display (for T-010)

- **Task:** [T-010](../tasks/T-010-feasibility-llm-call.md)
- **Status:** Executed
- **Date:** 2026-11-04

## Approach
A feature function in test-designer (`insight.py`) builds the in-scope element context from the **approved** scope and calls the gateway with a schema plus an id check. The API exposes it with usage evidence (migration `0005` logs the exact request text; snapshots record browser time), and the UI shows the result, the usage and the sent request. Both real-system checks are extended.

## Steps
1. Store: `llm_calls.request`; gateway logs the exact request per attempt.
2. `test_designer/insight.py`: template `insight` v1, `Insight` schema, `scoped_elements`, `check_ids`, `request_insight`.
3. API: `POST/GET /projects/{id}/insight`, `GET /projects/{id}/llm-calls`; `meta.browser_ms` on snapshots.
4. UI: `InsightPanel`, `UsageCard`.
5. Tests + smoke step + walkthrough step.

## Tests to add
| Test | Proves |
|---|---|
| `test_api_insight.py` | G0 required; only scoped elements sent; cited ids ⊆ sent; usage fields; reuse; invented ids rejected after repair retry |
| `test_llm_gateway.py::test_each_attempt_logs_the_exact_request` | Request logging per attempt |

## Risks / open questions
| Item | Mitigation / decision |
|---|---|
| No real model in this session | Fake provider, clearly labelled in the UI; live run listed as pending |

## Deviations (filled after execution)
None.
