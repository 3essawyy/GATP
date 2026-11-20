# ADR-019: Approvals bind to immutable versions; workflow state is computed

- **Status:** Accepted
- **Date:** 2026-11-04
- **Session:** S004
- **Related:** REQ-G2, REQ-G5, REQ-P1-3, T-008, TC-109, TC-110; builds on [ADR-005](ADR-005-storage-and-versioning.md); module api

## Context
The brief requires explicit human approval before consequential steps (REQ-G5). It also requires that edits are traceable (REQ-G2), and the HLD adds that editing an approved artifact must invalidate its approval. A stored state machine plus "revoke approval on edit" logic would be easy to get subtly wrong, e.g. by forgetting a revoke on one edit path.

## Decision
- **Gated content:** everything a gate covers is a **versioned artifact**. That includes the G0 scope (selected/excluded element keys per snapshot, goal, notes) as the new artifact kind `scope`.
- **Approvals name an exact `artifact_version_id`** (G0–G2, G5). Since versions are immutable and every change creates a new version, an edit leaves the new latest version unapproved. **Invalidation needs no code path of its own.**
- **Approval preconditions:**
  - The gate matches the artifact kind.
  - The version belongs to the same project.
  - It's the **latest** version (except G5, where the target is by definition older).
  - No clarification is open for that step.
- **G3/G4 approvals** carry a `subject` (exact run scope / repair) and are defined in T-014/T-017.
- **Workflow state is derived** on every request from snapshots, artifacts, approvals and open clarifications (`todo | needs_approval | approved | blocked`). It's never stored, so it can't drift.
- **Restore (G5)** requires the id of a G5 approval of exactly the version being restored.

## Alternatives considered
| Option | Why not |
|---|---|
| Stored workflow state column | Must be kept in sync on every edit/approval path; easy to desync |
| Approval flag on the artifact | Loses which version was approved; edits silently inherit approval |
| Revoke approvals on edit | Extra code on every edit path; history of what was approved is lost |

## Consequences
- Downstream actions must load the exact version they act on and call `require_approval` on it (codegen uses the approved plan version, runs use approved code versions).
- The approvals table is an audit trail: who approved which version of what, when, and with which comment.
