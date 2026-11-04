"""Typed runner jobs and results (ADR-004, ADR-017).

The runner accepts nothing but these models. ``Job`` is a discriminated union on ``type``, so
an unknown job type is rejected by validation before any code runs. Every job carries its
own origin allowlist, and its URL must be inside it.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator

from gatp.inspector.locators import LocatorSpec
from gatp.inspector.models import InspectionScope


def origin(url: str) -> str:
    """``scheme://host[:port]`` of an http(s) URL; raises ``ValueError`` otherwise."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise ValueError(f"not an http(s) URL: {url!r}")
    return f"{parts.scheme}://{parts.netloc}"


class _BrowserJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    allowlist: list[str] = Field(min_length=1, description="Allowed origins, e.g. http://host:port")
    timeout_s: float = Field(default=30.0, gt=0, le=600)

    @model_validator(mode="after")
    def _url_inside_allowlist(self) -> _BrowserJob:
        allowed = {origin(o) for o in self.allowlist}
        if origin(self.url) not in allowed:
            raise ValueError(f"url origin {origin(self.url)} is not in the allowlist")
        self.allowlist = sorted(allowed)
        return self


class SetupStep(BaseModel):
    """One tester-approved step run before inspecting (e.g. signing in). Data, not code."""

    model_config = ConfigDict(extra="forbid")

    action: Literal["goto", "fill", "click", "select"]
    url: str = ""  # goto only
    locator: LocatorSpec | None = None  # fill / click / select
    value: str = ""  # fill / select

    @model_validator(mode="after")
    def _fields_match_action(self) -> SetupStep:
        if self.action == "goto" and not self.url:
            raise ValueError("goto needs a url")
        if self.action != "goto" and self.locator is None:
            raise ValueError(f"{self.action} needs a locator")
        return self


class _PageJob(_BrowserJob):
    """A browser job that may first run tester-approved setup steps (ADR-018)."""

    setup: list[SetupStep] = Field(default_factory=list, max_length=50)

    @model_validator(mode="after")
    def _setup_urls_inside_allowlist(self) -> _PageJob:
        for step in self.setup:
            if step.action == "goto" and origin(step.url) not in self.allowlist:
                raise ValueError(f"setup url {step.url} is not in the allowlist")
        return self


class InspectJob(_PageJob):
    """Open the page in a visible browser and inspect it (T-007)."""

    type: Literal["inspect"] = "inspect"
    scope: InspectionScope = InspectionScope()


class RecountJob(_PageJob):
    """Count how many elements each locator matches on the live page (uniqueness, ADR-006)."""

    type: Literal["recount"] = "recount"
    locators: list[LocatorSpec] = Field(min_length=1, max_length=500)


SAFE_PATH = r"^(pages/[a-z0-9_]+\.py|tests/test_[a-z0-9_]+\.py|conftest\.py)$"


class CollectJob(BaseModel):
    """``pytest --collect-only`` on approved code files in a fresh sandbox (T-013)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["collect"] = "collect"
    files: dict[Annotated[str, Field(pattern=SAFE_PATH)], str] = Field(min_length=1, max_length=50)
    timeout_s: float = Field(default=60.0, gt=0, le=300)


Job = Annotated[InspectJob | RecountJob | CollectJob, Field(discriminator="type")]


class JobRequest(BaseModel):
    """Envelope posted to the runner."""

    model_config = ConfigDict(extra="forbid")

    job: Job


class BlockedRequest(BaseModel):
    url: str
    resource_type: str


class JobResult(BaseModel):
    """Outcome of one job. ``data`` depends on the job type; files are artifact-relative paths."""

    job_id: str
    type: str
    status: Literal["ok", "failed"]
    duration_ms: int
    blocked_requests: list[BlockedRequest] = []
    files: dict[str, str] = {}
    data: dict[str, Any] = {}
    error: str = ""
