"""Request/response models. They define the OpenAPI schema the TS client is generated from."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from gatp.inspector.models import InspectionScope
from gatp.runner.jobs import SetupStep
from gatp.test_designer.insight import Insight


class Health(BaseModel):
    """Liveness information for the API process."""

    status: Literal["ok"]
    app: str
    version: str


class RunnerHealth(BaseModel):
    available: bool
    headless: bool | None = None
    detail: str = ""


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# -- projects and pages -----------------------------------------------------------------
class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    url: str = Field(description="Any URL of the target site; its origin becomes the allowlist")


class ProjectOut(_Out):
    id: int
    name: str
    origin: str
    goal: str
    created_at: datetime


class GoalIn(BaseModel):
    goal: str = Field(max_length=5000)


class PageIn(BaseModel):
    url: str
    name: str = ""


class PageOut(_Out):
    id: int
    project_id: int
    url: str
    name: str
    setup: list[dict[str, Any]]
    created_at: datetime


class PageSetupIn(BaseModel):
    steps: list[SetupStep] = Field(max_length=50)


class RequirementIn(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class RequirementOut(_Out):
    id: int
    project_id: int
    text: str
    created_at: datetime


# -- inspections ------------------------------------------------------------------------
class InspectIn(BaseModel):
    scope: InspectionScope = InspectionScope()


class LocatorOut(_Out):
    id: int
    rank: int
    strategy: str
    expression: str
    match_count: int
    spec: dict[str, Any]
    targets_element: bool
    unique: bool


class ElementOut(_Out):
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
    locators: list[LocatorOut]


class SnapshotSummary(_Out):
    id: int
    page_id: int
    url: str
    title: str
    created_at: datetime
    element_count: int


class SnapshotOut(_Out):
    id: int
    page_id: int
    url: str
    title: str
    screenshot_path: str
    html_path: str
    html_sha256: str
    meta: dict[str, Any]
    created_at: datetime
    elements: list[ElementOut]


class InspectionOut(BaseModel):
    snapshot: SnapshotOut
    duration_ms: int = Field(description="Browser time in the runner (not model time)")
    blocked_requests: list[dict[str, str]]


# -- scope (G0) -------------------------------------------------------------------------
class ScopePage(BaseModel):
    snapshot_id: int
    include: list[str] = Field(default_factory=list, description="Element keys; empty = all")
    exclude: list[str] = Field(default_factory=list, description="Element keys to leave out")


class ScopeIn(BaseModel):
    pages: list[ScopePage] = Field(min_length=1)
    goal: str = Field(default="", max_length=5000)
    notes: str = Field(default="", max_length=5000)
    actor: str = Field(default="tester", max_length=100)


class ScopeOut(BaseModel):
    artifact_id: int
    version: VersionOut
    scope: ScopeIn
    approved: bool


# -- artifacts and versions -------------------------------------------------------------
class ArtifactOut(_Out):
    id: int
    project_id: int
    kind: str
    name: str
    created_at: datetime


class VersionOut(_Out):
    id: int
    artifact_id: int
    number: int
    content: str
    content_sha256: str
    author: str
    reason: str
    parent_number: int | None
    created_at: datetime


class VersionIn(BaseModel):
    content: str
    reason: str = Field(min_length=1, max_length=2000)
    actor: str = Field(default="tester", max_length=100)


class DiffRowOut(_Out):
    tag: str
    left_no: int | None
    left: str
    right_no: int | None
    right: str


class DiffOut(_Out):
    artifact_id: int
    from_number: int
    to_number: int
    unified: str
    rows: list[DiffRowOut]


class RestoreIn(BaseModel):
    number: int = Field(ge=1)
    approval_id: int = Field(description="G5 approval of exactly that version")


# -- gates ------------------------------------------------------------------------------
class ApprovalIn(BaseModel):
    gate: Literal["G0", "G1", "G2", "G3", "G4", "G5"]
    actor: str = Field(min_length=1, max_length=100)
    artifact_version_id: int | None = None
    subject: dict[str, Any] = Field(default_factory=dict)
    comment: str = Field(default="", max_length=2000)


class ApprovalOut(_Out):
    id: int
    project_id: int
    gate: str
    artifact_version_id: int | None
    subject: dict[str, Any]
    actor: str
    comment: str
    created_at: datetime


class ClarificationOut(_Out):
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


class AnswerIn(BaseModel):
    answer: str = Field(min_length=1, max_length=5000)
    actor: str = Field(min_length=1, max_length=100)


class StepOut(_Out):
    step: str
    gate: str | None
    status: Literal["todo", "needs_approval", "approved", "blocked"]
    detail: str
    open_clarifications: int


class LlmCallOut(_Out):
    id: int
    project_id: int | None
    purpose: str
    template_version: int
    provider: str
    model: str
    model_version: str
    input_tokens: int
    output_tokens: int
    tokens_estimated: bool
    latency_ms: int
    cache: str
    status: str
    error: str
    request: str
    response: str
    created_at: datetime


class InsightOut(BaseModel):
    """A grounded model answer with the usage evidence of the call that produced it."""

    insight: Insight
    call: LlmCallOut
    attempts: list[LlmCallOut]
    scope_version: int
    element_ids_sent: list[str]
    browser_ms: int = Field(description="Inspection (browser) time of the scoped pages")


class GateInfo(BaseModel):
    gate: str
    description: str


ScopeOut.model_rebuild()
