# ADR-015: Database access with SQLAlchemy 2 + Alembic; immutability enforced twice

- **Status:** Accepted
- **Date:** 2026-11-04
- **Session:** S004
- **Related:** REQ-G8, REQ-P2-5, T-004, TC-104; refines [ADR-005](ADR-005-storage-and-versioning.md); module store

## Context
ADR-005 chose SQLite + an artifacts folder with immutable versions but left the access layer and migration tool open. The code is checked with mypy `--strict`, the schema will grow in later tasks, and "versions are immutable" has to be defensible in the code review.

## Decision
- **SQLAlchemy 2.x ORM** with typed `Mapped[...]` models (`gatp/store/models.py`), one model per HLD §7 entity.
- **Alembic** migrations packaged in `gatp/store/migrations/`. `Database.migrate()` upgrades to `head`, so the first run creates `data/gatp.sqlite` automatically. `render_as_batch=True` is set for SQLite ALTERs.
- **Repositories return frozen dataclasses** (`gatp/store/dto.py`), never ORM objects. Sessions stay inside the store, and the other modules never import SQLAlchemy.
- **Immutability is enforced twice:**
  - ORM `before_update`/`before_delete` listeners raise `ImmutableRowError`.
  - SQLite triggers (`RAISE(ABORT)`) on `inspection_snapshots`, `elements`, `locator_candidates` and `artifact_versions` block raw SQL as well.
- **Timestamps** are naive UTC (SQLite has no timezone type).
- **Artifact files** live under `artifacts/` and are referenced by relative path + SHA-256. `ArtifactFiles` rejects paths that would escape the root.
- A test compares `models.py` with the migrated schema, so a model change without a migration fails CI.

## Alternatives considered
| Option | Why not |
|---|---|
| SQLModel | Weaker typing; blurs API schemas and DB rows |
| Raw `sqlite3` + SQL files | Hand-written mapping and migration runner |
| `Base.metadata.create_all()` without Alembic | No upgrade path once real data exists |

## Consequences
- Every schema change goes through `uv run poe db-revision "…"`, followed by a review of the generated file.
- Two layers of immutability mean tests must roll back after expecting `ImmutableRowError`.
