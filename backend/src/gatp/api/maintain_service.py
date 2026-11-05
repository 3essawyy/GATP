"""Rescan + snapshot diff + change flags (T-016, ADR-007, ADR-024).

On the tester's request, every page of the approved scope is inspected again (new immutable
snapshots) and compared with the snapshot the tests were built on. Elements the tests use
(plan steps/expectations, and setup-step locators) are classified unchanged / clear match /
ambiguous / missing by the maintainer's deterministic matcher. Nothing is repaired here;
repairs need G4 (T-017).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from gatp.api.context import approved_scope
from gatp.api.inspections import to_snapshot_in
from gatp.api.plan_service import current_plan
from gatp.api.services import Services
from gatp.codegen.validate import normalise
from gatp.inspector.locators import LocatorSpec
from gatp.inspector.models import InspectionResult, InspectionScope
from gatp.maintainer.match import El, ElementChange, match_page
from gatp.runner.jobs import InspectJob, SetupStep
from gatp.store.dto import ElementDTO, PageDTO, SnapshotDTO
from gatp.store.rescans import PageChange, RescanDTO, RescanRepository


@dataclass
class Reference:
    """An element the tests depend on, and why."""

    used_by: list[str] = field(default_factory=list)


def to_el(e: ElementDTO) -> El:
    usable = tuple(
        normalise(c.expression) for c in e.locators if c.unique and not c.spec.get("positional")
    )
    idx = e.details.get("default_locator")
    default = normalise(e.locators[idx].expression) if idx is not None else ""
    return El(e.key, bool(e.details.get("interactive", True)), dict(e.fingerprint), usable, default)


def _label(e: ElementDTO) -> str:
    return f'{e.role or e.tag} "{e.name or e.attributes.get("id", "") or e.key}"'


def _shown(e: ElementDTO | None) -> str:
    """Default locator as the generated code writes it (for display; matching normalises)."""
    if e is None:
        return ""
    idx = e.details.get("default_locator")
    return "" if idx is None else e.locators[idx].expression


def _default_spec(e: ElementDTO) -> dict[str, Any] | None:
    idx = e.details.get("default_locator")
    return None if idx is None else dict(e.locators[idx].spec)


def references(
    svc: Services, project_id: int, baseline: dict[int, SnapshotDTO]
) -> dict[str, Reference]:
    """``s<sid>.<key>`` -> what uses it: plan cases and setup steps."""
    refs: dict[str, Reference] = {}
    found = current_plan(svc, project_id)
    if found is not None:
        for case in found[2].cases:
            ids = [s.element_id for s in case.steps] + [e.element_id for e in case.expected]
            for eid in ids:
                if eid and case.id not in refs.setdefault(eid, Reference()).used_by:
                    refs[eid].used_by.append(case.id)
    by_expression = {
        expr: f"s{sid}.{e.key}"
        for sid, snap in baseline.items()
        for e in snap.elements
        for expr in to_el(e).usable
    }
    for page in svc.projects.pages(project_id):
        for n, step in enumerate(page.setup, 1):
            if not step.get("locator"):
                continue
            expr = normalise(LocatorSpec.model_validate(step["locator"]).to_python("page"))
            eid = by_expression.get(expr)
            if eid:
                refs.setdefault(eid, Reference()).used_by.append(f"setup of {page.url} step {n}")
    return refs


def _inspect(
    svc: Services, page: PageDTO, origin: str, scope: dict[str, Any], setup: list[dict[str, Any]]
) -> tuple[SnapshotDTO | None, str, int | None]:
    result = svc.runner.submit(
        InspectJob(
            url=page.url,
            allowlist=[origin],
            scope=InspectionScope.model_validate(scope or {}),
            setup=[SetupStep.model_validate(s) for s in setup],
            timeout_s=svc.settings.runner_job_timeout_s,
        )
    )
    if result.status != "ok":
        step = result.data.get("failed_setup_step")
        return None, result.error or "inspection failed", int(step) if step else None
    inspection = InspectionResult.model_validate(result.data)
    snapshot = svc.snapshots.save(
        to_snapshot_in(page.id, inspection, result.files, result.duration_ms)
    )
    return snapshot, "", None


def rescan(svc: Services, project_id: int) -> RescanDTO:
    ctx = approved_scope(svc, project_id)
    project = svc.projects.get(project_id)
    baseline = ctx.snapshots
    refs = references(svc, project_id, baseline)
    pages = {p.id: p for p in svc.projects.pages(project_id)}
    svc.events.publish(project_id, "rescan_started", {"pages": len(baseline)})

    results: dict[int, dict[str, Any]] = {}  # old snapshot id -> outcome
    for sid, old in baseline.items():
        page = pages[old.page_id]
        new, error, step = _inspect(
            svc, page, project.origin, old.meta.get("scope", {}), list(page.setup)
        )
        results[sid] = {"page": page, "new": new, "error": error, "failed_setup_step": step}

    changes: dict[int, tuple[dict[str, ElementChange], list[str]]] = {}
    for sid, r in results.items():
        if r["new"] is not None:
            changes[sid] = _match(baseline[sid], r["new"])

    # A setup step that broke on an element with a clear match elsewhere: inspect again,
    # read-only, with the proposed locator, so the page itself can still be compared.
    for sid, r in results.items():
        if r["new"] is not None or not r["failed_setup_step"]:
            continue
        trial = _trial_setup(r["page"], r["failed_setup_step"], baseline, results, changes)
        if trial is None:
            continue
        new, error, step = _inspect(
            svc, r["page"], project.origin, baseline[sid].meta.get("scope", {}), trial["setup"]
        )
        r["trial_setup"] = {k: v for k, v in trial.items() if k != "setup"}
        if new is not None:
            r.update(new=new, error="", failed_setup_step=None)
            changes[sid] = _match(baseline[sid], new)
        else:
            r["trial_setup"]["error"] = error

    page_changes = []
    page_rows = []
    for sid, r in results.items():
        row = {
            "page_id": r["page"].id,
            "page_url": r["page"].url,
            "old_snapshot_id": sid,
            "new_snapshot_id": r["new"].id if r["new"] else None,
            "error": r["error"],
            "failed_setup_step": r["failed_setup_step"],
            "trial_setup": r.get("trial_setup"),
        }
        page_rows.append(row)
        if r["new"] is not None:
            summary = page_summary(baseline[sid], r["new"], *changes[sid], refs)
            summary["trial_setup"] = r.get("trial_setup")
            row["counts"] = summary["counts"]
            page_changes.append(PageChange(sid, r["new"].id, summary))
    attention = sum(
        c["counts"]["clear_match"] + c["counts"]["ambiguous"] + c["counts"]["missing"]
        for c in page_rows
        if "counts" in c
    )
    errors = sum(1 for c in page_rows if c["error"])
    saved = RescanRepository(svc.db).add(
        project_id,
        {
            "scope_version": ctx.version_number,
            "pages": page_rows,
            "referenced_changes": attention,
            "page_errors": errors,
        },
        page_changes,
    )
    svc.events.publish(project_id, "rescan_finished", {"rescan_id": saved.id})
    return saved


def _match(old: SnapshotDTO, new: SnapshotDTO) -> tuple[dict[str, ElementChange], list[str]]:
    return match_page([to_el(e) for e in old.elements], [to_el(e) for e in new.elements])


def _trial_setup(
    page: PageDTO,
    failed_step: int,
    baseline: dict[int, SnapshotDTO],
    results: dict[int, dict[str, Any]],
    changes: dict[int, tuple[dict[str, ElementChange], list[str]]],
) -> dict[str, Any] | None:
    step = page.setup[failed_step - 1]
    if not step.get("locator"):
        return None
    expr = normalise(LocatorSpec.model_validate(step["locator"]).to_python("page"))
    for sid, snap in baseline.items():
        for e in snap.elements:
            if expr not in to_el(e).usable or sid not in changes:
                continue
            change = changes[sid][0].get(e.key)
            new_snap = results[sid]["new"]
            if change is None or change.status != "clear_match" or new_snap is None:
                return None
            new_el = next(x for x in new_snap.elements if x.key == change.new_key)
            spec = _default_spec(new_el)
            if spec is None:
                return None
            setup = [dict(s) for s in page.setup]
            setup[failed_step - 1] = {**setup[failed_step - 1], "locator": spec}
            return {
                "step": failed_step,
                "old_locator": LocatorSpec.model_validate(step["locator"]).to_python("page"),
                "proposed_locator": LocatorSpec.model_validate(spec).to_python("page"),
                "based_on": f"s{sid}.{e.key} -> s{new_snap.id}.{new_el.key} (clear match)",
                "note": "read-only inspection with the proposed locator; nothing was changed",
                "setup": setup,
            }
    return None


def page_summary(
    old: SnapshotDTO,
    new: SnapshotDTO,
    changes: dict[str, ElementChange],
    unmatched: list[str],
    refs: dict[str, Reference],
) -> dict[str, Any]:
    """What changed on one page; referenced elements always listed, others only if changed."""
    new_by_key = {e.key: e for e in new.elements}
    counts = {"unchanged": 0, "clear_match": 0, "ambiguous": 0, "missing": 0}
    items = []
    for e in old.elements:
        old_id = f"s{old.id}.{e.key}"
        change = changes[e.key]
        ref = refs.get(old_id)
        if ref is not None:
            counts[change.status] += 1
        if ref is None and change.status == "unchanged":
            continue
        new_el = new_by_key.get(change.new_key or "")
        items.append(
            {
                "old_id": old_id,
                "old_label": _label(e),
                "old_locator": _shown(e),
                "referenced": ref is not None,
                "used_by": ref.used_by if ref else [],
                "status": change.status,
                "reason": change.reason,
                "text_change": change.text_change,
                "new_id": f"s{new.id}.{new_el.key}" if new_el else None,
                "new_label": _label(new_el) if new_el else "",
                "new_locator": _shown(new_el),
                "candidates": [
                    {
                        "new_id": f"s{new.id}.{c.key}",
                        "label": _label(new_by_key[c.key]),
                        "score": c.score,
                        "locator": _shown(new_by_key[c.key]),
                        "breakdown": c.breakdown,
                    }
                    for c in change.candidates
                ],
            }
        )
    items.sort(key=lambda i: (not i["referenced"], i["status"] == "unchanged", i["old_id"]))
    return {
        "page_url": old.url,
        "html_changed": old.html_sha256 != new.html_sha256,
        "counts": counts,
        "elements": items,
        "appeared": [
            {
                "new_id": f"s{new.id}.{k}",
                "label": _label(new_by_key[k]),
                "locator": _shown(new_by_key[k]),
            }
            for k in unmatched
        ],
    }
