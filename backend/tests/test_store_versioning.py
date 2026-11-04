"""TC-104 / TC-211: immutable versions, diff, restore."""

import pytest
import sqlalchemy as sa

from gatp.store.db import Database
from gatp.store.errors import NotFoundError, ValidationError
from gatp.store.immutability import ImmutableRowError
from gatp.store.models import ArtifactVersion
from gatp.store.projects import ProjectRepository
from gatp.store.versioning import ArtifactStore, sha256


@pytest.fixture
def store(db: Database) -> ArtifactStore:
    return ArtifactStore(db)


@pytest.fixture
def project_id(db: Database) -> int:
    return ProjectRepository(db).create("BookShelf", "http://127.0.0.1:8090/index.html").id


def test_create_and_new_versions(store: ArtifactStore, project_id: int) -> None:
    art, v1 = store.create_artifact(project_id, "test_case", "login", "a\nb\n", "model", "proposed")
    assert (v1.number, v1.parent_number, v1.author) == (1, None, "model")
    assert v1.content_sha256 == sha256("a\nb\n")
    v2 = store.new_version(art.id, "a\nB\n", "user", "edited step 2")
    v3 = store.new_version(art.id, "a\nB\nc\n", "model", "revised")
    assert [v.number for v in store.history(art.id)] == [1, 2, 3]
    assert (v2.parent_number, v3.parent_number) == (1, 2)
    assert store.latest(art.id) == v3
    assert store.get_version(art.id, 1).content == "a\nb\n"  # old version unchanged


def test_versions_cannot_be_updated_or_deleted(
    db: Database, store: ArtifactStore, project_id: int
) -> None:
    art, _ = store.create_artifact(project_id, "test_file", "t.py", "x = 1\n", "model", "gen")
    with db.session() as s:
        row = s.scalars(sa.select(ArtifactVersion)).one()
        row.content = "tampered"
        with pytest.raises(ImmutableRowError):
            s.flush()
        s.rollback()
        s.delete(s.scalars(sa.select(ArtifactVersion)).one())
        with pytest.raises(ImmutableRowError):
            s.flush()
        s.rollback()
    with db.engine.begin() as conn, pytest.raises(sa.exc.DatabaseError, match="immutable"):
        conn.execute(sa.text("UPDATE artifact_versions SET content = 'raw tamper'"))
    assert store.latest(art.id).content == "x = 1\n"


def test_restore_creates_new_version(store: ArtifactStore, project_id: int) -> None:
    art, _ = store.create_artifact(project_id, "test_plan", "plan", "one\n", "model", "proposed")
    store.new_version(art.id, "two\n", "user", "edit")
    restored = store.restore(art.id, 1, actor="Abdo")
    assert restored.number == 3
    assert restored.author == "restore"
    assert restored.content == "one\n"
    assert restored.parent_number == 2
    assert "v1" in restored.reason
    assert "Abdo" in restored.reason
    assert len(store.history(art.id)) == 3


def test_diff_unified_and_side_by_side(store: ArtifactStore, project_id: int) -> None:
    art, _ = store.create_artifact(
        project_id, "page_object", "LoginPage", "a\nb\nc\n", "model", "gen"
    )
    store.new_version(art.id, "a\nB\nc\nd\n", "repair", "locator repair")
    d = store.diff(art.id, 1, 2)
    assert "-b\n" in d.unified
    assert "+B\n" in d.unified
    assert "+d\n" in d.unified
    assert [(r.tag, r.left, r.right) for r in d.rows] == [
        ("equal", "a", "a"),
        ("replace", "b", "B"),
        ("equal", "c", "c"),
        ("insert", "", "d"),
    ]


def test_rejects_unknown_author_kind_and_parent(store: ArtifactStore, project_id: int) -> None:
    with pytest.raises(ValidationError):
        store.create_artifact(project_id, "test_case", "x", "", "robot", "")
    with pytest.raises(ValidationError):
        store.create_artifact(project_id, "notes", "x", "", "user", "")
    art, _ = store.create_artifact(project_id, "test_case", "x", "", "user", "")
    with pytest.raises(ValidationError):
        store.new_version(art.id, "y", "user", "", parent=5)
    with pytest.raises(NotFoundError):
        store.get_version(art.id, 9)
