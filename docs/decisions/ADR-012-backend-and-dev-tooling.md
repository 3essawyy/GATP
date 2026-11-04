# ADR-012: Backend and developer tooling (uv, ruff, mypy strict, poethepoet, single package)

- **Status:** Accepted
- **Date:** 2026-11-04
- **Session:** S002
- **Related:** REQ-P1-S, REQ-P2-6, T-002, TC-102; refines [ADR-002](ADR-002-tech-stack.md), [ADR-004](ADR-004-runner-isolation.md)

## Context
ADR-002 left the Python environment tool and the lint/type tools open. The team is mixed: at least one member uses native Windows, so the setup and the "one command to start each process" requirement (T-002, TC-102) must work without Make or bash. Claude writes most of the code, so the checks must be strict and fully automated.

## Decision
| Concern | Choice |
|---|---|
| Python version | **3.12** (`.python-version`; `requires-python = ">=3.12,<3.14"`). Refines ADR-002's "3.11+". |
| Env / packages | **uv**: installs Python, creates `.venv`, locks dependencies in `uv.lock`, runs commands (`uv run …`). CI uses `uv sync --locked`. |
| Lint + format | **ruff** (rules E, W, F, I, B, UP, SIM, RUF, N, S, PT; line length 100), Python files only |
| Types | **mypy `--strict`** with the Pydantic plugin, over `backend/src` and `backend/tests` |
| Tests | **pytest** (+ FastAPI `TestClient`) |
| Task runner | **poethepoet**, with tasks in `pyproject.toml`, run as `uv run poe <task>`. It works the same on Windows, macOS and Linux. Frontend tasks call `npm --prefix frontend …`. |
| Package layout | **One** `pyproject.toml` at the repo root. **One** package `gatp` at `backend/src/gatp/`, with **one sub-package per module**. |
| Process separation | The runner is a separate **process** (`gatp-runner` script) sharing the venv, not a separate env. |
| Module boundaries | **import-linter** contracts in `pyproject.toml` mirror the dependency direction in [modules/README](../modules/README.md#dependency-direction); a pytest test fails when they break. |
| Pre-commit hooks | **None.** `uv run poe check` locally; CI enforces. |
| CI | GitHub Actions on **ubuntu-latest only**: backend job (ruff, mypy, pytest with Chromium installed), frontend job (see ADR-013). |

## Alternatives considered
| Option | Why not |
|---|---|
| pip + venv | No lockfile without extra tools; OS-specific activation steps make TC-102 fragile |
| Poetry | Slower; no Python version management |
| pyright | Needs Node in the Python job; Pydantic support less explicit than mypy's plugin |
| Make / justfile | Make is unavailable on native Windows; `just` is another binary every member must install |
| uv workspace (one package per module) | 9 pyprojects is too much friction for a 4-person team; import-linter gives the boundary check without it |
| Separate runner venv | A stronger isolation story, but two setups; ADR-004's isolation is about process, filesystem and network, which don't depend on the venv. Can be revisited in T-006/T-020. |
| pre-commit framework | Extra setup per member, slow on Windows; teammates rarely commit code |
| Windows CI job | ~3 extra min per PR; we rely on poe for portability and verify manually on Windows during TC-102 |

## Consequences
- Fresh setup is `uv sync` + `npm --prefix frontend ci` + `uv run poe browsers` (SG-001).
- `mypy --strict` means every function is annotated; untyped third-party modules need an override in `pyproject.toml`.
- Runner and API share one dependency set, so the runner *could* import LLM/store code. import-linter forbids that, which makes ADR-004's boundary a checked rule.
- No Windows CI: Windows regressions are caught by TC-102 runs and teammates, not CI.
