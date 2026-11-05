"""Maintenance: rescan the approved pages and flag changes (T-016); repairs follow in T-017."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from gatp.api.maintain_service import rescan
from gatp.api.routes.deps import Svc
from gatp.store.rescans import RescanDTO, RescanRepository

router = APIRouter(prefix="/api", tags=["maintain"])


class ChangeSetOut(BaseModel):
    id: int
    old_snapshot_id: int
    new_snapshot_id: int
    summary: dict[str, Any] = Field(
        description="page_url, html_changed, counts (referenced elements), elements, appeared"
    )


class RescanOut(BaseModel):
    id: int
    project_id: int
    summary: dict[str, Any] = Field(description="pages (errors, setup trial), referenced_changes")
    created_at: datetime
    change_sets: list[ChangeSetOut]


def rescan_out(r: RescanDTO) -> RescanOut:
    return RescanOut(
        id=r.id,
        project_id=r.project_id,
        summary=r.summary,
        created_at=r.created_at,
        change_sets=[ChangeSetOut(**vars(c)) for c in r.change_sets],
    )


@router.post("/projects/{project_id}/rescans", operation_id="rescanProject", status_code=201)
def start_rescan(project_id: int, svc: Svc) -> RescanOut:
    """Inspect every approved page again and compare with the snapshots the tests use."""
    return rescan_out(rescan(svc, project_id))


@router.get("/projects/{project_id}/rescans/latest", operation_id="getLatestRescan")
def latest_rescan(project_id: int, svc: Svc) -> RescanOut | None:
    svc.projects.get(project_id)
    found = RescanRepository(svc.db).latest(project_id)
    return None if found is None else rescan_out(found)
