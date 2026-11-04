"""Immutable artifact versioning: create, new version, read, diff, restore (ADR-005)."""

from __future__ import annotations

import difflib
import hashlib

from sqlalchemy import func, select

from gatp.store.db import Database
from gatp.store.dto import (
    ARTIFACT_KINDS,
    AUTHORS,
    ArtifactDTO,
    DiffRow,
    VersionDiff,
    VersionDTO,
)
from gatp.store.errors import NotFoundError, ValidationError
from gatp.store.models import Artifact, ArtifactVersion, Project


def sha256(text: str) -> str:
    """Hex SHA-256 of UTF-8 text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _artifact(a: Artifact) -> ArtifactDTO:
    return ArtifactDTO(a.id, a.project_id, a.kind, a.name, a.created_at)


def _version(v: ArtifactVersion) -> VersionDTO:
    return VersionDTO(
        id=v.id,
        artifact_id=v.artifact_id,
        number=v.number,
        content=v.content,
        content_sha256=v.content_sha256,
        author=v.author,
        reason=v.reason,
        parent_number=v.parent_number,
        created_at=v.created_at,
    )


def side_by_side(old: str, new: str) -> tuple[DiffRow, ...]:
    """Side-by-side diff rows (what the UI renders as two columns)."""
    a, b = old.splitlines(), new.splitlines()
    rows: list[DiffRow] = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if tag == "equal":
            rows += [
                DiffRow("equal", i + 1, a[i], j + 1, b[j])
                for i, j in zip(range(i1, i2), range(j1, j2), strict=True)
            ]
        elif tag == "replace":
            n = max(i2 - i1, j2 - j1)
            for k in range(n):
                i, j = i1 + k, j1 + k
                rows.append(
                    DiffRow(
                        "replace",
                        i + 1 if i < i2 else None,
                        a[i] if i < i2 else "",
                        j + 1 if j < j2 else None,
                        b[j] if j < j2 else "",
                    )
                )
        elif tag == "delete":
            rows += [DiffRow("delete", i + 1, a[i], None, "") for i in range(i1, i2)]
        else:  # insert
            rows += [DiffRow("insert", None, "", j + 1, b[j]) for j in range(j1, j2)]
    return tuple(rows)


class ArtifactStore:
    """Versioned artifacts. Versions are append-only; nothing is ever updated or deleted."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def create_artifact(
        self, project_id: int, kind: str, name: str, content: str, author: str, reason: str
    ) -> tuple[ArtifactDTO, VersionDTO]:
        """Create an artifact together with its version 1."""
        if kind not in ARTIFACT_KINDS:
            raise ValidationError(f"unknown artifact kind {kind!r}")
        self._check_author(author)
        with self.db.session() as s:
            if s.get(Project, project_id) is None:
                raise NotFoundError(f"project {project_id}")
            artifact = Artifact(project_id=project_id, kind=kind, name=name)
            version = ArtifactVersion(
                number=1,
                content=content,
                content_sha256=sha256(content),
                author=author,
                reason=reason,
                parent_number=None,
            )
            artifact.versions.append(version)
            s.add(artifact)
            s.flush()
            return _artifact(artifact), _version(version)

    def new_version(
        self,
        artifact_id: int,
        content: str,
        author: str,
        reason: str,
        parent: int | None = None,
    ) -> VersionDTO:
        """Append version N+1. ``parent`` defaults to the current latest version."""
        self._check_author(author)
        with self.db.session() as s:
            if s.get(Artifact, artifact_id) is None:
                raise NotFoundError(f"artifact {artifact_id}")
            latest = s.scalar(
                select(func.max(ArtifactVersion.number)).where(
                    ArtifactVersion.artifact_id == artifact_id
                )
            )
            number = (latest or 0) + 1
            parent_number = latest if parent is None else parent
            if parent_number is not None and not 1 <= parent_number <= number - 1:
                raise ValidationError(f"parent version {parent_number} does not exist")
            version = ArtifactVersion(
                artifact_id=artifact_id,
                number=number,
                content=content,
                content_sha256=sha256(content),
                author=author,
                reason=reason,
                parent_number=parent_number,
            )
            s.add(version)
            s.flush()
            return _version(version)

    def get_artifact(self, artifact_id: int) -> ArtifactDTO:
        with self.db.session() as s:
            artifact = s.get(Artifact, artifact_id)
            if artifact is None:
                raise NotFoundError(f"artifact {artifact_id}")
            return _artifact(artifact)

    def list_artifacts(self, project_id: int, kind: str | None = None) -> list[ArtifactDTO]:
        with self.db.session() as s:
            q = select(Artifact).where(Artifact.project_id == project_id)
            if kind is not None:
                q = q.where(Artifact.kind == kind)
            return [_artifact(a) for a in s.scalars(q.order_by(Artifact.id))]

    def find(self, project_id: int, kind: str, name: str) -> ArtifactDTO | None:
        with self.db.session() as s:
            a = s.scalar(
                select(Artifact).where(
                    Artifact.project_id == project_id, Artifact.kind == kind, Artifact.name == name
                )
            )
            return None if a is None else _artifact(a)

    def get_version(self, artifact_id: int, number: int) -> VersionDTO:
        with self.db.session() as s:
            v = s.scalar(
                select(ArtifactVersion).where(
                    ArtifactVersion.artifact_id == artifact_id, ArtifactVersion.number == number
                )
            )
            if v is None:
                raise NotFoundError(f"artifact {artifact_id} version {number}")
            return _version(v)

    def get_version_by_id(self, version_id: int) -> VersionDTO:
        with self.db.session() as s:
            v = s.get(ArtifactVersion, version_id)
            if v is None:
                raise NotFoundError(f"artifact version id {version_id}")
            return _version(v)

    def latest(self, artifact_id: int) -> VersionDTO:
        with self.db.session() as s:
            v = s.scalar(
                select(ArtifactVersion)
                .where(ArtifactVersion.artifact_id == artifact_id)
                .order_by(ArtifactVersion.number.desc())
                .limit(1)
            )
            if v is None:
                raise NotFoundError(f"artifact {artifact_id}")
            return _version(v)

    def history(self, artifact_id: int) -> list[VersionDTO]:
        """All versions, oldest first."""
        with self.db.session() as s:
            rows = s.scalars(
                select(ArtifactVersion)
                .where(ArtifactVersion.artifact_id == artifact_id)
                .order_by(ArtifactVersion.number)
            )
            return [_version(v) for v in rows]

    def diff(self, artifact_id: int, a: int, b: int) -> VersionDiff:
        """Unified + side-by-side diff from version ``a`` to version ``b``."""
        old, new = self.get_version(artifact_id, a), self.get_version(artifact_id, b)
        unified = "".join(
            difflib.unified_diff(
                old.content.splitlines(keepends=True),
                new.content.splitlines(keepends=True),
                fromfile=f"v{a}",
                tofile=f"v{b}",
            )
        )
        return VersionDiff(artifact_id, a, b, unified, side_by_side(old.content, new.content))

    def restore(self, artifact_id: int, number: int, actor: str) -> VersionDTO:
        """Append a new version whose content equals version ``number`` (author ``restore``)."""
        target = self.get_version(artifact_id, number)
        return self.new_version(
            artifact_id,
            target.content,
            author="restore",
            reason=f"Restore of v{number} by {actor}",
        )

    @staticmethod
    def _check_author(author: str) -> None:
        if author not in AUTHORS:
            raise ValidationError(f"unknown author {author!r}; expected one of {AUTHORS}")
