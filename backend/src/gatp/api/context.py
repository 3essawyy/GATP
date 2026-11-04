"""What the model may see: the latest **approved** scope and its elements (G0, TC-110)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from gatp.api.services import Services
from gatp.api.workflow import GateBlockedError, require_approval
from gatp.store.dto import SnapshotDTO
from gatp.test_designer.insight import ScopedElement, scoped_elements


@dataclass(frozen=True)
class ScopeContext:
    version_number: int
    scope: dict[str, Any]
    snapshots: dict[int, SnapshotDTO]
    elements: list[ScopedElement]

    @property
    def pages(self) -> list[dict[str, str]]:
        """Pages of the scope as the model sees them (URL + title)."""
        return [{"url": s.url, "title": s.title} for s in self.snapshots.values()]

    @property
    def browser_ms(self) -> int:
        return sum(int(s.meta.get("browser_ms", 0)) for s in self.snapshots.values())


def approved_scope(svc: Services, project_id: int) -> ScopeContext:
    """Latest scope version, which must carry a G0 approval; else ``GateBlockedError``."""
    artifact = svc.artifacts.find(project_id, "scope", "scope")
    if artifact is None:
        raise GateBlockedError("save and approve a scope (G0) first")
    version = svc.artifacts.latest(artifact.id)
    require_approval(svc, "G0", version)
    scope = json.loads(version.content)
    snapshots = {p["snapshot_id"]: svc.snapshots.get(p["snapshot_id"]) for p in scope["pages"]}
    return ScopeContext(version.number, scope, snapshots, scoped_elements(scope, snapshots))
