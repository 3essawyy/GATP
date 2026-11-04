"""Per-job sandbox working directories (ADR-004).

Each job gets a fresh, private directory. Outputs that should survive are copied to
``<artifacts>/jobs/<job_id>/``; the sandbox itself is always deleted afterwards.
"""

from __future__ import annotations

import shutil
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Sandbox:
    job_id: str
    path: Path
    artifacts_root: Path

    def keep(self, name: str) -> str:
        """Copy ``<sandbox>/<name>`` to ``artifacts/jobs/<job_id>/<name>``; return that path."""
        src = (self.path / name).resolve()
        if not src.is_relative_to(self.path.resolve()):
            raise ValueError(f"{name} is outside the sandbox")
        rel = Path("jobs") / self.job_id / name
        dest = self.artifacts_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        return rel.as_posix()


@contextmanager
def job_sandbox(root: Path, artifacts_root: Path, job_id: str | None = None) -> Iterator[Sandbox]:
    """Create ``<root>/job-<id>/`` (mode 0700), yield it, then delete it."""
    jid = job_id or uuid.uuid4().hex[:12]
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"job-{jid}"
    path.mkdir(mode=0o700)
    try:
        yield Sandbox(jid, path, artifacts_root)
    finally:
        shutil.rmtree(path, ignore_errors=True)
