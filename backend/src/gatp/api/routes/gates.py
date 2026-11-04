"""Approvals (G0-G5), clarifications and the computed workflow state."""

from __future__ import annotations

from fastapi import APIRouter

from gatp.api.plan_service import apply_answer
from gatp.api.routes.deps import Svc
from gatp.api.schemas import (
    AnswerIn,
    ApprovalIn,
    ApprovalOut,
    ClarificationOut,
    GateInfo,
    StepOut,
)
from gatp.api.workflow import GateBlockedError, check_approvable, workflow_state
from gatp.store.gates import GATES

router = APIRouter(prefix="/api", tags=["gates"])


@router.get("/gates", operation_id="listGates")
def list_gates() -> list[GateInfo]:
    return [GateInfo(gate=g, description=d) for g, d in GATES.items()]


@router.post("/projects/{project_id}/approvals", operation_id="approve", status_code=201)
def approve(project_id: int, body: ApprovalIn, svc: Svc) -> ApprovalOut:
    """Record a human approval bound to an exact version (G0-G2, G5) or a subject (G3, G4)."""
    svc.projects.get(project_id)
    if body.artifact_version_id is not None:
        version = svc.artifacts.get_version_by_id(body.artifact_version_id)
        check_approvable(svc, project_id, body.gate, version)
    elif body.gate in ("G0", "G1", "G2", "G5"):
        raise GateBlockedError(f"{body.gate} approvals must name the exact artifact version")
    approval = svc.gates.approve(
        project_id,
        body.gate,
        body.actor,
        artifact_version_id=body.artifact_version_id,
        subject=body.subject,
        comment=body.comment,
    )
    svc.events.publish(project_id, "approved", {"gate": body.gate, "approval_id": approval.id})
    return ApprovalOut.model_validate(approval)


@router.get("/projects/{project_id}/approvals", operation_id="listApprovals")
def list_approvals(project_id: int, svc: Svc) -> list[ApprovalOut]:
    return [ApprovalOut.model_validate(a) for a in svc.gates.approvals(project_id)]


@router.get("/projects/{project_id}/clarifications", operation_id="listClarifications")
def list_clarifications(
    project_id: int, svc: Svc, status: str | None = None
) -> list[ClarificationOut]:
    rows = svc.gates.clarifications(project_id, status=status)
    return [ClarificationOut.model_validate(c) for c in rows]


@router.post("/clarifications/{clarification_id}/answer", operation_id="answerClarification")
def answer_clarification(clarification_id: int, body: AnswerIn, svc: Svc) -> ClarificationOut:
    answered = svc.gates.answer(clarification_id, body.answer, body.actor)
    apply_answer(svc, answered)  # e.g. confirm/remove/correct a plan assumption (new version)
    svc.events.publish(answered.project_id, "clarification_answered", {"id": clarification_id})
    return ClarificationOut.model_validate(answered)


@router.get("/projects/{project_id}/workflow", operation_id="getWorkflow")
def get_workflow(project_id: int, svc: Svc) -> list[StepOut]:
    svc.projects.get(project_id)
    return [StepOut.model_validate(s) for s in workflow_state(svc, project_id)]
