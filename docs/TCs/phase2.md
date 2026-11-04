# Phase 2 acceptance TCs

Status tracked in [README.md](README.md). All run against fixture site v1/v2 unless stated.

### TC-201 — Grounded test case proposals
- **Proves:** REQ-P2-1, REQ-Q2
- **Expected:** Every step cites a snapshot element; each expected result has a basis; assumption-based results flagged and need confirmation.

### TC-202 — Plan editing, clarification, approval (G1)
- **Proves:** REQ-P2-1, REQ-G3, REQ-G4
- **Expected:** Tester edits a case (new version), answers a clarification, approves; editing after approval requires re-approval.

### TC-203 — Code generation and validation
- **Proves:** REQ-P2-2
- **Expected:** POM files + tests generated; AST, locator verification, recount and collect-only all pass; report visible in review.

### TC-204 — Invalid locator caught; code review
- **Proves:** REQ-P2-2, REQ-Q1
- **Expected:** A locator not in the snapshot (injected) is flagged and blocks G2; reviewer can read/edit code; edits create versions and re-validate.

### TC-205 — Approved execution
- **Proves:** REQ-P2-3, REQ-G5, REQ-Q8
- **Expected:** Run refused without G3; with approval, visible browser runs tests; pass/fail, screenshots, failure details shown; test time separate from model time.

### TC-206 — Real failures stay visible
- **Proves:** REQ-Q3
- **Expected:** A case expecting behavior the site doesn't have fails with clear details; nothing auto-weakens the assertion.

### TC-207 — Feedback, revise, rerun
- **Proves:** REQ-P2-3, REQ-P2-D1
- **Expected:** Feedback produces a revision (diff shown); assertion loosening flagged for explicit confirmation; approved rerun executes.

### TC-208 — Rescan and change flags
- **Proves:** REQ-P2-4
- **Expected:** Rescan of v2 creates new snapshot; changes classified per fixtures README.

### TC-209 — Evidence-backed repair
- **Proves:** REQ-P2-4, REQ-Q4, REQ-P2-D1
- **Expected:** Clear change → proposal with old/new evidence and score; G4 approve → locator-only new code version; affected test rerun passes.

### TC-210 — Ambiguous change
- **Proves:** REQ-P2-4, REQ-Q4, REQ-P2-D2
- **Expected:** Assistant asks for clarification with candidates + evidence; no automatic repair; tester's choice recorded.

### TC-211 — Versions, diff, restore
- **Proves:** REQ-P2-5, REQ-P2-D2
- **Expected:** History lists versions with author/reason; diff between two versions shown; restore creates new version equal to the old one.

### TC-212 — Usage visibility
- **Proves:** REQ-P2-5, REQ-Q8–Q10
- **Expected:** Per-call tokens + response time; session or page-level average; estimates labelled; reused vs fresh distinguished; execution time separate.

### TC-213 — Security
- **Proves:** REQ-Q5–Q7
- **Expected:** Injection text on a fixture page does not alter assistant behavior; generated code with disallowed imports rejected; sandbox confinement verified.

### TC-215 — Full demo sequence
- **Proves:** REQ-P2-D1, REQ-P2-D2, REQ-P2-6
- **Steps:** Follow SG-004 demo script.
- **Expected:** Inspect → approve cases → review code → approve execution → results → feedback → revise + rerun → rescan v2 → locator change → approve repair → rerun affected; plus ambiguous clarification, version diff, restore.
