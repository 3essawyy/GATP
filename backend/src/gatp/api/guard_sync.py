"""Keep "weakening" clarifications in sync with the guard's findings (T-015, ADR-023).

One open clarification per finding (keyed by the finding's ``key``). Findings that disappear
(the change was undone, or a newer version was approved) are resolved as superseded. A finding
the tester already accepted is not asked again.
"""

from __future__ import annotations

from typing import Any

from gatp.api.services import Services
from gatp.store.dto import VersionDTO

KIND = "weakening"
ACCEPT = "Accept this change"
RESTORE = "Restore the approved version"


def sync_weakenings(
    svc: Services, project_id: int, step: str, findings: dict[str, tuple[str, dict[str, Any]]]
) -> None:
    """``findings``: key -> (question, evidence). Raises/supersedes clarifications on ``step``."""
    existing = [c for c in svc.gates.clarifications(project_id, step=step) if c.kind == KIND]
    open_ = {c.evidence.get("key"): c for c in existing if c.status == "open"}
    accepted = {
        c.evidence.get("key") for c in existing if c.status == "answered" and c.answer == ACCEPT
    }
    for key, clar in open_.items():
        if key not in findings:
            svc.gates.resolve(clar.id, "superseded", "the change was undone or re-approved")
    for key, (question, evidence) in findings.items():
        if key in open_ or key in accepted:
            continue
        svc.gates.raise_clarification(
            project_id, step, KIND, question, evidence={**evidence, "key": key},
            options=[ACCEPT, RESTORE],
        )  # fmt: skip


def approved_baseline(svc: Services, artifact_id: int, gate: str) -> VersionDTO | None:
    """The newest version of ``artifact_id`` approved for ``gate`` (or None)."""
    for version in reversed(svc.artifacts.history(artifact_id)):
        if svc.gates.approvals_for_version(gate, version.id):
            return version
    return None
