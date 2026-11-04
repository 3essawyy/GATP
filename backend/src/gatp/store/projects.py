"""Projects and pages repository."""

from __future__ import annotations

from urllib.parse import urlsplit

from sqlalchemy import select

from gatp.store.db import Database
from gatp.store.dto import PageDTO, ProjectDTO
from gatp.store.errors import NotFoundError, ValidationError
from gatp.store.models import Page, Project


def origin_of(url: str) -> str:
    """``scheme://host[:port]`` of a URL; rejects anything but http(s)."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise ValidationError(f"not an http(s) URL: {url!r}")
    return f"{parts.scheme}://{parts.netloc}"


def _project(p: Project) -> ProjectDTO:
    return ProjectDTO(p.id, p.name, p.origin, p.goal, p.created_at)


def _page(p: Page) -> PageDTO:
    return PageDTO(p.id, p.project_id, p.url, p.name, p.created_at)


class ProjectRepository:
    """Create and read projects and their pages."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def create(self, name: str, url: str) -> ProjectDTO:
        """New project whose allowlisted origin is taken from ``url``."""
        with self.db.session() as s:
            project = Project(name=name, origin=origin_of(url))
            s.add(project)
            s.flush()
            return _project(project)

    def get(self, project_id: int) -> ProjectDTO:
        with self.db.session() as s:
            project = s.get(Project, project_id)
            if project is None:
                raise NotFoundError(f"project {project_id}")
            return _project(project)

    def all(self) -> list[ProjectDTO]:
        with self.db.session() as s:
            return [_project(p) for p in s.scalars(select(Project).order_by(Project.id))]

    def set_goal(self, project_id: int, goal: str) -> ProjectDTO:
        with self.db.session() as s:
            project = s.get(Project, project_id)
            if project is None:
                raise NotFoundError(f"project {project_id}")
            project.goal = goal
            s.flush()
            return _project(project)

    def add_page(self, project_id: int, url: str, name: str = "") -> PageDTO:
        """Add a page (or return the existing one). The URL must be on the project's origin."""
        with self.db.session() as s:
            project = s.get(Project, project_id)
            if project is None:
                raise NotFoundError(f"project {project_id}")
            if origin_of(url) != project.origin:
                raise ValidationError(f"{url} is outside the project origin {project.origin}")
            existing = s.scalar(select(Page).where(Page.project_id == project_id, Page.url == url))
            if existing is not None:
                return _page(existing)
            page = Page(project_id=project_id, url=url, name=name)
            s.add(page)
            s.flush()
            return _page(page)

    def get_page(self, page_id: int) -> PageDTO:
        with self.db.session() as s:
            page = s.get(Page, page_id)
            if page is None:
                raise NotFoundError(f"page {page_id}")
            return _page(page)

    def pages(self, project_id: int) -> list[PageDTO]:
        with self.db.session() as s:
            rows = s.scalars(select(Page).where(Page.project_id == project_id).order_by(Page.id))
            return [_page(p) for p in rows]
