"""Projects, pages (+ setup steps), goal and requirements."""

from __future__ import annotations

from fastapi import APIRouter

from gatp.api.routes.deps import Svc
from gatp.api.schemas import (
    GoalIn,
    PageIn,
    PageOut,
    PageSetupIn,
    ProjectIn,
    ProjectOut,
    RequirementIn,
    RequirementOut,
)
from gatp.runner.jobs import origin
from gatp.store.errors import ValidationError

router = APIRouter(prefix="/api", tags=["projects"])


@router.post("/projects", operation_id="createProject", status_code=201)
def create_project(body: ProjectIn, svc: Svc) -> ProjectOut:
    project = svc.projects.create(body.name.strip(), body.url)
    svc.projects.add_page(project.id, body.url, "start page")
    return ProjectOut.model_validate(project)


@router.get("/projects", operation_id="listProjects")
def list_projects(svc: Svc) -> list[ProjectOut]:
    return [ProjectOut.model_validate(p) for p in svc.projects.all()]


@router.get("/projects/{project_id}", operation_id="getProject")
def get_project(project_id: int, svc: Svc) -> ProjectOut:
    return ProjectOut.model_validate(svc.projects.get(project_id))


@router.put("/projects/{project_id}/goal", operation_id="setGoal")
def set_goal(project_id: int, body: GoalIn, svc: Svc) -> ProjectOut:
    project = svc.projects.set_goal(project_id, body.goal.strip())
    svc.events.publish(project_id, "goal_changed")
    return ProjectOut.model_validate(project)


@router.get("/projects/{project_id}/pages", operation_id="listPages")
def list_pages(project_id: int, svc: Svc) -> list[PageOut]:
    svc.projects.get(project_id)
    return [PageOut.model_validate(p) for p in svc.projects.pages(project_id)]


@router.post("/projects/{project_id}/pages", operation_id="addPage", status_code=201)
def add_page(project_id: int, body: PageIn, svc: Svc) -> PageOut:
    page = svc.projects.add_page(project_id, body.url, body.name)
    svc.events.publish(project_id, "page_added", {"page_id": page.id})
    return PageOut.model_validate(page)


@router.put("/pages/{page_id}/setup", operation_id="setPageSetup")
def set_page_setup(page_id: int, body: PageSetupIn, svc: Svc) -> PageOut:
    """Steps run before inspecting this page (e.g. sign in), ADR-018. URLs must be on-origin."""
    page = svc.projects.get_page(page_id)
    project = svc.projects.get(page.project_id)
    for step in body.steps:
        if step.action != "goto":
            continue
        try:
            step_origin = origin(step.url)
        except ValueError:  # relative or non-http(s) URL: a tester mistake, not a server error
            raise ValidationError(
                f"setup url {step.url!r} must be a full http(s) URL, "
                f"e.g. {project.origin}/index.html"
            ) from None
        if step_origin != project.origin:
            raise ValidationError(f"setup url {step.url} is outside {project.origin}")
    steps = [s.model_dump(mode="json", exclude_defaults=True) for s in body.steps]
    return PageOut.model_validate(svc.projects.set_page_setup(page_id, steps))


@router.get("/projects/{project_id}/requirements", operation_id="listRequirements")
def list_requirements(project_id: int, svc: Svc) -> list[RequirementOut]:
    return [RequirementOut.model_validate(r) for r in svc.gates.requirements(project_id)]


@router.post("/projects/{project_id}/requirements", operation_id="addRequirement", status_code=201)
def add_requirement(project_id: int, body: RequirementIn, svc: Svc) -> RequirementOut:
    return RequirementOut.model_validate(svc.gates.add_requirement(project_id, body.text))
