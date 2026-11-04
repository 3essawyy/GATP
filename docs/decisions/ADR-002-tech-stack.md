# ADR-002: Application tech stack

- **Status:** Accepted
- **Date:** 2026-11-04
- **Session:** S001
- **Related:** REQ-G1, REQ-P2-6; modules api, web-ui

## Context
Need a web-based assistant integrating LLM calls, Playwright, state, and a multi-step approval UI. The team wants a learning opportunity on the frontend.

## Decision
- **Backend:** Python 3.11+ with **FastAPI**, serving a JSON API (+ SSE for live progress).
- **Frontend:** **React + Vite + TypeScript**, deliberately **thin**: no business logic, no validation rules, no workflow decisions in the UI. All logic lives in Python.
- The TypeScript API client is **generated from FastAPI's OpenAPI schema**, never hand-written.
- Planned repo layout: `backend/` (one Python package per module), `frontend/`, `fixtures/`, `docs/`.

## Alternatives considered
| Option | Why not |
|---|---|
| FastAPI + Jinja + HTMX | Simpler and lower defense risk, but the team chose React for learning value |
| TypeScript/Node backend | LLM tooling and Python Playwright better fit; one-language test generation |
| Streamlit/Gradio | Awkward for multi-step approval flows and custom state |

## Consequences
- Two toolchains (Python + Node) in setup docs; CI must build both.
- CORS/dev-proxy config needed (Vite proxy to FastAPI in dev).
- Defense risk: teammates must explain TS code → keep UI thin and document components in the web-ui LLD.
- Rich UI pieces (code editor, diff viewer, element picker) via mature libraries (e.g., Monaco). Exact libraries are chosen in T-002 and recorded.
- Python package/env tool (uv vs pip+venv) is **open** — decide in T-002.
