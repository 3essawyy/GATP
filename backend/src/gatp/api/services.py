"""Everything the API routes need, built once at startup (and replaced in tests)."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property

from gatp.api.events import EventBus
from gatp.config import Settings
from gatp.llm_gateway.gateway import LLMGateway
from gatp.runner.client import RunnerClient
from gatp.store.db import Database
from gatp.store.files import ArtifactFiles
from gatp.store.gates import GateRepository
from gatp.store.llm_calls import LlmCallRepository
from gatp.store.projects import ProjectRepository
from gatp.store.snapshots import SnapshotRepository
from gatp.store.versioning import ArtifactStore


@dataclass
class Services:
    settings: Settings
    db: Database
    runner: RunnerClient
    events: EventBus = field(default_factory=EventBus)

    @cached_property
    def projects(self) -> ProjectRepository:
        return ProjectRepository(self.db)

    @cached_property
    def snapshots(self) -> SnapshotRepository:
        return SnapshotRepository(self.db)

    @cached_property
    def artifacts(self) -> ArtifactStore:
        return ArtifactStore(self.db)

    @cached_property
    def gates(self) -> GateRepository:
        return GateRepository(self.db)

    @cached_property
    def llm_calls(self) -> LlmCallRepository:
        return LlmCallRepository(self.db)

    @cached_property
    def files(self) -> ArtifactFiles:
        return ArtifactFiles(self.settings.artifacts_dir)

    @cached_property
    def llm(self) -> LLMGateway:
        return LLMGateway.from_settings(self.settings, self.db)


def build_services(settings: Settings) -> Services:
    """Open (and migrate) the database and connect the runner client."""
    db = Database.from_settings(settings)
    db.migrate()
    runner = RunnerClient(settings.runner_socket, timeout_s=settings.runner_job_timeout_s + 60)
    return Services(settings=settings, db=db, runner=runner)
