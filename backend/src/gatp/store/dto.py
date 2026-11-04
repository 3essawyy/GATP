"""Plain, immutable data objects returned by the store's repositories.

Callers never receive ORM objects, so no database session leaks out of the store package.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

Author = Literal["user", "model", "repair", "restore"]
ArtifactKind = Literal["scope", "test_plan", "test_case", "page_object", "test_file"]
AUTHORS: tuple[str, ...] = ("user", "model", "repair", "restore")
ARTIFACT_KINDS: tuple[str, ...] = ("scope", "test_plan", "test_case", "page_object", "test_file")


@dataclass(frozen=True)
class ProjectDTO:
    id: int
    name: str
    origin: str
    goal: str
    created_at: datetime


@dataclass(frozen=True)
class PageDTO:
    id: int
    project_id: int
    url: str
    name: str
    created_at: datetime
    setup: tuple[dict[str, Any], ...] = ()  # tester-approved setup steps (ADR-018)


@dataclass(frozen=True)
class LocatorIn:
    """A ranked locator candidate as produced by the inspector."""

    rank: int
    strategy: str
    expression: str
    match_count: int
    spec: dict[str, Any] = field(default_factory=dict)
    targets_element: bool = False


@dataclass(frozen=True)
class ElementIn:
    """An observed element as produced by the inspector."""

    key: str
    tag: str
    role: str = ""
    name: str = ""
    text: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)
    bbox: dict[str, Any] = field(default_factory=dict)
    fingerprint: dict[str, Any] = field(default_factory=dict)
    source_line: int | None = None
    details: dict[str, Any] = field(default_factory=dict)
    locators: tuple[LocatorIn, ...] = ()


@dataclass(frozen=True)
class SnapshotIn:
    """A complete inspection result to persist."""

    page_id: int
    url: str
    title: str
    elements: tuple[ElementIn, ...]
    screenshot_path: str = ""
    html_path: str = ""
    html_sha256: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LocatorDTO:
    id: int
    rank: int
    strategy: str
    expression: str
    match_count: int
    spec: dict[str, Any]
    targets_element: bool

    @property
    def unique(self) -> bool:
        """Usable only if it matches exactly one element, and that element (ADR-006)."""
        return self.match_count == 1 and self.targets_element


@dataclass(frozen=True)
class ElementDTO:
    id: int
    key: str
    tag: str
    role: str
    name: str
    text: str
    attributes: dict[str, Any]
    bbox: dict[str, Any]
    fingerprint: dict[str, Any]
    source_line: int | None
    details: dict[str, Any]
    locators: tuple[LocatorDTO, ...]


@dataclass(frozen=True)
class SnapshotDTO:
    id: int
    page_id: int
    url: str
    title: str
    screenshot_path: str
    html_path: str
    html_sha256: str
    meta: dict[str, Any]
    created_at: datetime
    elements: tuple[ElementDTO, ...]


@dataclass(frozen=True)
class ArtifactDTO:
    id: int
    project_id: int
    kind: str
    name: str
    created_at: datetime


@dataclass(frozen=True)
class VersionDTO:
    id: int
    artifact_id: int
    number: int
    content: str
    content_sha256: str
    author: str
    reason: str
    parent_number: int | None
    created_at: datetime


@dataclass(frozen=True)
class DiffRow:
    """One side-by-side row. ``tag`` is equal | replace | delete | insert."""

    tag: str
    left_no: int | None
    left: str
    right_no: int | None
    right: str


@dataclass(frozen=True)
class VersionDiff:
    artifact_id: int
    from_number: int
    to_number: int
    unified: str
    rows: tuple[DiffRow, ...]
