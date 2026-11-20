# T-004: Store core — schema, repositories, versioning

- **Status:** Done
- **Phase:** P1 (foundation for P2)
- **Target:** W+1
- **Modules:** store
- **Requirements:** REQ-G8, REQ-P2-5
- **Depends on:** T-002
- **Plan:** [PLAN-004](../implementationPlans/PLAN-004-store-core.md)
- **ADRs:** [ADR-015](../architectureDecisionRecords/ADR-015-db-access-sqlalchemy-alembic.md)
- **TCs:** TC-104 (Pass), TC-211 (store part)
- **Session:** [S004](../sessions/2026-11-04-S004-full-build-run.md)
- **Branch / PR:** `claude/serene-johnson-xtbl4s` → squash-merged to `main`

## Goal
Persistent storage for snapshots and all versioned artifacts per ADR-005.

## Scope
- In: SQLite schema for HLD §7 entities; repositories; immutable versioning API (create, new_version, get, latest, diff, restore); artifacts folder handling; DB access layer + migrations choice (ADR).
- Out: UI for history (T-018).

## Acceptance criteria
- [x] Unit tests: versions immutable; restore creates N+1 with author `restore`; diff returns unified + side-by-side data
- [x] Snapshot round-trip (write → read identical)
- [x] Fresh DB created automatically on first run

## Explain it (code-defense prep)

**What.** `gatp.store` holds every piece of GATP state, all of it in one SQLite file plus an `artifacts/` folder:
- **The data model:** the 15 tables of the HLD §7 data model, defined as SQLAlchemy models.
- **Migrations:** Alembic migrations that create or upgrade the schema automatically.
- **Repositories:** small classes that read and write the data and hand back plain frozen dataclasses:
  - `ProjectRepository` for projects and pages.
  - `SnapshotRepository` for inspection results.
  - `ArtifactStore` for versioned test plans, cases and code.
  - `ArtifactFiles` for screenshots and other files.

**Why:**
- **SQLite:** a single file needs zero setup for examiners (ADR-005).
- **SQLAlchemy:** typed models pass mypy `--strict`.
- **Alembic:** the schema will grow in later tasks without anyone deleting their data (ADR-015).
- **Dataclasses, not ORM objects:** returning frozen dataclasses means no other module touches a database session, so lazy-loading bugs and accidental writes outside the store can't happen.
- **Immutable versions:** the brief requires versioned artifacts with diff and restore (REQ-P2-5, REQ-P2-D2). Making versions *append-only* means history can't be lost, and restore is simply "copy an old version into a new one".

**How it works:**
- **Database startup:** `Database(url)` creates the engine. It turns on SQLite foreign keys and WAL mode on every connection and installs the immutability guards. `migrate()` runs `alembic upgrade head` on the same connection, so the first call creates every table and later calls apply only new migrations.
- **`create_artifact`** inserts the artifact row and version 1 in one transaction.
- **`new_version`** computes `max(number)+1` and stores the content, its SHA-256, the author (`user` | `model` | `repair` | `restore`), the reason, and the parent number.
- **`restore(n)`** reads version *n* and calls `new_version` with `author="restore"`. History only grows.
- **`diff(a, b)`** uses Python `difflib`. It returns a unified diff (for download or review) plus side-by-side rows (`equal`/`replace`/`delete`/`insert` with line numbers), which the UI renders in two columns in T-018.
- **Immutability, enforced twice:**
  1. ORM listeners raise `ImmutableRowError` before any UPDATE or DELETE on snapshots, elements, locators or versions.
  2. The initial migration installs SQLite triggers that `RAISE(ABORT)`, so even a raw `UPDATE artifact_versions …` fails.
- **Snapshots:** `SnapshotRepository.save` writes a snapshot, its elements and their ranked locators atomically. `LocatorDTO.unique` is `match_count == 1`, the ADR-006 rule for when a locator is usable.
- **Pages:** `ProjectRepository.add_page` refuses URLs outside the project's origin, which keeps the runner allowlist (one origin per project) meaningful.
- **Files:** `ArtifactFiles` refuses absolute paths and `..`, so a crafted file name can't write outside `artifacts/`.

**Likely examiner questions:**
- *How do you guarantee old versions can't be changed?* There are two independent layers: ORM guards and database triggers. Tests prove both, including raw SQL. The API offers no update method, only `new_version`.
- *What does "restore" do to history?* Nothing is removed. Restoring v1 when v3 is the latest creates v4 with v1's content, `author=restore`, and a reason naming who restored it.
- *Why not just `create_all()`?* That can create tables but can't change them. Alembic records each schema change as a reviewable file, and `test_models_match_migrations` fails if a model changes without one.
- *How do I reset GATP?* Delete `data/` and `artifacts/`. The next start recreates an empty database.
- *Why are times naive?* SQLite has no timezone type, so we store UTC everywhere and say so in the code.
