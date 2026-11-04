# T-004: Store core — schema, repositories, versioning

- **Status:** Todo
- **Phase:** P1 (foundation for P2)
- **Target:** W+1
- **Modules:** store
- **Requirements:** REQ-G8, REQ-P2-5
- **Depends on:** T-002
- **Plan:** PLAN-004 (to write)
- **TCs:** TC-104, TC-211
- **Branch / PR:** `feat/T-004-store-core`

## Goal
Persistent storage for snapshots and all versioned artifacts per ADR-005.

## Scope
- In: SQLite schema for HLD §7 entities; repositories; immutable versioning API (create, new_version, get, latest, diff, restore); artifacts folder handling; DB access layer + migrations choice (ADR).
- Out: UI for history (T-018).

## Acceptance criteria
- [ ] Unit tests: versions immutable; restore creates N+1 with author `restore`; diff returns unified + side-by-side data
- [ ] Snapshot round-trip (write → read identical)
- [ ] Fresh DB created automatically on first run

## Definition of Done
Standard (see [CLAUDE.md](../../CLAUDE.md)).

## Explain it (code-defense prep)
_To be written on completion._
