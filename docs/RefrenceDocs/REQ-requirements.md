# Requirements (extracted from the brief)

Source: [GenAI_Fall26_project.pdf](GenAI_Fall26_project.pdf). Paraphrased into traceable IDs. If this file and the PDF disagree, the PDF wins — fix this file.

## General (G)

| ID | Requirement |
|---|---|
| REQ-G1 | Web-based assistant: inspect page, design test cases, generate Playwright code, execute approved tests, maintain tests after page changes. |
| REQ-G2 | Findings, decisions and results are understandable and reviewable. |
| REQ-G3 | Tester can guide inspection, clarify expected behavior, edit test cases, review code, approve repairs. |
| REQ-G4 | Assistant asks for clarification when evidence is insufficient. |
| REQ-G5 | Explicit approval before executing generated tests and before applying maintenance changes. |
| REQ-G6 | Only local/open-source models or free-tier APIs. No paid APIs/subscriptions. |
| REQ-G7 | Document model, configuration, hardware/API setup, practical resource limits. |
| REQ-G8 | Retain inspection results so later steps refer to what was actually observed. |
| REQ-G9 | Works against an instructor-supplied small website and a modified version. |

## Phase 1 — Week 9 — 10 pts (P1)

| ID | Rubric line | Pts | Requirement |
|---|---|---|---|
| REQ-P1-1 | Architecture and system design | 4 | Component diagram + data flow (web UI, model integration, inspection/state storage, isolated runner). Explain approval points, validation, and how later phases use inspection results. |
| REQ-P1-2 | Working page inspection | 3 | Accept URL, open visible browser, extract interactive elements, observed labels/attributes, candidate locators. Display structured findings linked to source page. |
| REQ-P1-3 | Basic human interaction | 2 | User specifies a testing goal and selects elements or refines inspection scope in the UI. |
| REQ-P1-4 | Feasibility evidence | 1 | ≥1 meaningful model call using inspection data. Record model/version, hardware/API setup, token usage, response time. |
| REQ-P1-D | Demo | — | Open page, inspect, display findings; user picks target or goal; model summarizes selected elements or suggests next action grounded in observed page. |
| REQ-P1-S | Submission | — | Short design doc (component diagram, data flow, approval gates, resource assumptions, path inspection→generation→execution→maintenance); runnable code + deps + setup + model config (no secrets); short demo; sample structured inspection output; model usage/timing evidence. |

## Phase 2 — Week 13 — 20 pts (P2)

| ID | Rubric line | Pts | Requirement |
|---|---|---|---|
| REQ-P2-1 | Collaborative test design | 4 | Cases grounded in inspected elements + user requirements; actions and meaningful expected results; editing, clarification, explicit approval of the plan. |
| REQ-P2-2 | Test implementation | 4 | Executable Playwright tests using POM. Validate syntax; verify locators against observed elements before execution. Allow code review. |
| REQ-P2-3 | Execution and review | 4 | Run approved tests in isolated runner with visible browser. Show pass/fail, screenshots, failure details. User feedback, test revision, approved reruns. |
| REQ-P2-4 | Assisted maintenance | 4 | On user-requested rescan, compare stored inspection with modified page; flag changes; propose evidence-backed locator repairs; apply approved repairs preserving intent; clarify ambiguous matches. |
| REQ-P2-5 | Versioning and visibility | 2 | Versions of test cases and code; text diffs; restore earlier version. Per-call token usage and response time; session or page-level average response time. |
| REQ-P2-6 | Integration and code defense | 2 | Reproducible setup; docs of architecture, resources, limitations; demo complete system; explain assistant code and generated tests. |
| REQ-P2-D1 | Demo sequence | — | Inspect → review/approve cases → review code → approve execution → inspect results → feedback → revise and rerun → rescan modified site → identify locator change → approve repair → rerun affected test. |
| REQ-P2-D2 | Demo extras | — | Ambiguous change with clarification; diff between artifact versions; restore earlier version. |
| REQ-P2-S | Submission | — | Source + setup; model/resource config; architecture + limitations; approved test cases + generated code; run evidence + model usage logs; short end-to-end demo. |

## Quality (Q)

| ID | Requirement |
|---|---|
| REQ-Q1 | Reference only observed elements. Validate locators incl. uniqueness when an action targets one element. |
| REQ-Q2 | Distinguish page observations from business-rule assumptions; ask tester to confirm expected behavior when not established. |
| REQ-Q3 | Meaningful assertions for approved behavior; keep real failures visible; never weaken assertions or change intent to pass. |
| REQ-Q4 | Show evidence for repairs; request guidance when multiple candidates plausible. Clarification is a valid outcome. |
| REQ-Q5 | Run browser automation and tests separately from the core app in a restricted process/container with controlled filesystem access. |
| REQ-Q6 | Limit execution to the approved testing target; prevent unrestricted host commands. |
| REQ-Q7 | Treat webpage content as data, not instructions. |
| REQ-Q8 | Show model response time separately from browser/test execution time. |
| REQ-Q9 | Use provider/runtime token counts when available; label estimates. |
| REQ-Q10 | Document rate limits and resource constraints; distinguish reused results from fresh calls. |

## Assessment notes
- Graded on functional correctness, grounded outputs, useful human interaction, maintainable code, understanding of implementation.
- Speed, model size, or more autonomy earn nothing extra.
- Brief code discussion at both submissions.
- Bonus (≤1 pt): creative work beyond requirements — explain, show it solves a problem, demonstrate it working.
