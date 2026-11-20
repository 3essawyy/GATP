# Phase 1 code-defense preparation

Each component owner rehearses their row: explain the claim in their own words, then answer the questions without notes. Full answers are in each task's **Explain it** section (linked). Grouping per [modules/README](../../modules/README.md).

| Owner group | Component | One-sentence claim to defend | Questions to rehearse | Full answers |
|---|---|---|---|---|
| ④ api + store + web-ui | Repo/tooling | One command per process, strict checks, generated TS client, real-system tests in CI | Why uv/poe? How do you know the TS client matches the API? What does `poe smoke` prove that unit tests don't? | [T-002](../../tasks/T-002-repo-skeleton-ci.md#explain-it-code-defense-prep), [T-008 Verification](../../tasks/T-008-api-core.md#verification-real-system) |
| (team) | Fixture site | v2 contains exactly one clear and one ambiguous change, proven by a diff test | Why is FXC-1 clear but FXC-2 ambiguous? How do you know v2 has no other changes? | [T-003](../../tasks/T-003-fixture-site.md#explain-it-code-defense-prep) |
| ④ | Store | Versions are append-only; restore adds a version; immutability is enforced by the ORM **and** by DB triggers | How can't old versions change? What does restore do to history? Why Alembic? | [T-004](../../tasks/T-004-store-core.md#explain-it-code-defense-prep) |
| ② llm-gateway + test-designer | LLM gateway | One validated, logged entry point with cache, backoff, fallback and untrusted-data framing | How do you stop prompt injection? What if the quota runs out mid-demo? Are the tokens real? | [T-005](../../tasks/T-005-llm-gateway.md#explain-it-code-defense-prep) |
| ① inspector + runner | Runner | A separate process on a private Unix socket; typed jobs only; sandbox per job; network allowlist | Can the page reach other sites? Can someone send a shell command? Why not localhost HTTP? Is it really isolated? | [T-006](../../tasks/T-006-runner-skeleton.md#explain-it-code-defense-prep) |
| ① | Inspector | Every locator is executed live; usable = unique **and** this element; weak elements are flagged | How do you know the locator is right? Two identical "Delete" buttons? Does inspection change the page? | [T-007](../../tasks/T-007-inspector.md#explain-it-code-defense-prep) |
| ④ | API + gates | Approvals bind to exact versions; edits reopen the gate automatically; workflow state is computed | What stops tests running without approval? How does an edit invalidate approval? What blocks a step? | [T-008](../../tasks/T-008-api-core.md#explain-it-code-defense-prep) |
| ④ | Web UI | Thin: displays the API's decisions, sends user intent; verified in a real browser | Where is the logic that decides a step is done? How is the element highlighted? | [T-009](../../tasks/T-009-ui-inspection.md#explain-it-code-defense-prep) |
| ② | Grounded model call | Only approved, in-scope elements are sent; cited ids are checked; observed vs assumed; usage visible | How do you prove grounding? How does scope affect the model? Where do the two timings come from? | [T-010](../../tasks/T-010-feasibility-llm-call.md#explain-it-code-defense-prep) |

## Rehearsal checklist
- [ ] Every member can run the Phase 1 demo from [SG-004](../../SystemGuides/SG-004-demo-script.md) on their Linux/WSL machine.
- [ ] Every owner answers their row's questions without notes.
- [ ] Someone can explain any decision in the [ADR index](../../architectureDecisionRecords/README.md) (why, alternatives, consequences).
- [ ] Real Gemini: `uv run poe llm-check` passes on the demo machine and SG-003 §6 is filled in.
