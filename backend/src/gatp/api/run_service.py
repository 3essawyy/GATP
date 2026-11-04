"""Approved execution (T-014, gate G3).

G3 approves an exact *subject*: the code version ids, the target origin and the tests. A run
needs a G3 approval whose subject equals the current G2-approved code; each approval
authorises one run (every rerun needs a new approval).
"""

from __future__ import annotations

import re
from typing import Any

from gatp.api.code_service import code_files
from gatp.api.services import Services
from gatp.api.workflow import GateBlockedError, is_approved, require_no_open_clarifications
from gatp.runner.jobs import RunTestsJob
from gatp.store.gates import ApprovalDTO
from gatp.store.runs import RunDTO, RunRepository

FAILING_LINE = re.compile(r"^>.*#\s*(TC-[\w-]+\.x\d+)", re.M)


def failed_expectations(details: str) -> list[str]:
    """Expectation ids on the failing line(s) of a stack excerpt.

    Generated code ends every assertion line with ``# <expectation id> [basis]``, and pytest
    marks the failing line with ``>``, so a failure maps back to the plan's expected result.
    """
    return list(dict.fromkeys(FAILING_LINE.findall(details)))


def current_subject(
    svc: Services, project_id: int, tests: list[str] | None = None
) -> dict[str, Any]:
    """What a G3 approval must name: code versions (all G2-approved), target, tests."""
    files = code_files(svc, project_id)
    if not files:
        raise GateBlockedError("generate and approve code (G2) first")
    unapproved = [f.path for f in files if not is_approved(svc, "G2", f.version)]
    if unapproved:
        raise GateBlockedError(f"code not approved (G2): {', '.join(unapproved)}")
    project = svc.projects.get(project_id)
    return {
        "code_version_ids": sorted(f.version.id for f in files),
        "target": project.origin,
        "tests": sorted(tests or []),
    }


def check_run_approval(svc: Services, project_id: int, approval: ApprovalDTO) -> dict[str, Any]:
    if approval.project_id != project_id or approval.gate != "G3":
        raise GateBlockedError("a G3 approval of this project is required to run tests")
    subject = current_subject(svc, project_id, approval.subject.get("tests"))
    if {k: approval.subject.get(k) for k in subject} != subject:
        raise GateBlockedError(
            "the approved run no longer matches the code or target; approve the run again (G3)"
        )
    return subject


def execute(svc: Services, project_id: int, approval_id: int) -> RunDTO:
    approval = svc.gates.get_approval(approval_id)
    subject = check_run_approval(svc, project_id, approval)
    require_no_open_clarifications(svc, project_id, "run")
    runs = RunRepository(svc.db)
    run = runs.start(project_id, approval_id, subject["target"], subject)
    svc.events.publish(project_id, "run_started", {"run_id": run.id})
    files = {f.path: f.version.content for f in code_files(svc, project_id)}
    result = svc.runner.submit(
        RunTestsJob(
            files=files,
            base_url=subject["target"],
            allowlist=[subject["target"]],
            tests=subject["tests"],
        )
    )
    data = result.data
    results = data.get("results", [])
    if result.status != "ok" or not results:
        status = "error"
    elif all(r["outcome"] == "passed" for r in results):
        status = "passed"
    else:
        status = "failed"
    finished = runs.finish(
        run.id,
        status,
        result.duration_ms,
        results,
        {
            "isolation": data.get("isolation"),
            "headless": data.get("headless"),
            "exit_code": data.get("exit_code"),
            "blocked_requests": data.get("blocked_requests", []),
            "error": result.error,
            "output": data.get("output", "")[-3000:] if status == "error" else "",
            "files": result.files,
        },
    )
    svc.events.publish(project_id, "run_finished", {"run_id": run.id, "status": status})
    return finished
