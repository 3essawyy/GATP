"""Artifact files on disk (screenshots, HTML, traces, run outputs). The DB stores path + hash."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from gatp.store.errors import ValidationError


@dataclass(frozen=True)
class StoredFile:
    """A file written under the artifacts root; ``path`` is relative and POSIX-style."""

    path: str
    sha256: str
    size: int


class ArtifactFiles:
    """Write and read files strictly inside the artifacts root."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def _resolve(self, relative: str) -> Path:
        rel = PurePosixPath(relative)
        if rel.is_absolute() or ".." in rel.parts:
            raise ValidationError(f"artifact path must stay inside the artifacts root: {relative}")
        full = (self.root / rel).resolve()
        if not full.is_relative_to(self.root):
            raise ValidationError(f"artifact path escapes the artifacts root: {relative}")
        return full

    def write(self, relative: str, data: bytes) -> StoredFile:
        """Write bytes (creating folders) and return path + SHA-256."""
        full = self._resolve(relative)
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_bytes(data)
        return StoredFile(str(PurePosixPath(relative)), hashlib.sha256(data).hexdigest(), len(data))

    def read(self, relative: str) -> bytes:
        return self._resolve(relative).read_bytes()

    def absolute(self, relative: str) -> Path:
        """Absolute path of a stored file (for serving it)."""
        return self._resolve(relative)
