"""Validation reports: which exact code versions were validated, and the outcome (T-013)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select

from gatp.store.db import Database
from gatp.store.models import ValidationReport


@dataclass(frozen=True)
class ReportDTO:
    id: int
    project_id: int
    version_ids: tuple[int, ...]
    ok: bool
    report: dict[str, Any]
    created_at: datetime


def _dto(r: ValidationReport) -> ReportDTO:
    return ReportDTO(
        r.id, r.project_id, tuple(sorted(r.version_ids)), r.ok, dict(r.report), r.created_at
    )


class ReportRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(
        self, project_id: int, version_ids: list[int], ok: bool, report: dict[str, Any]
    ) -> ReportDTO:
        with self.db.session() as s:
            row = ValidationReport(
                project_id=project_id, version_ids=sorted(version_ids), ok=ok, report=report
            )
            s.add(row)
            s.flush()
            return _dto(row)

    def latest(self, project_id: int) -> ReportDTO | None:
        with self.db.session() as s:
            row = s.scalar(
                select(ValidationReport)
                .where(ValidationReport.project_id == project_id)
                .order_by(ValidationReport.id.desc())
                .limit(1)
            )
            return None if row is None else _dto(row)

    def passing_for(self, project_id: int, version_id: int) -> bool:
        """True if some passing report covers this exact version id."""
        with self.db.session() as s:
            rows = s.scalars(
                select(ValidationReport).where(
                    ValidationReport.project_id == project_id, ValidationReport.ok.is_(True)
                )
            )
            return any(version_id in r.version_ids for r in rows)
