"""Versioned artifacts: list, history, edit (new version), diff, gated restore (G5)."""

from __future__ import annotations

from fastapi import APIRouter

from gatp.api.routes.deps import Svc
from gatp.api.schemas import ArtifactOut, DiffOut, RestoreIn, VersionIn, VersionOut
from gatp.api.workflow import GateBlockedError

router = APIRouter(prefix="/api", tags=["artifacts"])


@router.get("/projects/{project_id}/artifacts", operation_id="listArtifacts")
def list_artifacts(project_id: int, svc: Svc, kind: str | None = None) -> list[ArtifactOut]:
    svc.projects.get(project_id)
    return [ArtifactOut.model_validate(a) for a in svc.artifacts.list_artifacts(project_id, kind)]


@router.get("/artifacts/{artifact_id}/versions", operation_id="listVersions")
def list_versions(artifact_id: int, svc: Svc) -> list[VersionOut]:
    return [VersionOut.model_validate(v) for v in svc.artifacts.history(artifact_id)]


@router.get("/artifacts/{artifact_id}/versions/{number}", operation_id="getVersion")
def get_version(artifact_id: int, number: int, svc: Svc) -> VersionOut:
    return VersionOut.model_validate(svc.artifacts.get_version(artifact_id, number))


@router.post("/artifacts/{artifact_id}/versions", operation_id="editArtifact", status_code=201)
def edit_artifact(artifact_id: int, body: VersionIn, svc: Svc) -> VersionOut:
    """A tester edit: always a new version (author ``user``); approvals stay on the old one."""
    artifact = svc.artifacts.get_artifact(artifact_id)
    version = svc.artifacts.new_version(
        artifact_id, body.content, "user", f"{body.reason} ({body.actor})"
    )
    svc.events.publish(artifact.project_id, "artifact_changed", {"artifact_id": artifact_id})
    return VersionOut.model_validate(version)


@router.get("/artifacts/{artifact_id}/diff", operation_id="diffVersions")
def diff_versions(artifact_id: int, a: int, b: int, svc: Svc) -> DiffOut:
    return DiffOut.model_validate(svc.artifacts.diff(artifact_id, a, b))


@router.post("/artifacts/{artifact_id}/restore", operation_id="restoreVersion", status_code=201)
def restore_version(artifact_id: int, body: RestoreIn, svc: Svc) -> VersionOut:
    """Restore = new version with old content. Needs a G5 approval of exactly that version."""
    artifact = svc.artifacts.get_artifact(artifact_id)
    target = svc.artifacts.get_version(artifact_id, body.number)
    approval = svc.gates.get_approval(body.approval_id)
    if approval.gate != "G5" or approval.artifact_version_id != target.id:
        raise GateBlockedError(f"G5 approval of artifact {artifact_id} v{body.number} required")
    version = svc.artifacts.restore(artifact_id, body.number, approval.actor)
    svc.events.publish(artifact.project_id, "artifact_changed", {"artifact_id": artifact_id})
    return VersionOut.model_validate(version)
