# SG-002: Developer workflow

- **Audience:** developer
- **Last verified:** 2026-11-04 on Linux at the T-002 merge commit

Read [CLAUDE.md](../../CLAUDE.md) for the process rules (branch per task, PLAN before code, Definition of Done). This guide covers the commands. Tooling rationale: [ADR-012](../architectureDecisionRecords/ADR-012-backend-and-dev-tooling.md), [ADR-013](../architectureDecisionRecords/ADR-013-frontend-libraries.md).

## Repository layout
```
pyproject.toml, uv.lock      Python project, tool config, poe tasks (repo root)
backend/src/gatp/            one package; one sub-package per module
  api/  inspector/  store/  llm_gateway/  test_designer/  codegen/  runner/  maintainer/
  config.py                  settings (GATP_* env vars, .env)
backend/tests/               pytest suite (incl. import-contract test)
frontend/                    Vite + React + TS (thin UI)
  openapi.json               GENERATED from FastAPI
  src/api/schema.d.ts        GENERATED from openapi.json
  src/api/client.ts          openapi-fetch client (the only way to call the API)
  src/api/queries.ts         TanStack Query hooks used by components
.github/workflows/ci.yml     CI
docs/                        all documentation
```

## Everyday commands
| Goal | Command |
|---|---|
| Everything CI runs | `uv run poe check` |
| Backend only (ruff, mypy, pytest) | `uv run poe check-backend` |
| Frontend only (eslint, prettier, tsc, build) | `uv run poe check-frontend` |
| Auto-fix Python lint + format | `uv run poe fmt` |
| Format frontend | `npm --prefix frontend run format` |
| Run one test | `uv run pytest backend/tests/test_health.py -k cors` |
| Check module boundaries only | `uv run lint-imports` |
| End-to-end smoke on real processes | `uv run poe smoke` (`--headed` for a visible browser, `--keep` to keep DB + screenshots) |
| Drive the real UI through the Phase 1 flow | `uv run poe ui-walkthrough --out walkthrough` (`--record FILE.webm` to record under Xvfb, `--phase1-only`, `--headed`) |
| Add a Python dependency | `uv add <pkg>` (dev: `uv add --dev <pkg>`); commit `pyproject.toml` + `uv.lock` |
| Add a frontend dependency | `npm --prefix frontend install --save-exact <pkg>`; commit `package.json` + `package-lock.json` |

## Changing the API → regenerate the TS client
1. Change the FastAPI routes or Pydantic models.
2. Run:
   ```bash
   uv run poe gen-client
   ```
   This writes `frontend/openapi.json` (sorted, deterministic) and regenerates `frontend/src/api/schema.d.ts`.
3. Commit both files. CI fails with "Generated client is stale" if you forget, and so does `test_committed_schema_is_current`.

Give each route an explicit `operation_id` (e.g. `getHealth`) and a Pydantic response model so the generated types have stable names.

## Database and migrations
- The schema lives in `backend/src/gatp/store/models.py`. Migrations live in `backend/src/gatp/store/migrations/versions/`.
- The database (`data/gatp.sqlite`) is created or upgraded automatically on API start, or manually with `uv run poe db-upgrade`.
- To change the schema:
  1. Edit `models.py`.
  2. Run:
     ```bash
     uv run poe db-revision "describe the change"
     ```
  3. Review the generated file and commit it with the model change.

  `test_models_match_migrations` fails if you forget step 2.
- Reset everything: delete `data/` and `artifacts/`.

## Module boundaries
`pyproject.toml` → `[tool.importlinter]` encodes the dependency direction from [modules/README](../modules/README.md#dependency-direction):
- Layers: `api` → {`test_designer`, `codegen`, `maintainer`, `runner`} → {`inspector`, `llm_gateway`, `store`}. Lower layers never import upper ones.
- Feature modules never import `runner` (only the api dispatches jobs).
- `runner` and `inspector` never import `llm_gateway` or `store` (ADR-004 isolation).
- `store` and `llm_gateway` never import `inspector`.

If a test reports a broken contract, change the design (or record an ADR and update the contract). Don't add an `ignore_imports` entry just to get green.

## CI
`.github/workflows/ci.yml` runs on every PR and on pushes to `main`, on ubuntu-latest:
- **backend:** `uv sync --locked` → `playwright install --with-deps chromium` → ruff → mypy → pytest.
- **frontend:** `npm ci` → regenerate the client and fail on diff → eslint → prettier → `tsc -b` → `vite build`.

`uv sync --locked` fails if `pyproject.toml` changed without `uv lock`; run `uv lock` and commit.
