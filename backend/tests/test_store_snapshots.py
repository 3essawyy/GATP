"""TC-104: snapshot round-trip; projects/pages; artifact files."""

from pathlib import Path

import pytest
import sqlalchemy as sa

from gatp.store.db import Database
from gatp.store.dto import ElementIn, LocatorIn, SnapshotIn
from gatp.store.errors import ValidationError
from gatp.store.files import ArtifactFiles
from gatp.store.immutability import ImmutableRowError
from gatp.store.models import Element
from gatp.store.projects import ProjectRepository, origin_of
from gatp.store.snapshots import SnapshotRepository


def _snapshot_in(page_id: int) -> SnapshotIn:
    return SnapshotIn(
        page_id=page_id,
        url="http://127.0.0.1:8090/index.html",
        title="BookShelf · Sign in",
        screenshot_path="snapshots/1/page.png",
        meta={"viewport": [1280, 800]},
        elements=(
            ElementIn(
                key="e1",
                tag="button",
                role="button",
                name="Sign in",
                attributes={"data-testid": "login-submit", "type": "submit"},
                bbox={"x": 10, "y": 20, "width": 80, "height": 30},
                fingerprint={"form": "login-form", "index": 0},
                source_line=23,
                locators=(
                    LocatorIn(
                        1,
                        "role",
                        'page.get_by_role("button", name="Sign in")',
                        1,
                        targets_element=True,
                    ),
                    LocatorIn(
                        2,
                        "test_id",
                        'page.get_by_test_id("login-submit")',
                        1,
                        targets_element=True,
                    ),
                    LocatorIn(6, "css", 'page.locator("button")', 1),
                ),
            ),
            ElementIn(key="e2", tag="input", role="textbox", name="Username"),
        ),
    )


def test_snapshot_round_trip(db: Database) -> None:
    projects = ProjectRepository(db)
    project = projects.create("BookShelf", "http://127.0.0.1:8090/")
    page = projects.add_page(project.id, "http://127.0.0.1:8090/index.html", "Sign in")
    repo = SnapshotRepository(db)
    data = _snapshot_in(page.id)
    saved = repo.save(data)
    again = repo.get(saved.id)
    assert again == saved
    e1 = again.elements[0]
    assert (e1.key, e1.name, e1.attributes, e1.bbox, e1.source_line) == (
        "e1",
        "Sign in",
        {"data-testid": "login-submit", "type": "submit"},
        {"x": 10, "y": 20, "width": 80, "height": 30},
        23,
    )
    assert [(c.rank, c.strategy, c.unique) for c in e1.locators] == [
        (1, "role", True),
        (2, "test_id", True),
        (6, "css", False),  # count 1 but not proven to target this element
    ]
    assert again.meta == {"viewport": [1280, 800]}
    second = repo.save(data)
    assert repo.latest_for_page(page.id) == second
    assert repo.list_for_page(page.id) == [saved.id, second.id]


def test_elements_are_immutable(db: Database) -> None:
    projects = ProjectRepository(db)
    project = projects.create("BookShelf", "http://127.0.0.1:8090/")
    page = projects.add_page(project.id, "http://127.0.0.1:8090/index.html")
    SnapshotRepository(db).save(_snapshot_in(page.id))
    with db.session() as s:
        s.scalars(sa.select(Element)).first().name = "changed"  # type: ignore[union-attr]
        with pytest.raises(ImmutableRowError):
            s.flush()
        s.rollback()


def test_duplicate_element_keys_rejected(db: Database) -> None:
    projects = ProjectRepository(db)
    page = projects.add_page(projects.create("P", "http://a.test/").id, "http://a.test/x")
    with pytest.raises(ValidationError):
        SnapshotRepository(db).save(
            SnapshotIn(page.id, "http://a.test/x", "", (ElementIn("e1", "a"), ElementIn("e1", "b")))
        )


def test_pages_must_stay_on_project_origin(db: Database) -> None:
    projects = ProjectRepository(db)
    project = projects.create("BookShelf", "http://127.0.0.1:8090/index.html")
    assert project.origin == "http://127.0.0.1:8090"
    first = projects.add_page(project.id, "http://127.0.0.1:8090/books.html")
    assert projects.add_page(project.id, "http://127.0.0.1:8090/books.html") == first
    with pytest.raises(ValidationError, match="outside the project origin"):
        projects.add_page(project.id, "http://evil.test/books.html")
    with pytest.raises(ValidationError):
        origin_of("file:///etc/passwd")


def test_artifact_files_confined_to_root(tmp_path: Path) -> None:
    files = ArtifactFiles(tmp_path / "artifacts")
    stored = files.write("snapshots/1/page.png", b"\x89PNG")
    assert stored.size == 4
    assert files.read(stored.path) == b"\x89PNG"
    for bad in ("../escape.txt", "/etc/passwd", "a/../../b"):
        with pytest.raises(ValidationError):
            files.write(bad, b"x")
