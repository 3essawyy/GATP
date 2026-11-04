"""Code generation and validation lifecycle (T-013, gate G2).

generate: approved plan (G1) -> rendered files stored as versioned artifacts (author ``generator``).
validate: static checks + live recount (runner) + ``pytest --collect-only`` (runner) -> a report
bound to the exact code versions. G2 needs a passing report for exactly those versions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from gatp.api.context import ScopeContext, approved_scope
from gatp.api.guard_sync import KIND as WEAKENING
from gatp.api.guard_sync import RESTORE, approved_baseline, sync_weakenings
from gatp.api.plan_service import (
    current_plan,
    sync_clarifications,
    sync_plan_weakenings,
)
from gatp.api.services import Services
from gatp.api.workflow import GateBlockedError, require_approval
from gatp.codegen.guard import code_weakenings
from gatp.codegen.render import ElementRef, render
from gatp.codegen.validate import normalise, validate
from gatp.inspector.locators import LocatorSpec
from gatp.runner.jobs import CollectJob, RecountJob, SetupStep
from gatp.store.dto import ArtifactDTO, VersionDTO
from gatp.store.gates import ClarificationDTO
from gatp.store.reports import ReportDTO, ReportRepository

CODE_KINDS = ("page_object", "test_file")


@dataclass(frozen=True)
class CodeFile:
    artifact_id: int
    path: str
    kind: str
    version: VersionDTO


def code_files(svc: Services, project_id: int) -> list[CodeFile]:
    """Current code set: latest versions of code artifacts that are not retired (empty)."""
    out = []
    for kind in CODE_KINDS:
        for a in svc.artifacts.list_artifacts(project_id, kind):
            v = svc.artifacts.latest(a.id)
            if v.content:
                out.append(CodeFile(a.id, a.name, kind, v))
    return sorted(out, key=lambda f: f.path)


def element_refs(ctx: ScopeContext) -> dict[str, ElementRef]:
    """Verified default locator (as data) for every scoped element that has one."""
    refs: dict[str, ElementRef] = {}
    for sid, snap in ctx.snapshots.items():
        for e in snap.elements:
            eid = f"s{sid}.{e.key}"
            idx = e.details.get("default_locator")
            if idx is None or eid not in {x.id for x in ctx.elements}:
                continue
            refs[eid] = ElementRef(
                id=eid,
                page_url=snap.url,
                role=e.role,
                tag=e.tag,
                name=e.name,
                html_id=str(e.attributes.get("id", "")),
                locator=LocatorSpec.model_validate(e.locators[idx].spec),
            )
    return refs


def verified_locators(ctx: ScopeContext) -> dict[str, tuple[str, LocatorSpec]]:
    """Every usable, non-positional candidate of scoped elements: expression -> (page, spec)."""
    allowed: dict[str, tuple[str, LocatorSpec]] = {}
    scoped = {e.id for e in ctx.elements}
    for sid, snap in ctx.snapshots.items():
        for e in snap.elements:
            if f"s{sid}.{e.key}" not in scoped:
                continue
            for c in e.locators:
                if c.unique and not c.spec.get("positional"):
                    spec = LocatorSpec.model_validate(c.spec)
                    allowed[normalise(spec.to_python("page"))] = (snap.url, spec)
    return allowed


def setup_locators(svc: Services, project_id: int) -> set[str]:
    """Locators of tester-approved setup steps (ADR-018); allowed in page objects' open()."""
    out = set()
    for p in svc.projects.pages(project_id):
        for step in p.setup:
            if step.get("locator"):
                out.add(normalise(LocatorSpec.model_validate(step["locator"]).to_python("page")))
    return out


def generate(svc: Services, project_id: int) -> list[CodeFile]:
    found = current_plan(svc, project_id)
    if found is None:
        raise GateBlockedError("propose and approve a test plan (G1) first")
    _, plan_version, plan = found
    require_approval(svc, "G1", plan_version)
    ctx = approved_scope(svc, project_id)
    refs = element_refs(ctx)
    missing = sorted(
        {
            s.element_id
            for c in plan.cases
            for s in c.steps
            if s.element_id and s.element_id not in refs
        }
        | {
            e.element_id
            for c in plan.cases
            for e in c.expected
            if e.element_id and e.element_id not in refs
        }
    )
    if missing:
        raise GateBlockedError(f"elements without a verified locator: {missing}")
    project = svc.projects.get(project_id)
    files = render(
        plan,
        refs,
        origin=project.origin,
        plan_number=plan_version.number,
        plan_version_id=plan_version.id,
        setups={p.url: list(p.setup) for p in svc.projects.pages(project_id)},
    )
    reason = f"generated from test plan v{plan_version.number} (version id {plan_version.id})"
    produced = set()
    for f in files:
        produced.add(f.path)
        existing = svc.artifacts.find(project_id, f.kind, f.path)
        if existing is None:
            svc.artifacts.create_artifact(
                project_id, f.kind, f.path, f.content, "generator", reason
            )
        elif svc.artifacts.latest(existing.id).content != f.content:
            svc.artifacts.new_version(existing.id, f.content, "generator", reason)
    for old in code_files(svc, project_id):
        if old.path not in produced:
            svc.artifacts.new_version(
                old.artifact_id,
                "",
                "generator",
                f"retired: not used by plan v{plan_version.number}",
            )
    sync_code_weakenings(svc, project_id)
    svc.events.publish(project_id, "artifact_changed", {"code": True})
    return code_files(svc, project_id)


def sync_code_weakenings(svc: Services, project_id: int) -> None:
    """Flag assertions a tester edit removed/changed vs the last G2-approved test file.

    Generated files are not checked here: they follow the G1-approved plan, whose own
    revisions are guarded (plan_service.sync_plan_weakenings).
    """
    findings: dict[str, tuple[str, dict[str, Any]]] = {}
    for f in code_files(svc, project_id):
        if not f.path.startswith("tests/") or f.version.author == "generator":
            continue
        baseline = approved_baseline(svc, f.artifact_id, "G2")
        if baseline is None or baseline.id == f.version.id:
            continue
        for w in code_weakenings(f.path, baseline.content, f.version.content):
            findings[w.key] = (
                f"{f.path} v{f.version.number}: {w.message}. This weakens what the approved "
                f"code (v{baseline.number}) checks: accept the change, or restore the approved "
                "file?",
                {
                    "change": w.change,
                    "artifact_id": f.artifact_id,
                    "path": f.path,
                    "test": w.test,
                    "baseline_version_id": baseline.id,
                    "baseline_number": baseline.number,
                },
            )
    sync_weakenings(svc, project_id, "code", findings)


def on_artifact_changed(svc: Services, artifact: ArtifactDTO) -> None:
    """After a generic tester edit or restore: keep plan/code clarifications in sync."""
    if artifact.kind == "test_plan":
        found = current_plan(svc, artifact.project_id)
        if found is not None:
            sync_clarifications(svc, artifact.project_id, found[2])
            sync_plan_weakenings(svc, artifact.project_id, artifact.id, found[2])
    elif artifact.kind in CODE_KINDS:
        sync_code_weakenings(svc, artifact.project_id)


def apply_code_answer(svc: Services, clarification: ClarificationDTO) -> None:
    """Restore the approved test file when the tester chose to (Accept changes nothing)."""
    if clarification.step != "code" or clarification.kind != WEAKENING:
        return
    if clarification.answer == RESTORE:
        ev = clarification.evidence
        artifact_id = int(ev["artifact_id"])
        baseline = svc.artifacts.get_version_by_id(int(ev["baseline_version_id"]))
        if svc.artifacts.latest(artifact_id).content != baseline.content:
            svc.artifacts.new_version(
                artifact_id,
                baseline.content,
                "user",
                f"restored approved v{baseline.number} (clarification #{clarification.id}, "
                f"{clarification.answered_by})",
            )
    sync_code_weakenings(svc, clarification.project_id)
    svc.events.publish(clarification.project_id, "artifact_changed", {"code": True})


def run_validation(svc: Services, project_id: int) -> ReportDTO:
    files = code_files(svc, project_id)
    if not files:
        raise GateBlockedError("generate code first")
    ctx = approved_scope(svc, project_id)
    allowed = verified_locators(ctx)
    contents = {f.path: f.version.content for f in files}
    setup = setup_locators(svc, project_id)
    static = validate(contents, set(allowed) | setup)
    report: dict[str, Any] = {
        "static": {
            "ok": static.ok,
            "findings": [vars(x) for x in static.findings],
            "locators": len(static.locators),
            # setup-step locators act on other pages (e.g. sign-in); approved by the tester
            "setup_locators": sum(1 for x in static.locators if x in setup and x not in allowed),
        }
    }
    # Live recount of every verified locator the code uses, per page, with its setup steps.
    pages = {p.url: p for p in svc.projects.pages(project_id)}
    by_page: dict[str, list[tuple[str, LocatorSpec]]] = {}
    for expr in dict.fromkeys(static.locators):
        if expr in allowed:
            url, spec = allowed[expr]
            by_page.setdefault(url, []).append((expr, spec))
    recount: list[dict[str, Any]] = []
    project = svc.projects.get(project_id)
    for url, items in by_page.items():
        page = pages.get(url)
        result = svc.runner.submit(
            RecountJob(
                url=url,
                allowlist=[project.origin],
                locators=[spec for _, spec in items],
                setup=[SetupStep.model_validate(s) for s in (page.setup if page else ())],
            )
        )
        counts = result.data.get("counts", []) if result.status == "ok" else []
        for (expr, _), count in zip(items, counts or [None] * len(items), strict=True):
            recount.append({"page": url, "locator": expr, "count": count, "ok": count == 1})
        if result.status != "ok":
            recount.append(
                {
                    "page": url,
                    "locator": "(page)",
                    "count": None,
                    "ok": False,
                    "error": result.error,
                }
            )
    report["recount"] = {"ok": all(r["ok"] for r in recount), "items": recount}
    if static.ok:
        collected = svc.runner.submit(CollectJob(files=contents))
        tests = collected.data.get("tests", [])
        report["collect"] = {
            "ok": collected.status == "ok",
            "tests": tests,
            "exit_code": collected.data.get("exit_code"),
            "output": collected.data.get("output", "")[-2000:] if collected.status != "ok" else "",
            "error": collected.error,
        }
    else:
        report["collect"] = {"ok": False, "tests": [], "error": "skipped: static checks failed"}
    ok = all(report[k]["ok"] for k in ("static", "recount", "collect"))
    saved = ReportRepository(svc.db).add(project_id, [f.version.id for f in files], ok, report)
    svc.events.publish(project_id, "code_validated", {"ok": ok})
    return saved


def latest_report_for_current(svc: Services, project_id: int) -> ReportDTO | None:
    """The newest report, but only if it covers exactly the current code versions."""
    report = ReportRepository(svc.db).latest(project_id)
    current = tuple(sorted(f.version.id for f in code_files(svc, project_id)))
    return report if report is not None and report.version_ids == current else None
