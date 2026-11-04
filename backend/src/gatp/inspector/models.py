"""Inspection output models (the InspectionSnapshot of the inspector LLD)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from gatp.inspector.locators import LocatorSpec


class LocatorCandidateOut(BaseModel):
    """A ranked candidate with its live evidence (ADR-006)."""

    rank: int
    spec: LocatorSpec
    expression: str
    count: int  # how many elements it matches on the live page
    targets_element: bool  # True if the single match is this element
    usable: bool  # count == 1 and targets_element
    positional: bool = False  # structural CSS path: unique now, brittle under change


class InspectedElement(BaseModel):
    key: str  # e1, e2, … stable within the snapshot
    tag: str
    role: str
    name: str
    text: str
    label: str
    attributes: dict[str, str]
    dom_path: str
    bbox: dict[str, int]
    visible: bool
    enabled: bool
    nearby_text: list[str]
    form: str
    index_in_form: int
    source_line: int | None  # line of the start tag in the served HTML, None if script-made
    locators: list[LocatorCandidateOut]
    default_locator: int | None  # best usable *non-positional* candidate (None = ask tester)
    # no_unique_locator | no_accessible_name | weak_accessible_name | no_visible_label |
    # hidden | disabled
    flags: list[str]
    fingerprint: dict[str, Any]


class InspectionScope(BaseModel):
    """CSS selectors of containers to include (empty = whole page) or exclude."""

    include: list[str] = []
    exclude: list[str] = []


class InspectionResult(BaseModel):
    url: str
    final_url: str
    title: str
    elements: list[InspectedElement]
    scope: InspectionScope
    html_sha256: str
