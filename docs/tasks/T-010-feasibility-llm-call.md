# T-010: Grounded LLM summary / next action + usage display

- **Status:** Done (real Gemini run 2026-11-20: see SG-003 §6 and `docs/submission/phase1/usage-evidence.json`)
- **Phase:** P1
- **Target:** W+2
- **Modules:** test-designer (`insight.py`), llm-gateway, api, web-ui, store
- **Requirements:** REQ-P1-4, REQ-P1-D, REQ-Q2, REQ-Q7, REQ-Q8, REQ-Q9, REQ-Q10
- **Depends on:** T-005, T-009
- **Plan:** [PLAN-010](../implementationPlans/PLAN-010-feasibility-llm-call.md)
- **TCs:** TC-111 Pass (fake provider in T-010; real Gemini run 2026-11-20), TC-110 (model part Pass)
- **Session:** [S004](../sessions/2026-11-04-S004-full-build-run.md)
- **Branch / PR:** `claude/serene-johnson-xtbl4s` → squash-merged to `main`

## Goal
The graded Phase 1 model call: summarise selected elements or suggest a next testing action, grounded in the snapshot, with usage evidence.

## Scope
- In: prompt template; output schema citing element IDs (rejected if unknown); UI panel showing the result + model, version, tokens (provider/estimated), latency, fresh/reused; usage evidence for submission.
- Out: test case generation (T-012).

## Acceptance criteria
- [x] Every element referenced in the response exists in what was sent (semantic `check`; invented ids → repair retry → 502, `test_invented_element_ids_are_rejected`)
- [x] Usage metrics visible and logged; model time shown separately from inspection (browser) time

## Verification (real system)
- **`poe smoke`:** the new step "re-approve + grounded model call" passes. It sends 6 elements and leaves out the element excluded in the scope; model time is reported apart from browser time.
- **`poe ui-walkthrough`:** the final screenshot is the model panel ([08-model-insight.png](../samples/phase1-walkthrough/08-model-insight.png)): the fake-provider label, estimated tokens, model time vs. browser time, "fresh call", and exactly what was sent (5 in-scope elements).
- **Fixes from reviewing it:** the request text now wraps; the browser-time label was clarified; the evidence screenshot is element-only; the output folder is cleaned first.
- **Still to do:** with a real key, run `uv run poe llm-check`, then the walkthrough with `GATP_LLM_PRIMARY=gemini`, and record the result in SG-003 §6 + TC-111.

## Explain it (code-defense prep)

**What.** After the tester approves the scope (G0), the Scope step offers "Summarise & suggest next actions". GATP sends **only the in-scope elements** of the approved scope version to the model. The model returns a summary, per-element observations, next testing actions (each marked `observed` or `assumption`), the business-rule assumptions it would need, and questions for the tester. The panel shows the answer, the usage evidence and the exact request text.

**Why:**
- **Grounding and evidence:** Phase 1 requires one meaningful model call that uses inspection data, with model/version, setup, tokens and response time recorded (REQ-P1-4).
- **Observed vs assumed:** the brief asks us to separate page observations from assumptions and to ask the tester when expected behavior isn't established (REQ-Q2).
- **Usage visibility:** model time must be shown apart from browser time (REQ-Q8), tokens labelled by source (REQ-Q9), and reused results distinguished (REQ-Q10).

**How it works:**
1. `POST /projects/{id}/insight` loads the latest scope version and calls `require_approval(G0, version)`. An unapproved scope never reaches the model.
2. `scoped_elements()` applies the scope's include/exclude to each snapshot and builds a compact, untrusted data record per element. Ids are qualified as `s<snapshot>.e<n>` because keys repeat across pages.
3. `request_insight()` calls the gateway with the `insight` template v1. Goal, notes and requirements are trusted inputs. The elements are JSON inside `<untrusted_page_data>`.
4. The response must match the `Insight` schema, and `check_ids()` rejects any element id that wasn't sent. That triggers one repair retry; if the answer is still invalid, the API returns 502 and both attempts stay in the log.
5. The gateway logs the call: provider/model/version, tokens (estimated and flagged when the provider doesn't report them), latency, fresh/reused and the **exact request text** (migration `0005`). The API adds the snapshots' recorded browser time (`meta.browser_ms`) so the UI can show both times side by side.
6. Asking again with an identical request is served from the cache and shown as "reused".

**Likely examiner questions:**
- *How do you prove the answer is grounded?* Every id it cites is checked against the set of ids actually sent. Unknown ids are rejected, never shown. The panel also shows exactly what was sent.
- *How does the tester's scope affect the model?* Only included, approved elements are sent. The tests check that an excluded element's id and name are absent from the request (TC-110).
- *Where do model time and browser time come from?* Model time is the gateway's measured latency of the provider call. Browser time is the runner's measured duration of the inspections, stored with each snapshot. They are separate numbers from separate processes.
- *What if the model invents business rules?* The schema forces them into `assumptions`, actions based on them are marked `assumption`, and open points become `questions`. In T-012 these become clarification requests that block test design until the tester answers.
