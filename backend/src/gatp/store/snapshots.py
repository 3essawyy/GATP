"""Inspection snapshots repository (immutable; a rescan creates a new snapshot)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from gatp.store.db import Database
from gatp.store.dto import ElementDTO, LocatorDTO, SnapshotDTO, SnapshotIn
from gatp.store.errors import NotFoundError, ValidationError
from gatp.store.models import Element, InspectionSnapshot, LocatorCandidate, Page


def _to_dto(snap: InspectionSnapshot) -> SnapshotDTO:
    return SnapshotDTO(
        id=snap.id,
        page_id=snap.page_id,
        url=snap.url,
        title=snap.title,
        screenshot_path=snap.screenshot_path,
        html_path=snap.html_path,
        html_sha256=snap.html_sha256,
        meta=dict(snap.meta),
        created_at=snap.created_at,
        elements=tuple(
            ElementDTO(
                id=e.id,
                key=e.key,
                tag=e.tag,
                role=e.role,
                name=e.name,
                text=e.text,
                attributes=dict(e.attributes),
                bbox=dict(e.bbox),
                fingerprint=dict(e.fingerprint),
                source_line=e.source_line,
                locators=tuple(
                    LocatorDTO(c.id, c.rank, c.strategy, c.expression, c.match_count)
                    for c in e.locators
                ),
            )
            for e in snap.elements
        ),
    )


class SnapshotRepository:
    """Persist and read inspection snapshots with their elements and locators."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def save(self, data: SnapshotIn) -> SnapshotDTO:
        """Store a snapshot atomically. Element keys must be unique within the snapshot."""
        keys = [e.key for e in data.elements]
        if len(keys) != len(set(keys)):
            raise ValidationError("element keys must be unique within a snapshot")
        with self.db.session() as s:
            if s.get(Page, data.page_id) is None:
                raise NotFoundError(f"page {data.page_id}")
            snap = InspectionSnapshot(
                page_id=data.page_id,
                url=data.url,
                title=data.title,
                screenshot_path=data.screenshot_path,
                html_path=data.html_path,
                html_sha256=data.html_sha256,
                meta=dict(data.meta),
            )
            for e in data.elements:
                element = Element(
                    key=e.key,
                    tag=e.tag,
                    role=e.role,
                    name=e.name,
                    text=e.text,
                    attributes=dict(e.attributes),
                    bbox=dict(e.bbox),
                    fingerprint=dict(e.fingerprint),
                    source_line=e.source_line,
                )
                element.locators = [
                    LocatorCandidate(
                        rank=c.rank,
                        strategy=c.strategy,
                        expression=c.expression,
                        match_count=c.match_count,
                    )
                    for c in e.locators
                ]
                snap.elements.append(element)
            s.add(snap)
            s.flush()
            snap_id = snap.id
        return self.get(snap_id)

    def get(self, snapshot_id: int) -> SnapshotDTO:
        with self.db.session() as s:
            snap = s.scalar(
                select(InspectionSnapshot)
                .where(InspectionSnapshot.id == snapshot_id)
                .options(selectinload(InspectionSnapshot.elements).selectinload(Element.locators))
            )
            if snap is None:
                raise NotFoundError(f"snapshot {snapshot_id}")
            return _to_dto(snap)

    def latest_for_page(self, page_id: int) -> SnapshotDTO | None:
        """The newest snapshot of a page, or None if it was never inspected."""
        with self.db.session() as s:
            snap_id = s.scalar(
                select(InspectionSnapshot.id)
                .where(InspectionSnapshot.page_id == page_id)
                .order_by(InspectionSnapshot.id.desc())
                .limit(1)
            )
        return None if snap_id is None else self.get(snap_id)

    def list_for_page(self, page_id: int) -> list[int]:
        """Snapshot ids of a page, oldest first."""
        with self.db.session() as s:
            return list(
                s.scalars(
                    select(InspectionSnapshot.id)
                    .where(InspectionSnapshot.page_id == page_id)
                    .order_by(InspectionSnapshot.id)
                )
            )
