"""FastAPI application factory.

On startup the database is migrated (a fresh one is created on first run) and the runner
client is prepared. Domain errors map to HTTP status codes in one place.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from gatp import __version__
from gatp.api.routes import artifacts, assist, gates, inspections, projects, scope, system
from gatp.api.routes.inspections import InspectionFailedError
from gatp.api.services import Services, build_services
from gatp.api.workflow import GateBlockedError
from gatp.config import Settings, get_settings
from gatp.llm_gateway.gateway import LLMOutputError, LLMUnavailableError
from gatp.runner.client import RunnerRejectedError, RunnerUnavailableError
from gatp.store.errors import NotFoundError, ValidationError

APP_NAME = system.APP_NAME

# Domain error -> (HTTP status, machine-readable code)
ERRORS: dict[type[Exception], tuple[int, str]] = {
    NotFoundError: (404, "not_found"),
    ValidationError: (422, "invalid"),
    GateBlockedError: (409, "gate_blocked"),
    RunnerUnavailableError: (503, "runner_unavailable"),
    RunnerRejectedError: (400, "runner_rejected"),
    InspectionFailedError: (502, "inspection_failed"),
    LLMUnavailableError: (503, "model_unavailable"),
    LLMOutputError: (502, "model_output_invalid"),
}


def create_app(settings: Settings | None = None, services: Services | None = None) -> FastAPI:
    """Build the app. Tests pass ``services``; otherwise they are built at startup."""
    settings = settings or (services.settings if services else get_settings())

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        svc = services or build_services(settings)
        svc.events.bind(asyncio.get_running_loop())
        app.state.services = svc
        yield

    app = FastAPI(
        title=f"{APP_NAME} API",
        version=__version__,
        description="Human-in-the-loop web testing assistant.",
        lifespan=lifespan,
    )
    # Dev uses the Vite proxy (same origin); CORS is only for direct calls from the dev server.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for module in (system, projects, inspections, scope, artifacts, gates, assist):
        app.include_router(module.router)

    for exc_type, (status, code) in ERRORS.items():

        def handler(
            _request: Request, exc: Exception, status: int = status, code: str = code
        ) -> JSONResponse:
            return JSONResponse(status_code=status, content={"error": code, "detail": str(exc)})

        app.add_exception_handler(exc_type, handler)
    return app
