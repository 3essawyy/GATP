"""Approval gates, clarification blocking and the computed workflow state (HLD §4).

The state of each step is *derived* from stored facts (artifacts, versions, approvals,
clarifications), never stored separately, so it cannot drift out of sync.
"""

from __future__ import annotations

from dataclasses import dataclass

from gatp.api.services import Services
from gatp.store.dto import VersionDTO
from gatp.store.reports import ReportRepository
from gatp.test_designer.plan import TestPlan, unconfirmed_assumptions

# Which artifact kinds each version-bound gate covers, and the workflow step it unlocks.
GATE_KINDS: dict[str, tuple[str, ...]] = {
    "G0": ("scope",),
    "G1": ("test_plan",),
    "G2": ("page_object", "test_file"),
}
GATE_STEP = {
    "G0": "scope",
    "G1": "plan",
    "G2": "code",
    "G3": "run",
    "G4": "maintain",
    "G5": "history",
}


class GateBlockedError(Exception):
    """An action needs an approval (or an answered clarification) it does not have."""


@dataclass(frozen=True)
class StepState:
    step: str
    gate: str | None
    status: str  # todo | needs_approval | approved | blocked
    detail: str
    open_clarifications: int


def is_approved(services: Services, gate: str, version: VersionDTO) -> bool:
    return bool(services.gates.approvals_for_version(gate, version.id))


def require_approval(services: Services, gate: str, version: VersionDTO) -> None:
    """Raise unless this exact version carries an approval for ``gate``."""
    if not is_approved(services, gate, version):
        raise GateBlockedError(
            f"{gate} approval required for artifact {version.artifact_id} v{version.number}"
        )


def require_no_open_clarifications(services: Services, project_id: int, step: str) -> None:
    open_ = services.gates.clarifications(project_id, step=step, status="open")
    if open_:
        ids = ", ".join(str(c.id) for c in open_)
        raise GateBlockedError(f"step '{step}' is blocked by open clarification(s): {ids}")


def check_approvable(services: Services, project_id: int, gate: str, version: VersionDTO) -> None:
    """Rules for approving a version: right kind, same project, latest version, no open CQs."""
    artifact = services.artifacts.get_artifact(version.artifact_id)
    if artifact.project_id != project_id:
        raise GateBlockedError("artifact belongs to another project")
    if gate in GATE_KINDS and artifact.kind not in GATE_KINDS[gate]:
        raise GateBlockedError(f"{gate} cannot approve a {artifact.kind}")
    if gate != "G5" and services.artifacts.latest(artifact.id).id != version.id:
        raise GateBlockedError("only the latest version can be approved; it changed since")
    require_no_open_clarifications(services, project_id, GATE_STEP[gate])
    if gate == "G2" and not ReportRepository(services.db).passing_for(project_id, version.id):
        raise GateBlockedError("validate the code first: G2 needs a passing validation report")
    if gate == "G1":
        pending = unconfirmed_assumptions(TestPlan.model_validate_json(version.content))
        if pending:
            ids = ", ".join(e.id for e in pending)
            raise GateBlockedError(f"confirm or remove assumption-based expectations first: {ids}")


def _gate_step(services: Services, project_id: int, step: str, gate: str) -> StepState:
    open_count = len(services.gates.clarifications(project_id, step=step, status="open"))
    artifacts = [
        a for kind in GATE_KINDS[gate] for a in services.artifacts.list_artifacts(project_id, kind)
    ]
    if open_count:
        return StepState(step, gate, "blocked", "open clarification(s)", open_count)
    if not artifacts:
        return StepState(step, gate, "todo", "nothing proposed yet", 0)
    latest = [v for v in (services.artifacts.latest(a.id) for a in artifacts) if v.content]
    if not latest:
        return StepState(step, gate, "todo", "nothing proposed yet", 0)
    pending = [v for v in latest if not is_approved(services, gate, v)]
    if pending:
        names = ", ".join(f"#{v.artifact_id} v{v.number}" for v in pending)
        if len(pending) > 2:
            names = f"{len(pending)} versions"
        return StepState(step, gate, "needs_approval", f"awaiting {gate}: {names}", 0)
    return StepState(step, gate, "approved", f"{len(latest)} version(s) approved", 0)


def workflow_state(services: Services, project_id: int) -> list[StepState]:
    """Status of every workflow step for the UI's step navigation."""
    pages = services.projects.pages(project_id)
    inspected = sum(1 for p in pages if services.snapshots.latest_for_page(p.id) is not None)
    inspect_open = len(services.gates.clarifications(project_id, step="inspect", status="open"))
    if inspect_open:
        inspect = StepState("inspect", None, "blocked", "open clarification(s)", inspect_open)
    elif inspected:
        inspect = StepState("inspect", None, "approved", f"{inspected} page(s) inspected", 0)
    else:
        inspect = StepState("inspect", None, "todo", "no page inspected yet", 0)
    return [
        inspect,
        _gate_step(services, project_id, "scope", "G0"),
        _gate_step(services, project_id, "plan", "G1"),
        _gate_step(services, project_id, "code", "G2"),
    ]
