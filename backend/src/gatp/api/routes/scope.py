"""Scope + selection + goal as a versioned artifact approved at gate G0 (REQ-P1-3)."""

from __future__ import annotations

from fastapi import APIRouter

from gatp.api.routes.deps import Svc
from gatp.api.schemas import ScopeIn, ScopeOut, VersionOut
from gatp.api.services import Services
from gatp.api.workflow import is_approved
from gatp.store.errors import ValidationError

router = APIRouter(prefix="/api", tags=["scope"])
SCOPE_NAME = "scope"


def _validate(svc: Services, project_id: int, body: ScopeIn) -> None:
    page_ids = {p.id for p in svc.projects.pages(project_id)}
    for entry in body.pages:
        snap = svc.snapshots.get(entry.snapshot_id)
        if snap.page_id not in page_ids:
            raise ValidationError(f"snapshot {entry.snapshot_id} is not from this project")
        keys = {e.key for e in snap.elements}
        unknown = sorted((set(entry.include) | set(entry.exclude)) - keys)
        if unknown:
            raise ValidationError(f"unknown element keys in snapshot {snap.id}: {unknown}")


def _out(svc: Services, artifact_id: int) -> ScopeOut:
    version = svc.artifacts.latest(artifact_id)
    return ScopeOut(
        artifact_id=artifact_id,
        version=VersionOut.model_validate(version),
        scope=ScopeIn.model_validate_json(version.content),
        approved=is_approved(svc, "G0", version),
    )


@router.put("/projects/{project_id}/scope", operation_id="saveScope")
def save_scope(project_id: int, body: ScopeIn, svc: Svc) -> ScopeOut:
    """Store the tester's selection, exclusions and goal as a new scope version."""
    svc.projects.get(project_id)
    _validate(svc, project_id, body)
    content = body.model_dump_json(indent=2, exclude={"actor"})
    existing = svc.artifacts.find(project_id, "scope", SCOPE_NAME)
    if existing is None:
        artifact, _ = svc.artifacts.create_artifact(
            project_id, "scope", SCOPE_NAME, content, "user", f"scope set by {body.actor}"
        )
        artifact_id = artifact.id
    else:
        artifact_id = existing.id
        if svc.artifacts.latest(artifact_id).content != content:
            svc.artifacts.new_version(artifact_id, content, "user", f"scope edited by {body.actor}")
    if body.goal:
        svc.projects.set_goal(project_id, body.goal)
    svc.events.publish(project_id, "scope_saved", {"artifact_id": artifact_id})
    return _out(svc, artifact_id)


@router.get("/projects/{project_id}/scope", operation_id="getScope")
def get_scope(project_id: int, svc: Svc) -> ScopeOut | None:
    """The latest scope, or ``null`` if none was saved yet (not an error)."""
    svc.projects.get(project_id)
    existing = svc.artifacts.find(project_id, "scope", SCOPE_NAME)
    return None if existing is None else _out(svc, existing.id)
