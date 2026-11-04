"""Generated code: generate from the approved plan, read, validate, approve (T-013, G2)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from gatp.api.code_service import (
    code_files,
    generate,
    latest_report_for_current,
    run_validation,
)
from gatp.api.routes.deps import Svc
from gatp.api.schemas import ApprovalOut, VersionOut
from gatp.api.services import Services
from gatp.api.workflow import check_approvable, is_approved

router = APIRouter(prefix="/api", tags=["code"])


class CodeFileOut(BaseModel):
    artifact_id: int
    path: str
    kind: str
    version: VersionOut
    approved: bool


class ReportOut(BaseModel):
    id: int
    ok: bool
    version_ids: list[int]
    report: dict[str, Any]
    created_at: datetime


class CodeOut(BaseModel):
    files: list[CodeFileOut]
    report: ReportOut | None = Field(
        description="Latest report, only if it covers these exact versions"
    )
    approved: bool = Field(description="Every current file version carries G2")


class ApproveCodeIn(BaseModel):
    actor: str = Field(min_length=1, max_length=100)
    comment: str = Field(default="", max_length=2000)


def _out(svc: Services, project_id: int) -> CodeOut:
    files = [
        CodeFileOut(
            artifact_id=f.artifact_id,
            path=f.path,
            kind=f.kind,
            version=VersionOut.model_validate(f.version),
            approved=is_approved(svc, "G2", f.version),
        )
        for f in code_files(svc, project_id)
    ]
    report = latest_report_for_current(svc, project_id)
    return CodeOut(
        files=files,
        report=None
        if report is None
        else ReportOut(
            id=report.id,
            ok=report.ok,
            version_ids=list(report.version_ids),
            report=report.report,
            created_at=report.created_at,
        ),
        approved=bool(files) and all(f.approved for f in files),
    )


@router.post("/projects/{project_id}/code/generate", operation_id="generateCode", status_code=201)
def generate_code(project_id: int, svc: Svc) -> CodeOut:
    """Render Page Objects + tests from the G1-approved plan (deterministic, no model call)."""
    generate(svc, project_id)
    return _out(svc, project_id)


@router.get("/projects/{project_id}/code", operation_id="getCode")
def get_code(project_id: int, svc: Svc) -> CodeOut:
    svc.projects.get(project_id)
    return _out(svc, project_id)


@router.post("/projects/{project_id}/code/validate", operation_id="validateCode")
def validate_code(project_id: int, svc: Svc) -> CodeOut:
    """Static checks + live recount + pytest --collect-only in the runner; stores the report."""
    run_validation(svc, project_id)
    return _out(svc, project_id)


@router.post("/projects/{project_id}/code/approve", operation_id="approveCode", status_code=201)
def approve_code(project_id: int, body: ApproveCodeIn, svc: Svc) -> list[ApprovalOut]:
    """G2 for every current file version (each must be latest and covered by a passing report)."""
    files = code_files(svc, project_id)
    for f in files:
        check_approvable(svc, project_id, "G2", f.version)
    approvals = [
        svc.gates.approve(
            project_id, "G2", body.actor, artifact_version_id=f.version.id, comment=body.comment
        )
        for f in files
        if not is_approved(svc, "G2", f.version)
    ]
    svc.events.publish(project_id, "approved", {"gate": "G2"})
    return [ApprovalOut.model_validate(a) for a in approvals]
