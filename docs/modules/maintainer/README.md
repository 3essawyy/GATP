# Module: maintainer

- **Owner:** TBD
- **Status:** Planned
- **Code:** `backend/src/gatp/maintainer/`
- **Tasks:** T-016, T-017
- **ADRs:** ADR-007

## Responsibility
On a user-requested rescan, compares the stored snapshot with the new one, flags changes, and for every element referenced by approved tests proposes an evidence-backed locator repair, or raises a clarification when ambiguous. Applies only G4-approved repairs, changing locators only (test intent preserved), and identifies affected tests for rerun.

## Algorithm (summary — full spec in PLAN-016/017)
1. Load old snapshot (referenced by the code version) and new snapshot.
2. For each referenced old element: if its default locator still resolves uniquely to a fingerprint-similar element → **unchanged**.
3. Else score all new elements by weighted fingerprint similarity.
4. Classify: **clear match** (score ≥ threshold and margin ≥ margin), **ambiguous**, or **missing**.
5. Build `ChangeSet` + `RepairProposal`s with evidence (attribute diff, score breakdown, screenshots).
6. LLM writes a plain-language explanation only.
7. On G4 approval: new page-object version (`author=repair`), list affected tests for G3 rerun.

## Known limitations
Weights tuned on our fixture site; may need retuning on the instructor's site.
