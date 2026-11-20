# ADR-013: Frontend libraries and API client generation

- **Status:** Accepted; the Monaco editor choice is superseded by [ADR-021](ADR-021-deterministic-codegen.md)
- **Date:** 2026-11-04
- **Session:** S002
- **Related:** REQ-P2-6, T-002, T-013, T-018; refines [ADR-002](ADR-002-tech-stack.md); module web-ui

## Context
ADR-002 fixes React + Vite + TS, a thin UI, and a generated TypeScript client, but leaves the libraries open. Teammates must be able to defend the TS code, so we want little hand-written code, mainstream tools and as little generated code as possible to explain.

## Decision
| Concern | Choice |
|---|---|
| Package manager | **npm** (ships with Node 22); `package-lock.json` committed; exact versions pinned |
| Lint / format | **ESLint** (flat config: `@eslint/js` + `typescript-eslint` strict + react-hooks + react-refresh) and **Prettier** |
| TypeScript | **5.9.x** (TS 7 isn't supported by `openapi-typescript`/`typescript-eslint` yet), `strict` + `noUncheckedIndexedAccess` |
| API client | **openapi-typescript** generates `src/api/schema.d.ts` (types only) from `frontend/openapi.json`; **openapi-fetch** is the small typed `fetch` wrapper (`src/api/client.ts`). The schema is exported by `python -m gatp.api.export_openapi` (no server needed). `uv run poe gen-client` does both steps. |
| Client freshness | CI regenerates the schema and types and fails on any diff; a pytest test also checks `openapi.json` |
| Server state | **TanStack Query**: hooks in `src/api/queries.ts` wrap client calls; components never call `fetch` |
| UI components | **Mantine** (`@mantine/core`, PostCSS preset) |
| Code editor + diff | **Monaco** via `@monaco-editor/react` (its `DiffEditor` covers version diffs). **Chosen now, installed in T-013.** |
| Dev networking | Vite proxies `/api` to `http://127.0.0.1:8000` (override with `GATP_API_URL`); the client uses relative URLs |
| Frontend unit tests | **Not yet.** Add Vitest + Testing Library when the UI gains logic worth testing |

## Alternatives considered
| Option | Why not |
|---|---|
| Biome | Single tool, but less familiar and fewer React rules |
| pnpm | Another tool to install on every machine |
| @hey-api/openapi-ts, orval | Generate much more code (SDK functions, hooks) that teammates would need to understand |
| Plain `useEffect` fetching | Hand-written loading/error/refetch logic on every screen |
| SWR | Weaker mutation/invalidation support for approval flows |
| Tailwind + shadcn/ui | Copies component source into the repo, which is more TS to defend |
| CodeMirror 6 | Lighter, but the diff view needs a separate merge package |

## Consequences
- Any API change must be followed by `uv run poe gen-client` and committing `frontend/openapi.json` + `frontend/src/api/schema.d.ts`.
- `npm audit` reports moderate advisories in dev-only lint tooling (transitive `minimatch`); production dependencies are clean. Re-check when bumping ESLint.
- Monaco adds a large bundle in T-013; lazy-load it on the review screens.
