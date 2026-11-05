"""Rescans and their per-page change sets (T-016). Both are write-once evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select

from gatp.store.db import Database
from gatp.store.errors import NotFoundError
from gatp.store.models import ChangeSet, Rescan


@dataclass(frozen=True)
class ChangeSetDTO:
    id: int
    old_snapshot_id: int
    new_snapshot_id: int
    summary: dict[str, Any]


@dataclass(frozen=True)
class RescanDTO:
    id: int
    project_id: int
    summary: dict[str, Any]
    created_at: datetime
    change_sets: tuple[ChangeSetDTO, ...]


@dataclass(frozen=True)
class PageChange:
    """Input for one page: which snapshots were compared, and what was found."""

    old_snapshot_id: int
    new_snapshot_id: int
    summary: dict[str, Any]


class RescanRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, project_id: int, summary: dict[str, Any], pages: list[PageChange]) -> RescanDTO:
        with self.db.session() as s:
            rescan = Rescan(project_id=project_id, summary=summary)
            s.add(rescan)
            s.flush()
            for p in pages:
                s.add(
                    ChangeSet(
                        project_id=project_id,
                        rescan_id=rescan.id,
                        old_snapshot_id=p.old_snapshot_id,
                        new_snapshot_id=p.new_snapshot_id,
                        summary=p.summary,
                    )
                )
            s.flush()
            return self._dto(s, rescan)

    def get(self, rescan_id: int) -> RescanDTO:
        with self.db.session() as s:
            row = s.get(Rescan, rescan_id)
            if row is None:
                raise NotFoundError(f"rescan {rescan_id}")
            return self._dto(s, row)

    def latest(self, project_id: int) -> RescanDTO | None:
        with self.db.session() as s:
            row = s.scalar(
                select(Rescan)
                .where(Rescan.project_id == project_id)
                .order_by(Rescan.id.desc())
                .limit(1)
            )
            return None if row is None else self._dto(s, row)

    @staticmethod
    def _dto(s: Any, row: Rescan) -> RescanDTO:
        sets = s.scalars(
            select(ChangeSet).where(ChangeSet.rescan_id == row.id).order_by(ChangeSet.id)
        )
        return RescanDTO(
            id=row.id,
            project_id=row.project_id,
            summary=dict(row.summary),
            created_at=row.created_at,
            change_sets=tuple(
                ChangeSetDTO(c.id, c.old_snapshot_id, c.new_snapshot_id, dict(c.summary))
                for c in sets
            ),
        )
