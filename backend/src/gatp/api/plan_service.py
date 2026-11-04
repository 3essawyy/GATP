"""Test plan lifecycle: store versions, keep clarifications in sync, apply tester answers (T-012).

Every assumption-based expected result that is not confirmed gets a clarification on step
``plan``; open clarifications block G1 (HLD §4). Answers change the plan as a **new version**.
"""

from __future__ import annotations

from typing import Any

from gatp.api.guard_sync import KIND as WEAKENING
from gatp.api.guard_sync import RESTORE, approved_baseline, sync_weakenings
from gatp.api.services import Services
from gatp.store.dto import VersionDTO
from gatp.store.gates import ClarificationDTO
from gatp.test_designer.guard import Weakening, plan_weakenings, restore
from gatp.test_designer.plan import (
    TestPlan,
    describe,
    normalise,
    plan_json,
    unconfirmed_assumptions,
)

PLAN_NAME = "test plan"
CONFIRM = "Confirm"
REMOVE = "Remove this expectation"


def current_plan(svc: Services, project_id: int) -> tuple[int, VersionDTO, TestPlan] | None:
    artifact = svc.artifacts.find(project_id, "test_plan", PLAN_NAME)
    if artifact is None:
        return None
    version = svc.artifacts.latest(artifact.id)
    return artifact.id, version, TestPlan.model_validate_json(version.content)


def store_plan(
    svc: Services, project_id: int, plan: TestPlan, author: str, reason: str
) -> tuple[int, VersionDTO, TestPlan]:
    """Normalise ids against the previous version, append a version, sync clarifications."""
    existing = current_plan(svc, project_id)
    plan = normalise(plan, existing[2] if existing else None)
    content = plan_json(plan)
    if existing is None:
        artifact, version = svc.artifacts.create_artifact(
            project_id, "test_plan", PLAN_NAME, content, author, reason
        )
        artifact_id = artifact.id
    else:
        artifact_id = existing[0]
        version = existing[1]
        if version.content != content:
            version = svc.artifacts.new_version(artifact_id, content, author, reason)
    sync_clarifications(svc, project_id, plan)
    sync_plan_weakenings(svc, project_id, artifact_id, plan)
    svc.events.publish(project_id, "artifact_changed", {"artifact_id": artifact_id})
    return artifact_id, version, plan


def element_labels(svc: Services, project_id: int) -> dict[str, str]:
    """Human-readable names for element ids of the approved scope (for questions and the UI)."""
    from gatp.api.context import approved_scope  # local: context imports workflow

    try:
        ctx = approved_scope(svc, project_id)
    except Exception:
        return {}
    labels = {}
    for e in ctx.elements:
        d = e.data
        name = d.get("name") or d.get("attributes", {}).get("id", "")
        labels[e.id] = f'{d.get("role") or d.get("tag")} "{name}" ({e.id})'
    return labels


def sync_clarifications(svc: Services, project_id: int, plan: TestPlan) -> None:
    """One open clarification per unconfirmed assumption and per new open question."""
    labels = element_labels(svc, project_id)
    pending = {e.id: (c.id, e) for c in plan.cases for e in unconfirmed_assumptions_of(c)}
    questions = {(c.id, q) for c in plan.cases for q in c.open_questions}
    existing = svc.gates.clarifications(project_id, step="plan")
    open_by_exp = {
        c.evidence.get("expectation_id"): c
        for c in existing
        if c.status == "open" and c.kind == "assumption"
    }
    for exp_id, clar in open_by_exp.items():
        if exp_id not in pending:
            svc.gates.resolve(
                clar.id, "superseded", "expectation changed or removed in a newer plan version"
            )
    for exp_id, (case_id, exp) in pending.items():
        if exp_id in open_by_exp:
            continue
        svc.gates.raise_clarification(
            project_id,
            "plan",
            "assumption",
            f"{case_id}: GATP assumes that {describe(exp, labels)}. "
            f"Reason: {exp.evidence.rstrip('.')}. Is this the expected behaviour?",
            evidence={
                "expectation_id": exp_id,
                "case_id": case_id,
                "expectation": exp.model_dump(),
            },
            options=[CONFIRM, REMOVE],
        )
    asked = {(c.evidence.get("case_id"), c.question) for c in existing if c.kind == "question"}
    for case_id, question in sorted(questions):
        if (case_id, question) not in asked:
            svc.gates.raise_clarification(
                project_id, "plan", "question", question, evidence={"case_id": case_id}
            )


def unconfirmed_assumptions_of(case: Any) -> list[Any]:
    return [e for e in case.expected if e.basis == "assumption" and not e.confirmed]


def sync_plan_weakenings(svc: Services, project_id: int, artifact_id: int, plan: TestPlan) -> None:
    """Flag what this plan drops or changes compared with the last G1-approved version."""
    baseline = approved_baseline(svc, artifact_id, "G1")
    findings: dict[str, tuple[str, dict[str, Any]]] = {}
    if baseline is not None:
        approved = TestPlan.model_validate_json(baseline.content)
        for w in plan_weakenings(approved, plan, element_labels(svc, project_id)):
            question = (
                f"{w.message}. This weakens what the approved plan (v{baseline.number}) checks: "
                "accept the change, or restore the approved check?"
            )
            findings[w.key] = (
                question,
                {
                    "change": w.change,
                    "case_id": w.case_id,
                    "expectation_id": w.expectation_id,
                    "original": w.original,
                    "baseline_version_id": baseline.id,
                },
            )
    sync_weakenings(svc, project_id, "plan", findings)


def apply_answer(svc: Services, clarification: ClarificationDTO) -> None:
    """Turn the tester's answer to an assumption into a new plan version."""
    if clarification.step == "plan" and clarification.kind == WEAKENING:
        _apply_weakening_answer(svc, clarification)
        return
    if clarification.step != "plan" or clarification.kind != "assumption":
        return
    found = current_plan(svc, clarification.project_id)
    if found is None:
        return
    _, _, plan = found
    exp_id = clarification.evidence.get("expectation_id")
    answer = clarification.answer
    cases = []
    for case in plan.cases:
        expected = []
        for exp in case.expected:
            if exp.id != exp_id:
                expected.append(exp)
            elif answer == CONFIRM:
                expected.append(exp.model_copy(update={"confirmed": True}))
            elif answer == REMOVE:
                continue
            else:  # the tester stated the correct expected value
                expected.append(
                    exp.model_copy(
                        update={
                            "value": answer,
                            "basis": "requirement",
                            "evidence": f"stated by {clarification.answered_by}: {answer}",
                            "confirmed": True,
                        }
                    )
                )
        if expected:
            cases.append(case.model_copy(update={"expected": expected}))
    if not cases:
        return
    updated = plan.model_copy(update={"cases": cases})
    # normalise() keeps confirmations only for unchanged expectations: set them after it.
    store_confirmed(svc, clarification, updated)


def store_confirmed(svc: Services, clarification: ClarificationDTO, plan: TestPlan) -> None:
    existing = current_plan(svc, clarification.project_id)
    if existing is None:
        return
    artifact_id, _, _ = existing
    content = plan_json(plan)
    svc.artifacts.new_version(
        artifact_id,
        content,
        "user",
        f"clarification #{clarification.id} answered by {clarification.answered_by}: "
        f"{clarification.answer}",
    )
    sync_clarifications(svc, clarification.project_id, plan)
    sync_plan_weakenings(svc, clarification.project_id, artifact_id, plan)
    svc.events.publish(clarification.project_id, "artifact_changed", {"artifact_id": artifact_id})


def _apply_weakening_answer(svc: Services, clarification: ClarificationDTO) -> None:
    """Accept: nothing to change (the answer is the record). Restore: put the check back."""
    if clarification.answer != RESTORE:
        return
    found = current_plan(svc, clarification.project_id)
    if found is None:
        return
    ev = clarification.evidence
    weakening = Weakening(
        key=str(ev.get("key")),
        case_id=str(ev.get("case_id")),
        expectation_id=ev.get("expectation_id"),
        change=str(ev.get("change")),
        message="",
        original=dict(ev.get("original") or {}),
    )
    store_confirmed(svc, clarification, restore(found[2], weakening))


def plan_blockers(plan: TestPlan) -> list[str]:
    """Reasons the plan cannot be approved yet (besides open clarifications)."""
    return [f"{e.id} is an unconfirmed assumption" for e in unconfirmed_assumptions(plan)]
