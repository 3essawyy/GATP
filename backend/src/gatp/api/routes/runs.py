"""Approved test execution: what G3 covers, run, results (T-014)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from gatp.api.code_service import code_files, latest_report_for_current
from gatp.api.routes.deps import Svc
from gatp.api.run_service import current_subject, execute, failed_expectations
from gatp.store.runs import RunDTO, RunRepository

router = APIRouter(prefix="/api", tags=["runs"])


class RunSubjectOut(BaseModel):
    """Exactly what a G3 approval will authorise."""

    subject: dict[str, Any]
    files: list[str]
    available_tests: list[str] = Field(description="Collected test ids from the validation")
    isolation: str
    headless: bool
    timeout_s: float


class RunIn(BaseModel):
    approval_id: int


class RunResultOut(BaseModel):
    id: int
    test_id: str
    outcome: str
    duration_ms: int
    message: str
    screenshot_path: str
    details: str
    failed_expectations: list[str] = Field(
        default_factory=list, description="Plan expectation ids on the failing line (T-015)"
    )


class RunOut(BaseModel):
    id: int
    project_id: int
    approval_id: int | None
    status: str
    target_url: str
    scope: dict[str, Any]
    duration_ms: int | None = Field(
        description="Test execution time in the runner (not model time)"
    )
    created_at: datetime
    finished_at: datetime | None
    results: list[RunResultOut]


def run_out(r: RunDTO) -> RunOut:
    return RunOut(
        id=r.id,
        project_id=r.project_id,
        approval_id=r.approval_id,
        status=r.status,
        target_url=r.target_url,
        scope=r.scope,
        duration_ms=r.duration_ms,
        created_at=r.created_at,
        finished_at=r.finished_at,
        results=[
            RunResultOut(
                id=x.id,
                test_id=x.test_id,
                outcome=x.outcome,
                duration_ms=x.duration_ms,
                message=x.message,
                screenshot_path=x.screenshot_path,
                details=x.trace_path,
                failed_expectations=failed_expectations(x.trace_path),
            )
            for x in r.results
        ],
    )


@router.get("/projects/{project_id}/runs/subject", operation_id="getRunSubject")
def run_subject(project_id: int, svc: Svc) -> RunSubjectOut:
    report = latest_report_for_current(svc, project_id)
    tests = list(report.report.get("collect", {}).get("tests", [])) if report else []
    return RunSubjectOut(
        subject=current_subject(svc, project_id),
        files=[f.path for f in code_files(svc, project_id)],
        available_tests=tests,
        isolation=svc.settings.runner_isolation,
        headless=svc.settings.runner_headless,
        timeout_s=300.0,
    )


@router.post("/projects/{project_id}/runs", operation_id="startRun", status_code=201)
def start_run(project_id: int, body: RunIn, svc: Svc) -> RunOut:
    """Run exactly what the G3 approval names, in the runner (visible browser, sandbox)."""
    return run_out(execute(svc, project_id, body.approval_id))


@router.get("/projects/{project_id}/runs", operation_id="listRuns")
def list_runs(project_id: int, svc: Svc) -> list[RunOut]:
    svc.projects.get(project_id)
    return [run_out(r) for r in RunRepository(svc.db).for_project(project_id)]


@router.get("/runs/{run_id}", operation_id="getRun")
def get_run(run_id: int, svc: Svc) -> RunOut:
    return run_out(RunRepository(svc.db).get(run_id))
