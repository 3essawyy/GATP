"""Test plan endpoints: propose / revise with the model, edit, read (T-012, gate G1)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from gatp.api.context import approved_scope
from gatp.api.plan_service import current_plan, element_labels, plan_blockers, store_plan
from gatp.api.routes.deps import Svc
from gatp.api.schemas import ClarificationOut, LlmCallOut, VersionOut
from gatp.api.services import Services
from gatp.api.workflow import is_approved, require_no_open_clarifications
from gatp.store.errors import ValidationError
from gatp.test_designer.plan import TestPlan, element_index, propose_plan, validate_plan

router = APIRouter(prefix="/api", tags=["plan"])


class ProposeIn(BaseModel):
    feedback: str = Field(default="", max_length=5000, description="Revise the current plan")


class PlanEditIn(BaseModel):
    plan: TestPlan
    reason: str = Field(min_length=1, max_length=2000)
    actor: str = Field(default="tester", max_length=100)


class PlanOut(BaseModel):
    artifact_id: int
    version: VersionOut
    plan: TestPlan
    approved: bool
    blockers: list[str] = Field(description="Why G1 is not possible yet (empty = approvable)")
    validation_errors: list[str]
    open_clarifications: list[ClarificationOut]
    element_labels: dict[str, str] = Field(
        default_factory=dict, description='Display label per element id, e.g. button "Save"'
    )
    call: LlmCallOut | None = None


def _out(svc: Services, project_id: int, call: LlmCallOut | None = None) -> PlanOut | None:
    found = current_plan(svc, project_id)
    if found is None:
        return None
    artifact_id, version, plan = found
    try:
        ctx = approved_scope(svc, project_id)
        errors = validate_plan(plan, element_index(ctx.elements), {p["url"] for p in ctx.pages})
    except Exception as exc:  # surface why the plan can't be checked
        errors = [f"cannot validate against the approved scope: {exc}"]
    open_ = svc.gates.clarifications(project_id, step="plan", status="open")
    blockers = plan_blockers(plan) + errors
    if open_:
        blockers.append(f"{len(open_)} open clarification(s)")
    return PlanOut(
        artifact_id=artifact_id,
        version=VersionOut.model_validate(version),
        plan=plan,
        approved=is_approved(svc, "G1", version),
        blockers=blockers,
        validation_errors=errors,
        open_clarifications=[ClarificationOut.model_validate(c) for c in open_],
        element_labels=element_labels(svc, project_id),
        call=call,
    )


@router.post("/projects/{project_id}/plan/propose", operation_id="proposePlan", status_code=201)
def propose(project_id: int, body: ProposeIn, svc: Svc) -> PlanOut:
    """Ask the model for a plan grounded in the approved scope (or revise it with feedback)."""
    project = svc.projects.get(project_id)
    ctx = approved_scope(svc, project_id)
    require_no_open_clarifications(svc, project_id, "scope")
    existing = current_plan(svc, project_id)
    answers = [
        f"Q: {c.question} A: {c.answer}"
        for c in svc.gates.clarifications(project_id, status="answered")
    ]
    svc.events.publish(project_id, "model_call_started", {"purpose": "test_plan"})
    result = propose_plan(
        svc.llm,
        project_id=project_id,
        goal=str(ctx.scope.get("goal") or project.goal),
        notes=str(ctx.scope.get("notes") or ""),
        requirements=[r.text for r in svc.gates.requirements(project_id)],
        answers=answers,
        elements=ctx.elements,
        pages=ctx.pages,
        current=existing[2] if existing and body.feedback else None,
        feedback=body.feedback,
    )
    reason = f"revised by model: {body.feedback}" if body.feedback else "proposed by model"
    store_plan(svc, project_id, result.value, "model", f"{reason} (call #{result.call.id})")
    svc.events.publish(project_id, "model_call_finished", {"call_id": result.call.id})
    out = _out(svc, project_id, LlmCallOut.model_validate(result.call))
    assert out is not None  # noqa: S101 - just stored
    return out


@router.get("/projects/{project_id}/plan", operation_id="getPlan")
def get_plan(project_id: int, svc: Svc) -> PlanOut | None:
    svc.projects.get(project_id)
    return _out(svc, project_id)


@router.put("/projects/{project_id}/plan", operation_id="editPlan")
def edit_plan(project_id: int, body: PlanEditIn, svc: Svc) -> PlanOut:
    """A tester edit: validated against the approved scope, stored as a new version."""
    ctx = approved_scope(svc, project_id)
    errors = validate_plan(body.plan, element_index(ctx.elements), {p["url"] for p in ctx.pages})
    if errors:
        raise ValidationError("; ".join(errors))
    store_plan(svc, project_id, body.plan, "user", f"{body.reason} ({body.actor})")
    out = _out(svc, project_id)
    assert out is not None  # noqa: S101
    return out
