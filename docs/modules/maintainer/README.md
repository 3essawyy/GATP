# Module: maintainer

- **Owner:** TBD
- **Status:** Rescan + matching implemented (T-016); repairs planned (T-017)
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

## Implemented (T-016, [ADR-024](../../architectureDecisionRecords/ADR-024-rescan-matching-rules.md))
| File | Contents |
|---|---|
| `maintainer/match.py` | `El`, `WEIGHTS`, `field_similarity`, `score` (with breakdown), `match_page` (unchanged by locator, then scoring against appeared elements), `classify` (clear: ≥ 0.70, margin ≥ 0.15, no split; ambiguous ≥ 0.45; else missing) |
| api `maintain_service.py` | Used elements from plan + setup steps; rescan of approved pages; read-only setup retry; per-page summaries |
| api `routes/maintain.py` | `POST /projects/{id}/rescans`, `GET /projects/{id}/rescans/latest` |
| store `rescans.py` | `rescans` + `change_sets` (migration 0007), write-once |

Fixture v1 → v2 results: FXC-1 sign-in 0.85 → clear; FXC-2 Save → Save draft 0.81 / Publish 0.69 → ambiguous (split); FXC-3 → "page HTML changed".

## Known limitations
Weights tuned on our fixture site; may need retuning on the instructor's site.
