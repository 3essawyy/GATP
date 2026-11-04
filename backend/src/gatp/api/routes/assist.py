"""Phase 1 grounded model call (T-010) and the model usage log."""

from __future__ import annotations

from fastapi import APIRouter

from gatp.api.context import ScopeContext, approved_scope
from gatp.api.routes.deps import Svc
from gatp.api.schemas import InsightOut, LlmCallOut
from gatp.api.workflow import GateBlockedError
from gatp.store.errors import NotFoundError
from gatp.test_designer.insight import INSIGHT, Insight, request_insight

router = APIRouter(prefix="/api", tags=["assist"])


@router.post("/projects/{project_id}/insight", operation_id="requestInsight", status_code=201)
def create_insight(project_id: int, svc: Svc) -> InsightOut:
    """Summarise the approved scope and suggest next actions, grounded in the snapshots."""
    project = svc.projects.get(project_id)
    ctx = approved_scope(svc, project_id)
    scope, elements = ctx.scope, ctx.elements
    if not elements:
        raise GateBlockedError("the approved scope contains no elements")
    svc.events.publish(project_id, "model_call_started", {"purpose": INSIGHT.id})
    result = request_insight(
        svc.llm,
        project_id=project_id,
        goal=str(scope.get("goal") or project.goal),
        notes=str(scope.get("notes") or ""),
        requirements=[r.text for r in svc.gates.requirements(project_id)],
        elements=elements,
    )
    svc.events.publish(project_id, "model_call_finished", {"call_id": result.call.id})
    return InsightOut(
        insight=result.value,
        call=LlmCallOut.model_validate(result.call),
        attempts=[LlmCallOut.model_validate(a) for a in result.attempts],
        scope_version=ctx.version_number,
        element_ids_sent=[e.id for e in elements],
        browser_ms=ctx.browser_ms,
    )


@router.get("/projects/{project_id}/insight", operation_id="latestInsight")
def latest_insight(project_id: int, svc: Svc) -> InsightOut | None:
    """The most recent successful insight call, or ``null``."""
    svc.projects.get(project_id)
    call = next(
        (
            c
            for c in svc.llm_calls.recent(project_id)
            if c.purpose == INSIGHT.id and c.status == "ok"
        ),
        None,
    )
    if call is None:
        return None
    try:
        ctx: ScopeContext | None = approved_scope(svc, project_id)
    except (GateBlockedError, NotFoundError):
        ctx = None
    return InsightOut(
        insight=Insight.model_validate_json(call.response),
        call=LlmCallOut.model_validate(call),
        attempts=[LlmCallOut.model_validate(call)],
        scope_version=ctx.version_number if ctx else 0,
        element_ids_sent=[e.id for e in ctx.elements] if ctx else [],
        browser_ms=ctx.browser_ms if ctx else 0,
    )


@router.get("/projects/{project_id}/llm-calls", operation_id="listLlmCalls")
def list_llm_calls(project_id: int, svc: Svc) -> list[LlmCallOut]:
    """Every model call attempt for the project, newest first (usage evidence)."""
    svc.projects.get(project_id)
    return [LlmCallOut.model_validate(c) for c in svc.llm_calls.recent(project_id)]
