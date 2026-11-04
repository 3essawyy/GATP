"""Inspections (via the runner), snapshots and artifact files."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import FileResponse

from gatp.api.inspections import to_snapshot_in
from gatp.api.routes.deps import Svc
from gatp.api.schemas import InspectIn, InspectionOut, SnapshotOut, SnapshotSummary
from gatp.api.workflow import require_no_open_clarifications
from gatp.inspector.models import InspectionResult
from gatp.runner.jobs import InspectJob, SetupStep
from gatp.store.errors import NotFoundError

router = APIRouter(prefix="/api", tags=["inspections"])


class InspectionFailedError(RuntimeError):
    """The runner ran the job but the page could not be inspected."""


@router.post("/pages/{page_id}/inspections", operation_id="inspectPage", status_code=201)
def inspect_page(page_id: int, body: InspectIn, svc: Svc) -> InspectionOut:
    """Ask the runner to open the page (visible browser), inspect it and store a snapshot."""
    page = svc.projects.get_page(page_id)
    project = svc.projects.get(page.project_id)
    require_no_open_clarifications(svc, project.id, "inspect")
    svc.events.publish(project.id, "inspection_started", {"page_id": page_id})
    job = InspectJob(
        url=page.url,
        allowlist=[project.origin],
        scope=body.scope,
        setup=[SetupStep.model_validate(s) for s in page.setup],
        timeout_s=svc.settings.runner_job_timeout_s,
    )
    result = svc.runner.submit(job)
    if result.status != "ok":
        svc.events.publish(project.id, "inspection_failed", {"page_id": page_id})
        raise InspectionFailedError(result.error or "inspection failed")
    inspection = InspectionResult.model_validate(result.data)
    snapshot = svc.snapshots.save(
        to_snapshot_in(page_id, inspection, result.files, result.duration_ms)
    )
    svc.events.publish(
        project.id, "inspection_finished", {"page_id": page_id, "snapshot_id": snapshot.id}
    )
    return InspectionOut(
        snapshot=SnapshotOut.model_validate(snapshot),
        duration_ms=result.duration_ms,
        blocked_requests=[b.model_dump() for b in result.blocked_requests],
    )


@router.get("/pages/{page_id}/snapshots", operation_id="listSnapshots")
def list_snapshots(page_id: int, svc: Svc) -> list[SnapshotSummary]:
    svc.projects.get_page(page_id)
    out = []
    for sid in reversed(svc.snapshots.list_for_page(page_id)):
        s = svc.snapshots.get(sid)
        out.append(
            SnapshotSummary(
                id=s.id,
                page_id=s.page_id,
                url=s.url,
                title=s.title,
                created_at=s.created_at,
                element_count=len(s.elements),
            )
        )
    return out


@router.get("/snapshots/{snapshot_id}", operation_id="getSnapshot")
def get_snapshot(snapshot_id: int, svc: Svc) -> SnapshotOut:
    return SnapshotOut.model_validate(svc.snapshots.get(snapshot_id))


@router.get("/files/{path:path}", operation_id="getFile", response_class=FileResponse)
def get_file(path: str, svc: Svc) -> FileResponse:
    """Serve a stored artifact file (screenshot, page HTML). Confined to ``artifacts/``."""
    full = svc.files.absolute(path)
    if not full.is_file():
        raise NotFoundError(f"file {path}")
    media = "text/plain; charset=utf-8" if full.suffix == ".html" else None
    return FileResponse(full, media_type=media)
