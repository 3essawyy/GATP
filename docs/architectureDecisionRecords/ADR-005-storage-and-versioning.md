# ADR-005: Storage and versioning

- **Status:** Accepted
- **Date:** 2026-11-04
- **Session:** S001
- **Related:** REQ-G8, REQ-P2-5, REQ-P2-D2; module store

## Context
Inspection results must be retained for later steps. Test cases and code need versions, text diffs, and restore. Setup must be reproducible and simple.

## Decision
- **SQLite** single-file database + an **`artifacts/`** folder for screenshots, traces, and run outputs (DB stores paths and hashes).
- **Immutable versions:** every edit, generation, repair, or restore creates version N+1 of an artifact. Each version records `author` (`user` | `model` | `repair` | `restore`), `reason`, `parent_version`, timestamp, and content hash.
- **Restore = new version** whose content equals the chosen old version; history is never rewritten.
- Diffs computed on the backend (unified + side-by-side data) and rendered by the UI.
- Inspection snapshots are immutable too; a rescan creates a new snapshot.

## Alternatives considered
| Option | Why not |
|---|---|
| PostgreSQL | Extra service in setup and demo |
| JSON files | Versioning and queries become messy |
| Git-backed artifact repo | More moving parts; less clear UI integration |

## Consequences
- Reset = delete the `data/` folder.
- Schema migrations needed as the model grows (tool chosen in T-004).
