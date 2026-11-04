"""SQLAlchemy ORM models: the HLD §7 data model (ADR-005, ADR-015).

Conventions:
- Every table has an integer ``id`` primary key and a UTC ``created_at``.
- JSON columns hold small structured data (attributes, evidence); large blobs go to ``artifacts/``.
- Immutable rows (snapshots, elements, locator candidates, artifact versions) are protected by
  ORM guards in ``gatp.store.immutability`` and by SQLite triggers in the initial migration.

Only the store package imports this module; other modules use the repositories and DTOs.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, ClassVar

from sqlalchemy import JSON, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    """'Now' in UTC as a naive datetime (SQLite has no timezone type; all times are UTC)."""
    return datetime.now(UTC).replace(tzinfo=None)


class Base(DeclarativeBase):
    """Declarative base with a JSON type mapping for ``dict``/``list`` annotations."""

    type_annotation_map: ClassVar[dict[Any, Any]] = {dict[str, Any]: JSON, list[Any]: JSON}


class Project(Base):
    """A testing project: one approved target origin (the runner allowlist), many pages."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    origin: Mapped[str] = mapped_column(String(500))
    goal: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    pages: Mapped[list[Page]] = relationship(back_populates="project", order_by="Page.id")


class Page(Base):
    """A URL inside a project that the tester chose to inspect."""

    __tablename__ = "pages"
    __table_args__ = (UniqueConstraint("project_id", "url"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    url: Mapped[str] = mapped_column(String(2000))
    name: Mapped[str] = mapped_column(String(200), default="")
    setup: Mapped[list[Any]] = mapped_column(default=list, server_default="[]")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    project: Mapped[Project] = relationship(back_populates="pages")


class InspectionSnapshot(Base):
    """Immutable result of one inspection of a page. A rescan creates a new snapshot."""

    __tablename__ = "inspection_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("pages.id"), index=True)
    url: Mapped[str] = mapped_column(String(2000))
    title: Mapped[str] = mapped_column(String(500), default="")
    screenshot_path: Mapped[str] = mapped_column(String(500), default="")
    html_path: Mapped[str] = mapped_column(String(500), default="")
    html_sha256: Mapped[str] = mapped_column(String(64), default="")
    meta: Mapped[dict[str, Any]] = mapped_column(default=dict)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    elements: Mapped[list[Element]] = relationship(
        back_populates="snapshot", order_by="Element.id", cascade="all"
    )


class Element(Base):
    """One interactive or significant element observed in a snapshot (immutable)."""

    __tablename__ = "elements"
    __table_args__ = (UniqueConstraint("snapshot_id", "key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("inspection_snapshots.id"), index=True)
    key: Mapped[str] = mapped_column(String(40))  # stable within the snapshot, e.g. "e7"
    tag: Mapped[str] = mapped_column(String(40))
    role: Mapped[str] = mapped_column(String(60), default="")
    name: Mapped[str] = mapped_column(String(500), default="")
    text: Mapped[str] = mapped_column(Text, default="")
    attributes: Mapped[dict[str, Any]] = mapped_column(default=dict)
    bbox: Mapped[dict[str, Any]] = mapped_column(default=dict)
    fingerprint: Mapped[dict[str, Any]] = mapped_column(default=dict)
    source_line: Mapped[int | None] = mapped_column(default=None)
    # label, dom_path, visible, enabled, nearby_text, form, index_in_form, flags, default_locator
    details: Mapped[dict[str, Any]] = mapped_column(default=dict, server_default="{}")

    snapshot: Mapped[InspectionSnapshot] = relationship(back_populates="elements")
    locators: Mapped[list[LocatorCandidate]] = relationship(
        back_populates="element", order_by="LocatorCandidate.rank", cascade="all"
    )


class LocatorCandidate(Base):
    """A ranked locator for an element with its live match count (ADR-006; immutable)."""

    __tablename__ = "locator_candidates"

    id: Mapped[int] = mapped_column(primary_key=True)
    element_id: Mapped[int] = mapped_column(ForeignKey("elements.id"), index=True)
    rank: Mapped[int]
    strategy: Mapped[str] = mapped_column(String(40))  # role | label | test_id | placeholder | ...
    expression: Mapped[str] = mapped_column(Text)  # Playwright Python expression
    match_count: Mapped[int]
    spec: Mapped[dict[str, Any]] = mapped_column(default=dict, server_default="{}")  # LocatorSpec
    targets_element: Mapped[bool] = mapped_column(default=False, server_default="0")

    element: Mapped[Element] = relationship(back_populates="locators")


class Requirement(Base):
    """Free-text requirement or note from the tester (observations vs. stated behavior)."""

    __tablename__ = "requirements"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class Artifact(Base):
    """A versioned thing: test plan, test case, page object or test file (ADR-005)."""

    __tablename__ = "artifacts"
    __table_args__ = (UniqueConstraint("project_id", "kind", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    kind: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    versions: Mapped[list[ArtifactVersion]] = relationship(
        back_populates="artifact", order_by="ArtifactVersion.number"
    )


class ArtifactVersion(Base):
    """Immutable version N of an artifact. Every change (incl. restore) appends a new row."""

    __tablename__ = "artifact_versions"
    __table_args__ = (UniqueConstraint("artifact_id", "number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    artifact_id: Mapped[int] = mapped_column(ForeignKey("artifacts.id"), index=True)
    number: Mapped[int]
    content: Mapped[str] = mapped_column(Text)
    content_sha256: Mapped[str] = mapped_column(String(64))
    author: Mapped[str] = mapped_column(String(20))  # user | model | repair | restore
    reason: Mapped[str] = mapped_column(Text, default="")
    parent_number: Mapped[int | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)

    artifact: Mapped[Artifact] = relationship(back_populates="versions")


class Approval(Base):
    """A human approval at a gate (G0-G5), bound to the exact version(s) it covers."""

    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    gate: Mapped[str] = mapped_column(String(4))
    artifact_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("artifact_versions.id"), default=None
    )
    subject: Mapped[dict[str, Any]] = mapped_column(default=dict)  # e.g. run scope, version ids
    actor: Mapped[str] = mapped_column(String(100))
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class Clarification(Base):
    """A question GATP must not answer itself; blocks the step that raised it (HLD §4)."""

    __tablename__ = "clarifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    step: Mapped[str] = mapped_column(String(40))
    kind: Mapped[str] = mapped_column(String(40))
    question: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict[str, Any]] = mapped_column(default=dict)
    options: Mapped[list[Any]] = mapped_column(default=list)
    status: Mapped[str] = mapped_column(String(20), default="open")  # open | answered
    answer: Mapped[str] = mapped_column(Text, default="")
    answered_by: Mapped[str] = mapped_column(String(100), default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    answered_at: Mapped[datetime | None] = mapped_column(default=None)


class Run(Base):
    """One approved execution of a set of tests."""

    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    approval_id: Mapped[int | None] = mapped_column(ForeignKey("approvals.id"), default=None)
    status: Mapped[str] = mapped_column(String(20), default="queued")
    target_url: Mapped[str] = mapped_column(String(2000), default="")
    scope: Mapped[dict[str, Any]] = mapped_column(default=dict)  # artifact version ids, tests
    duration_ms: Mapped[int | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(default=None)

    results: Mapped[list[RunResult]] = relationship(back_populates="run", order_by="RunResult.id")


class RunResult(Base):
    """Outcome of one test in a run."""

    __tablename__ = "run_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), index=True)
    test_id: Mapped[str] = mapped_column(String(300))
    outcome: Mapped[str] = mapped_column(String(20))  # passed | failed | error | skipped
    duration_ms: Mapped[int] = mapped_column(default=0)
    message: Mapped[str] = mapped_column(Text, default="")
    screenshot_path: Mapped[str] = mapped_column(String(500), default="")
    trace_path: Mapped[str] = mapped_column(String(500), default="")

    run: Mapped[Run] = relationship(back_populates="results")


class ChangeSet(Base):
    """Comparison of an old and a new snapshot of the same page (maintenance)."""

    __tablename__ = "change_sets"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    old_snapshot_id: Mapped[int] = mapped_column(ForeignKey("inspection_snapshots.id"))
    new_snapshot_id: Mapped[int] = mapped_column(ForeignKey("inspection_snapshots.id"))
    summary: Mapped[dict[str, Any]] = mapped_column(default=dict)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class RepairProposal(Base):
    """An evidence-backed proposal to update a locator, or a reason it needs clarification."""

    __tablename__ = "repair_proposals"

    id: Mapped[int] = mapped_column(primary_key=True)
    change_set_id: Mapped[int] = mapped_column(ForeignKey("change_sets.id"), index=True)
    old_element_id: Mapped[int] = mapped_column(ForeignKey("elements.id"))
    new_element_id: Mapped[int | None] = mapped_column(ForeignKey("elements.id"), default=None)
    score: Mapped[float] = mapped_column(default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="proposed")
    evidence: Mapped[dict[str, Any]] = mapped_column(default=dict)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class LlmCall(Base):
    """Usage log for every model call (HLD §10, REQ-Q8-Q10)."""

    __tablename__ = "llm_calls"
    __table_args__ = (Index("ix_llm_calls_request_hash", "request_hash"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), default=None)
    purpose: Mapped[str] = mapped_column(String(60))  # prompt template id
    template_version: Mapped[int] = mapped_column(default=1, server_default="1")
    provider: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(100))
    model_version: Mapped[str] = mapped_column(String(100), default="")
    request_hash: Mapped[str] = mapped_column(String(64))
    input_tokens: Mapped[int] = mapped_column(default=0)
    output_tokens: Mapped[int] = mapped_column(default=0)
    tokens_estimated: Mapped[bool] = mapped_column(default=False)
    latency_ms: Mapped[int] = mapped_column(default=0)
    cache: Mapped[str] = mapped_column(String(10), default="fresh")  # fresh | reused
    status: Mapped[str] = mapped_column(String(20), default="ok")
    error: Mapped[str] = mapped_column(Text, default="")
    response: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


IMMUTABLE_TABLES = ("inspection_snapshots", "elements", "locator_candidates", "artifact_versions")
