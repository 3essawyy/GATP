# Module: store

- **Owner:** TBD
- **Status:** Implemented (core, T-004)
- **Code:** `backend/src/gatp/store/`
- **Tasks:** T-004, T-018
- **ADRs:** ADR-005, ADR-015

## Responsibility
Persistence for everything: projects, pages, inspection snapshots and elements, requirements, versioned artifacts, approvals, clarifications, runs/results, change sets, repair proposals, LLM call logs. Provides repositories and the versioning API. Knows nothing about LLMs or browsers.

## Entities
See the ER diagram in [HLD §7](../../architecture/HLD.md#7-core-data-model-initial).

## Files
| File | Contents |
|---|---|
| `models.py` | SQLAlchemy models for all HLD §7 entities (`projects`, `pages`, `inspection_snapshots`, `elements`, `locator_candidates`, `requirements`, `artifacts`, `artifact_versions`, `approvals`, `clarifications`, `runs`, `run_results`, `change_sets`, `repair_proposals`, `llm_calls`) |
| `db.py` | `Database(url)`: engine (SQLite `foreign_keys=ON`, WAL), `session()` unit of work, `migrate()` → Alembic `head` |
| `migrations/` | Alembic env + versions; `0001` = initial schema + immutability triggers |
| `immutability.py` | ORM guards raising `ImmutableRowError` on update/delete of immutable rows |
| `dto.py` | Frozen dataclasses returned by repositories (`ProjectDTO`, `SnapshotDTO`, `VersionDTO`, `VersionDiff`, …) |
| `projects.py` | `ProjectRepository`: create/get/all/set_goal, `add_page` (must be on the project origin), `pages` |
| `snapshots.py` | `SnapshotRepository`: `save(SnapshotIn)`, `get`, `latest_for_page`, `list_for_page` |
| `versioning.py` | `ArtifactStore` (below) + `side_by_side()` diff rows |
| `files.py` | `ArtifactFiles(root)`: write/read files confined to `artifacts/`, returns path + SHA-256 |
| `migrate.py` | CLI behind `poe db-upgrade` / `poe db-revision` |

## Versioning API
| Function | Behavior |
|---|---|
| `create_artifact(project_id, kind, name, content, author, reason)` | Creates artifact + version 1. Kinds: `test_plan`, `test_case`, `page_object`, `test_file` |
| `new_version(artifact_id, content, author, reason, parent=None)` | Appends version N+1; `parent` defaults to the current latest |
| `get_version(artifact_id, n)` / `get_version_by_id(id)` / `latest(artifact_id)` / `history(artifact_id)` | Read |
| `diff(artifact_id, a, b)` | `VersionDiff(unified, rows)`. Each row is `DiffRow(tag, left_no, left, right_no, right)` with tag `equal`/`replace`/`delete`/`insert` |
| `restore(artifact_id, n, actor)` | New version with the content of `n`, `author=restore`, reason "Restore of vN by <actor>" |

Authors: `user` | `model` | `repair` | `restore`. Each version stores a content SHA-256.

## Immutability (two layers)
1. **ORM:** `before_update`/`before_delete` listeners on snapshots, elements, locator candidates and artifact versions raise `ImmutableRowError`.
2. **Database:** triggers `<table>_no_update` / `<table>_no_delete` `RAISE(ABORT)`, which also stops raw SQL.

## Validation and failure modes
| Failure | Detection | Behavior |
|---|---|---|
| Unknown author/kind, bad parent | `ArtifactStore` checks | `store.errors.ValidationError` |
| Page outside the project origin | `origin_of()` compare | `ValidationError` (keeps the runner allowlist meaningful) |
| Duplicate element keys in a snapshot | `SnapshotRepository.save` | `ValidationError` |
| Missing row | repository lookups | `store.errors.NotFoundError` |
| Path traversal in artifact files | `ArtifactFiles._resolve` | `ValidationError` |
| Model changed without migration | `test_models_match_migrations` | CI fails |

## Config
| Key | Default | Meaning |
|---|---|---|
| `GATP_DATA_DIR` | `data` | Folder for `gatp.sqlite` |
| `GATP_ARTIFACTS_DIR` | `artifacts` | Screenshots, HTML, traces, run outputs |
| `GATP_DATABASE_URL` | empty → `sqlite:///<data_dir>/gatp.sqlite` | Override (tests use a temp file) |

## Tests
`test_store_db.py`, `test_store_versioning.py`, `test_store_snapshots.py` (TC-104; diff/restore part of TC-211).

## Storage locations
- `data/gatp.sqlite` — database
- `artifacts/` — screenshots, traces, run outputs (DB holds paths + hashes)
Both are gitignored.

## Known limitations
- Single-user SQLite. Concurrent writers are serialized by SQLite; that's fine for a local tool.
- Artifact files are not deleted when DB rows are (nothing is deleted by design); reset = delete `data/` and `artifacts/`.
