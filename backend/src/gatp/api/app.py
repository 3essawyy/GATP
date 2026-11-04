"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from gatp import __version__
from gatp.api.schemas import Health
from gatp.config import Settings, get_settings

APP_NAME = "GATP"


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI app. Kept as a factory so tests can inject settings."""
    settings = settings or get_settings()
    app = FastAPI(
        title=f"{APP_NAME} API",
        version=__version__,
        description="Human-in-the-loop web testing assistant.",
    )
    # Dev uses the Vite proxy (same origin); CORS is only for direct calls from the dev server.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health", operation_id="getHealth", tags=["system"])
    def health() -> Health:
        """Report that the API process is up."""
        return Health(status="ok", app=APP_NAME, version=__version__)

    return app
