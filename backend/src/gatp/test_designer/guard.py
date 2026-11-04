"""Assertion-weakening guard for test plan revisions (T-015, ADR-023).

A revision (by the model or a tester edit) is compared with the last **approved** (G1) plan.
Every expected result that was removed or changed, and every removed case, becomes a finding.
GATP turns each finding into a clarification that blocks G1 until the tester explicitly
accepts the change or restores the original, so weakening is never silent (REQ-Q3).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from gatp.test_designer.plan import Expectation, TestCase, TestPlan, describe

# Pairs (old kind -> new kind) that make a check strictly weaker.
LOOSER = {
    ("text_equals", "text_contains"),
    ("text_equals", "visible"),
    ("text_contains", "visible"),
    ("value_equals", "visible"),
    ("value_equals", "enabled"),
    ("count_equals", "visible"),
    ("checked", "visible"),
    ("disabled", "visible"),
    ("enabled", "visible"),
}


@dataclass(frozen=True)
class Weakening:
    key: str  # stable id of this exact change, e.g. "TC-01.x2:removed"
    case_id: str
    expectation_id: str | None  # None when the whole case was removed
    change: str  # removed | loosened | changed | case_removed
    message: str
    original: dict[str, Any] = field(default_factory=dict)  # the approved case/expectation


def _signature(e: Expectation) -> str:
    return f"{e.kind}|{e.element_id or ''}|{e.value}"


def plan_weakenings(
    approved: TestPlan, revised: TestPlan, labels: dict[str, str] | None = None
) -> list[Weakening]:
    """What ``revised`` drops or changes compared with the ``approved`` plan."""
    out: list[Weakening] = []
    new_cases = {c.id: c for c in revised.cases}
    for case in approved.cases:
        new = new_cases.get(case.id)
        if new is None:
            checks = "; ".join(describe(e, labels) for e in case.expected)
            out.append(
                Weakening(
                    key=f"{case.id}:case_removed",
                    case_id=case.id,
                    expectation_id=None,
                    change="case_removed",
                    message=f"{case.id} ({case.title}) was removed with its checks: {checks}",
                    original=case.model_dump(),
                )
            )
            continue
        new_exp = {e.id: e for e in new.expected}
        same_checks = {_signature(e) for e in new.expected}
        for exp in case.expected:
            after = new_exp.get(exp.id)
            if after is None and _signature(exp) in same_checks:
                continue  # the same check is still there (under another id)
            if after is None:
                out.append(
                    Weakening(
                        key=f"{exp.id}:removed",
                        case_id=case.id,
                        expectation_id=exp.id,
                        change="removed",
                        message=f"{exp.id} was removed: {describe(exp, labels)}",
                        original=exp.model_dump(),
                    )
                )
            elif _signature(after) != _signature(exp):
                change = "loosened" if (exp.kind, after.kind) in LOOSER else "changed"
                out.append(
                    Weakening(
                        key=f"{exp.id}:{change}:{_signature(after)}",
                        case_id=case.id,
                        expectation_id=exp.id,
                        change=change,
                        message=(
                            f"{exp.id} was {change}: {describe(exp, labels)} "
                            f"-> {describe(after, labels)}"
                        ),
                        original=exp.model_dump(),
                    )
                )
    return out


def restore(plan: TestPlan, weakening: Weakening) -> TestPlan:
    """Put the approved case / expectation back into ``plan`` (the tester chose to restore)."""
    if weakening.change == "case_removed":
        if any(c.id == weakening.case_id for c in plan.cases):
            return plan
        return plan.model_copy(
            update={"cases": [*plan.cases, TestCase.model_validate(weakening.original)]}
        )
    original = Expectation.model_validate(weakening.original)
    cases = []
    for case in plan.cases:
        if case.id == weakening.case_id:
            kept = [e for e in case.expected if e.id != original.id]
            index = next((i for i, e in enumerate(case.expected) if e.id == original.id), len(kept))
            kept.insert(index, original)
            case = case.model_copy(update={"expected": kept})
        cases.append(case)
    return plan.model_copy(update={"cases": cases})
