# Module: store

- **Owner:** TBD
- **Status:** Planned
- **Code:** `backend/gatp/store/`
- **Tasks:** T-004, T-018
- **ADRs:** ADR-005

## Responsibility
Persistence for everything: projects, pages, inspection snapshots and elements, requirements, versioned artifacts, approvals, clarifications, runs/results, change sets, repair proposals, LLM call logs. Provides repositories and the versioning API. Knows nothing about LLMs or browsers.

## Entities
See the ER diagram in [HLD §7](../../architecture/HLD.md#7-core-data-model-initial).

## Versioning API (draft)
| Function | Behavior |
|---|---|
| `create_artifact(kind, content, author, reason)` | Creates artifact + version 1 |
| `new_version(artifact_id, content, author, reason, parent)` | Appends version N+1 (immutable) |
| `get_version(artifact_id, n)` / `latest(artifact_id)` | Read |
| `diff(artifact_id, a, b)` | Unified diff + side-by-side structure |
| `restore(artifact_id, n, actor)` | New version with content of `n`, `author=restore` |

## Storage locations
- `data/gatp.sqlite` — database
- `artifacts/` — screenshots, traces, run outputs (DB holds paths + hashes)
Both are gitignored.

## Known limitations
TBD.
