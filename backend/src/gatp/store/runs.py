"""Test runs and their per-test results (T-014). Execution time is stored separately from
model time (REQ-Q8)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from gatp.store.db import Database
from gatp.store.errors import NotFoundError, ValidationError
from gatp.store.models import Run, RunResult, utcnow


@dataclass(frozen=True)
class RunResultDTO:
    id: int
    test_id: str
    outcome: str
    duration_ms: int
    message: str
    screenshot_path: str
    trace_path: str  # stack excerpt is stored here as text (no Playwright trace yet)


@dataclass(frozen=True)
class RunDTO:
    id: int
    project_id: int
    approval_id: int | None
    status: str
    target_url: str
    scope: dict[str, Any]
    duration_ms: int | None
    created_at: datetime
    finished_at: datetime | None
    results: tuple[RunResultDTO, ...]


def _dto(r: Run) -> RunDTO:
    return RunDTO(
        id=r.id,
        project_id=r.project_id,
        approval_id=r.approval_id,
        status=r.status,
        target_url=r.target_url,
        scope=dict(r.scope),
        duration_ms=r.duration_ms,
        created_at=r.created_at,
        finished_at=r.finished_at,
        results=tuple(
            RunResultDTO(
                x.id,
                x.test_id,
                x.outcome,
                x.duration_ms,
                x.message,
                x.screenshot_path,
                x.trace_path,
            )
            for x in r.results
        ),
    )


class RunRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def start(
        self, project_id: int, approval_id: int, target_url: str, scope: dict[str, Any]
    ) -> RunDTO:
        """Create a run for a G3 approval. Each approval authorises exactly one run."""
        with self.db.session() as s:
            used = s.scalar(select(Run.id).where(Run.approval_id == approval_id))
            if used is not None:
                raise ValidationError(f"approval {approval_id} was already used by run {used}")
            run = Run(
                project_id=project_id,
                approval_id=approval_id,
                status="running",
                target_url=target_url,
                scope=dict(scope),
            )
            s.add(run)
            s.flush()
            run_id = run.id
        return self.get(run_id)

    def finish(
        self,
        run_id: int,
        status: str,
        duration_ms: int,
        results: list[dict[str, Any]],
        extra: dict[str, Any],
    ) -> RunDTO:
        with self.db.session() as s:
            run = s.get(Run, run_id)
            if run is None:
                raise NotFoundError(f"run {run_id}")
            run.status = status
            run.duration_ms = duration_ms
            run.finished_at = utcnow()
            run.scope = {**run.scope, **extra}
            for r in results:
                run.results.append(
                    RunResult(
                        test_id=r["test_id"],
                        outcome=r["outcome"],
                        duration_ms=int(r.get("duration_ms", 0)),
                        message=str(r.get("message", ""))[:4000],
                        screenshot_path=(r.get("screenshots") or [""])[-1],
                        trace_path=str(r.get("details", ""))[:8000],
                    )
                )
            s.flush()
        return self.get(run_id)

    def get(self, run_id: int) -> RunDTO:
        with self.db.session() as s:
            run = s.scalar(select(Run).where(Run.id == run_id).options(selectinload(Run.results)))
            if run is None:
                raise NotFoundError(f"run {run_id}")
            return _dto(run)

    def for_project(self, project_id: int) -> list[RunDTO]:
        with self.db.session() as s:
            rows = s.scalars(
                select(Run)
                .where(Run.project_id == project_id)
                .order_by(Run.id.desc())
                .options(selectinload(Run.results))
            )
            return [_dto(r) for r in rows]
