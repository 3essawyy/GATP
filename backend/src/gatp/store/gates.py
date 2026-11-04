"""Approvals, clarifications and requirements (HLD §4: gates G0-G5 and clarification requests).

Approvals are bound to the **exact** artifact version they cover (or to a subject such as a
run scope). Because versions are immutable and every edit creates a new version, an edit
automatically leaves the new latest version without approval.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select

from gatp.store.db import Database
from gatp.store.errors import NotFoundError, ValidationError
from gatp.store.models import Approval, Clarification, Project, Requirement, utcnow

GATES: dict[str, str] = {
    "G0": "Scope: inspection results may be used for test design",
    "G1": "Plan: test cases may be turned into code",
    "G2": "Code: generated code may be executed (on request)",
    "G3": "Execution: these exact tests may run against this target",
    "G4": "Repair: this maintenance change may be applied",
    "G5": "Restore: this older version may become the latest",
}


@dataclass(frozen=True)
class ApprovalDTO:
    id: int
    project_id: int
    gate: str
    artifact_version_id: int | None
    subject: dict[str, Any]
    actor: str
    comment: str
    created_at: datetime


@dataclass(frozen=True)
class ClarificationDTO:
    id: int
    project_id: int
    step: str
    kind: str
    question: str
    evidence: dict[str, Any]
    options: list[Any]
    status: str
    answer: str
    answered_by: str
    created_at: datetime
    answered_at: datetime | None


@dataclass(frozen=True)
class RequirementDTO:
    id: int
    project_id: int
    text: str
    created_at: datetime


def _approval(a: Approval) -> ApprovalDTO:
    return ApprovalDTO(
        a.id,
        a.project_id,
        a.gate,
        a.artifact_version_id,
        dict(a.subject),
        a.actor,
        a.comment,
        a.created_at,
    )


def _clar(c: Clarification) -> ClarificationDTO:
    return ClarificationDTO(
        id=c.id,
        project_id=c.project_id,
        step=c.step,
        kind=c.kind,
        question=c.question,
        evidence=dict(c.evidence),
        options=list(c.options),
        status=c.status,
        answer=c.answer,
        answered_by=c.answered_by,
        created_at=c.created_at,
        answered_at=c.answered_at,
    )


class GateRepository:
    """Persistence for approvals, clarifications and requirements."""

    def __init__(self, db: Database) -> None:
        self.db = db

    # -- approvals ---------------------------------------------------------------------
    def approve(
        self,
        project_id: int,
        gate: str,
        actor: str,
        *,
        artifact_version_id: int | None = None,
        subject: dict[str, Any] | None = None,
        comment: str = "",
    ) -> ApprovalDTO:
        if gate not in GATES:
            raise ValidationError(f"unknown gate {gate!r}")
        if not actor.strip():
            raise ValidationError("an approval needs the approver's name")
        with self.db.session() as s:
            if s.get(Project, project_id) is None:
                raise NotFoundError(f"project {project_id}")
            row = Approval(
                project_id=project_id,
                gate=gate,
                artifact_version_id=artifact_version_id,
                subject=dict(subject or {}),
                actor=actor.strip(),
                comment=comment,
            )
            s.add(row)
            s.flush()
            return _approval(row)

    def approvals_for_version(self, gate: str, artifact_version_id: int) -> list[ApprovalDTO]:
        with self.db.session() as s:
            rows = s.scalars(
                select(Approval).where(
                    Approval.gate == gate, Approval.artifact_version_id == artifact_version_id
                )
            )
            return [_approval(a) for a in rows]

    def get_approval(self, approval_id: int) -> ApprovalDTO:
        with self.db.session() as s:
            a = s.get(Approval, approval_id)
            if a is None:
                raise NotFoundError(f"approval {approval_id}")
            return _approval(a)

    def approvals(self, project_id: int) -> list[ApprovalDTO]:
        with self.db.session() as s:
            rows = s.scalars(
                select(Approval).where(Approval.project_id == project_id).order_by(Approval.id)
            )
            return [_approval(a) for a in rows]

    # -- clarifications ----------------------------------------------------------------
    def raise_clarification(
        self,
        project_id: int,
        step: str,
        kind: str,
        question: str,
        *,
        evidence: dict[str, Any] | None = None,
        options: list[Any] | None = None,
    ) -> ClarificationDTO:
        with self.db.session() as s:
            if s.get(Project, project_id) is None:
                raise NotFoundError(f"project {project_id}")
            row = Clarification(
                project_id=project_id,
                step=step,
                kind=kind,
                question=question,
                evidence=dict(evidence or {}),
                options=list(options or []),
            )
            s.add(row)
            s.flush()
            return _clar(row)

    def answer(self, clarification_id: int, answer: str, actor: str) -> ClarificationDTO:
        if not answer.strip() or not actor.strip():
            raise ValidationError("an answer and the tester's name are required")
        with self.db.session() as s:
            row = s.get(Clarification, clarification_id)
            if row is None:
                raise NotFoundError(f"clarification {clarification_id}")
            if row.status != "open":
                raise ValidationError("clarification already answered")
            row.status = "answered"
            row.answer = answer.strip()
            row.answered_by = actor.strip()
            row.answered_at = utcnow()
            s.flush()
            return _clar(row)

    def resolve(self, clarification_id: int, status: str, note: str) -> ClarificationDTO:
        """Close an open clarification without a tester answer (e.g. ``superseded`` by an edit)."""
        with self.db.session() as s:
            row = s.get(Clarification, clarification_id)
            if row is None:
                raise NotFoundError(f"clarification {clarification_id}")
            if row.status == "open":
                row.status = status
                row.answer = note
                row.answered_by = "GATP"
                row.answered_at = utcnow()
            s.flush()
            return _clar(row)

    def get_clarification(self, clarification_id: int) -> ClarificationDTO:
        with self.db.session() as s:
            row = s.get(Clarification, clarification_id)
            if row is None:
                raise NotFoundError(f"clarification {clarification_id}")
            return _clar(row)

    def clarifications(
        self, project_id: int, *, step: str | None = None, status: str | None = None
    ) -> list[ClarificationDTO]:
        with self.db.session() as s:
            q = select(Clarification).where(Clarification.project_id == project_id)
            if step is not None:
                q = q.where(Clarification.step == step)
            if status is not None:
                q = q.where(Clarification.status == status)
            return [_clar(c) for c in s.scalars(q.order_by(Clarification.id))]

    # -- requirements ------------------------------------------------------------------
    def add_requirement(self, project_id: int, text: str) -> RequirementDTO:
        if not text.strip():
            raise ValidationError("requirement text is empty")
        with self.db.session() as s:
            if s.get(Project, project_id) is None:
                raise NotFoundError(f"project {project_id}")
            row = Requirement(project_id=project_id, text=text.strip())
            s.add(row)
            s.flush()
            return RequirementDTO(row.id, row.project_id, row.text, row.created_at)

    def requirements(self, project_id: int) -> list[RequirementDTO]:
        with self.db.session() as s:
            rows = s.scalars(
                select(Requirement)
                .where(Requirement.project_id == project_id)
                .order_by(Requirement.id)
            )
            return [RequirementDTO(r.id, r.project_id, r.text, r.created_at) for r in rows]
