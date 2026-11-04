"""Test plan endpoints: propose / revise with the model, edit, read (T-012, gate G1)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from gatp.api.context import approved_scope
from gatp.api.plan_service import current_plan, element_labels, plan_blockers, store_plan
from gatp.api.routes.deps import Svc
from gatp.api.run_service import failed_expectations
from gatp.api.schemas import ClarificationOut, LlmCallOut, VersionOut
from gatp.api.services import Services
from gatp.api.workflow import is_approved, require_no_open_clarifications
from gatp.store.errors import ValidationError
from gatp.store.runs import RunRepository
from gatp.test_designer.plan import TestPlan, element_index, propose_plan, validate_plan

router = APIRouter(prefix="/api", tags=["plan"])


class ProposeIn(BaseModel):
    feedback: str = Field(default="", max_length=5000, description="Revise the current plan")
    run_id: int | None = Field(default=None, description="Revise from this run's results (T-015)")
    test_ids: list[str] = Field(
        default_factory=list, description="Results to include (empty = every non-passed test)"
    )


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
    run_results = _run_results(svc, project_id, body.run_id, body.test_ids)
    revising = bool(body.feedback or run_results)
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
        current=existing[2] if existing and revising else None,
        feedback=body.feedback,
        run_results=run_results,
    )
    source = f" from run #{body.run_id}" if run_results else ""
    reason = f"revised by model{source}: {body.feedback}" if revising else "proposed by model"
    store_plan(svc, project_id, result.value, "model", f"{reason} (call #{result.call.id})")
    svc.events.publish(project_id, "model_call_finished", {"call_id": result.call.id})
    out = _out(svc, project_id, LlmCallOut.model_validate(result.call))
    assert out is not None  # noqa: S101 - just stored
    return out


def _run_results(
    svc: Services, project_id: int, run_id: int | None, test_ids: list[str]
) -> list[dict[str, Any]]:
    """Failures of an earlier run, as page data for a revision (messages are page text)."""
    if run_id is None:
        return []
    run = RunRepository(svc.db).get(run_id)
    if run.project_id != project_id:
        raise ValidationError(f"run {run_id} belongs to another project")
    chosen = [
        r for r in run.results if (r.test_id in test_ids if test_ids else r.outcome != "passed")
    ]
    return [
        {
            "test_id": r.test_id,
            "outcome": r.outcome,
            "message": r.message[:800],
            "failed_expectations": failed_expectations(r.trace_path),
        }
        for r in chosen
    ]


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
