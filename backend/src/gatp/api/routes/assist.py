"""Phase 1 grounded model call (T-010) and the model usage log."""

from __future__ import annotations

import json

from fastapi import APIRouter

from gatp.api.routes.deps import Svc
from gatp.api.schemas import InsightOut, LlmCallOut
from gatp.api.services import Services
from gatp.api.workflow import GateBlockedError, require_approval
from gatp.store.dto import SnapshotDTO
from gatp.store.errors import NotFoundError
from gatp.test_designer.insight import INSIGHT, Insight, request_insight, scoped_elements

router = APIRouter(prefix="/api", tags=["assist"])


def _approved_scope(
    svc: Services, project_id: int
) -> tuple[int, dict[str, object], dict[int, SnapshotDTO]]:
    artifact = svc.artifacts.find(project_id, "scope", "scope")
    if artifact is None:
        raise GateBlockedError("save and approve a scope (G0) first")
    version = svc.artifacts.latest(artifact.id)
    require_approval(svc, "G0", version)  # only approved scopes reach the model
    scope = json.loads(version.content)
    snapshots = {p["snapshot_id"]: svc.snapshots.get(p["snapshot_id"]) for p in scope["pages"]}
    return version.number, scope, snapshots


@router.post("/projects/{project_id}/insight", operation_id="requestInsight", status_code=201)
def create_insight(project_id: int, svc: Svc) -> InsightOut:
    """Summarise the approved scope and suggest next actions, grounded in the snapshots."""
    project = svc.projects.get(project_id)
    number, scope, snapshots = _approved_scope(svc, project_id)
    elements = scoped_elements(scope, snapshots)
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
        scope_version=number,
        element_ids_sent=[e.id for e in elements],
        browser_ms=sum(int(s.meta.get("browser_ms", 0)) for s in snapshots.values()),
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
        number, scope, snapshots = _approved_scope(svc, project_id)
    except (GateBlockedError, NotFoundError):
        number, scope, snapshots = 0, {"pages": []}, {}
    return InsightOut(
        insight=Insight.model_validate_json(call.response),
        call=LlmCallOut.model_validate(call),
        attempts=[LlmCallOut.model_validate(call)],
        scope_version=number,
        element_ids_sent=[e.id for e in scoped_elements(scope, snapshots)],
        browser_ms=sum(int(s.meta.get("browser_ms", 0)) for s in snapshots.values()),
    )


@router.get("/projects/{project_id}/llm-calls", operation_id="listLlmCalls")
def list_llm_calls(project_id: int, svc: Svc) -> list[LlmCallOut]:
    """Every model call attempt for the project, newest first (usage evidence)."""
    svc.projects.get(project_id)
    return [LlmCallOut.model_validate(c) for c in svc.llm_calls.recent(project_id)]
