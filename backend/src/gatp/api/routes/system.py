"""Health checks and the per-project Server-Sent Events stream."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from gatp import __version__
from gatp.api.routes.deps import Svc
from gatp.api.schemas import Health, RunnerHealth
from gatp.runner.client import RunnerUnavailableError

APP_NAME = "GATP"
router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health", operation_id="getHealth")
def health() -> Health:
    """Report that the API process is up."""
    return Health(status="ok", app=APP_NAME, version=__version__)


@router.get("/runner/health", operation_id="getRunnerHealth")
def runner_health(svc: Svc) -> RunnerHealth:
    try:
        info = svc.runner.health()
    except RunnerUnavailableError as exc:
        return RunnerHealth(available=False, detail=str(exc))
    return RunnerHealth(available=True, headless=info.get("headless") == "true")


@router.get(
    "/projects/{project_id}/events",
    operation_id="projectEvents",
    response_class=StreamingResponse,
    responses={200: {"content": {"text/event-stream": {}}}},
)
async def project_events(project_id: int, svc: Svc) -> StreamingResponse:
    """Live updates (inspection started/finished, approvals, …) as Server-Sent Events."""
    return StreamingResponse(svc.events.stream(project_id), media_type="text/event-stream")
