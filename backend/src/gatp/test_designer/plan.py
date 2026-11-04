"""Collaborative test design (T-012): grounded test plan proposals, validation, clarifications.

The plan is the contract with code generation (T-013): steps are data that refer to inspected
element ids, so the generated code can only use locators the inspector verified (ADR-006).
Expected results carry a ``basis``; assumptions must be confirmed by the tester before G1.
"""

from __future__ import annotations

import json
import re
from typing import Any, Literal

from pydantic import BaseModel, Field

from gatp.llm_gateway.gateway import OFFLINE_EXAMPLES, LLMGateway, LLMResult
from gatp.llm_gateway.providers import ProviderRequest
from gatp.llm_gateway.templates import PromptTemplate, registry
from gatp.test_designer.insight import ScopedElement

Action = Literal["goto", "fill", "click", "select", "check", "uncheck", "press"]
ExpectKind = Literal[
    "visible",
    "hidden",
    "text_equals",
    "text_contains",
    "value_equals",
    "url_contains",
    "count_equals",
    "enabled",
    "disabled",
    "checked",
]
Basis = Literal["requirement", "observation", "assumption"]
NEEDS_VALUE = {"fill", "select", "press", "goto"}
PAGE_LEVEL_KINDS = {"url_contains"}
FILLABLE_ROLES = {"textbox", "searchbox", "spinbutton", "combobox"}
FILLABLE_TAGS = {"input", "textarea"}


class PlanStep(BaseModel):
    action: Action
    element_id: str | None = Field(default=None, description="Interactive element id; not for goto")
    value: str = Field(default="", description="Text to fill, option to select, key, or goto URL")


class Expectation(BaseModel):
    id: str = Field(default="", description="Assigned by GATP; leave empty")
    kind: ExpectKind
    element_id: str | None = Field(default=None, description="Element or region id (not for url_*)")
    value: str = Field(default="", description="Expected text/value/URL part/count")
    basis: Basis
    evidence: str = Field(description="Which requirement, what was observed, or why it is assumed")
    confirmed: bool = Field(default=False, description="Set by the tester, never by the model")


class TestCase(BaseModel):
    id: str = Field(description="TC-01, TC-02, …")
    title: str
    priority: Literal["high", "medium", "low"] = "medium"
    preconditions: list[str] = Field(default_factory=list)
    steps: list[PlanStep] = Field(min_length=1, max_length=30)
    expected: list[Expectation] = Field(min_length=1, max_length=15)
    open_questions: list[str] = Field(default_factory=list)


class TestPlan(BaseModel):
    cases: list[TestCase] = Field(min_length=1, max_length=15)
    notes: str = ""


PLAN_TEMPLATE = registry.register(
    PromptTemplate(
        id="test_plan",
        version=1,
        system=(
            "You design functional UI test cases with a human tester. Use ONLY the pages and "
            "elements in the page data. Rules:\n"
            "- Each case starts with a `goto` step to one of the given page URLs.\n"
            "- Steps act only on elements with interactive=true, by their id. Actions: fill "
            "(text inputs), select (dropdowns), check/uncheck (checkboxes), click, press.\n"
            "- You may choose test input values (e.g. a book title).\n"
            "- Expected results check elements or regions by id (alerts, status, headings are "
            "regions) or the URL. Each has a basis: 'requirement' (stated by the tester; quote "
            "it in evidence), 'observation' (seen in the page data; say what), or 'assumption' "
            "(a business rule you believe but nobody stated; explain). Never present an "
            "assumption as a requirement. Prefer meaningful checks over trivial ones.\n"
            "- Put anything you cannot determine in open_questions."
        ),
        user=(
            "Testing goal: {goal}\n"
            "Tester notes: {notes}\n"
            "Requirements:\n{requirements}\n"
            "Answers the tester already gave:\n{answers}\n"
            "{revision}"
            "Propose a focused test plan for this goal."
        ),
    )
)


def element_index(elements: list[ScopedElement]) -> dict[str, dict[str, Any]]:
    return {e.id: e.data for e in elements}


def validate_plan(
    plan: TestPlan, elements: dict[str, dict[str, Any]], page_urls: set[str]
) -> list[str]:
    """Grounding and consistency errors (empty = valid); used for model output and tester edits."""
    errors: list[str] = []
    seen: set[str] = set()
    for case in plan.cases:
        where = case.id
        if case.id in seen:
            errors.append(f"{where}: duplicate case id")
        seen.add(case.id)
        if case.steps[0].action != "goto":
            errors.append(f"{where}: the first step must be goto a page URL")
        for n, step in enumerate(case.steps, 1):
            errors += _step_errors(f"{where} step {n}", step, elements, page_urls)
        for n, exp in enumerate(case.expected, 1):
            errors += _expectation_errors(f"{where} expected {n}", exp, elements)
    return errors


def _step_errors(
    where: str, step: PlanStep, elements: dict[str, dict[str, Any]], page_urls: set[str]
) -> list[str]:
    if step.action in NEEDS_VALUE and step.action != "goto" and not step.value:
        return [f"{where}: {step.action} needs a value"]
    if step.action == "goto":
        return (
            []
            if step.value in page_urls
            else [f"{where}: goto URL must be one of {sorted(page_urls)}"]
        )
    if step.element_id is None:
        return [f"{where}: {step.action} needs an element_id"]
    el = elements.get(step.element_id)
    if el is None:
        return [f"{where}: unknown element id {step.element_id!r}"]
    if not el.get("interactive", True):
        return [f"{where}: {step.element_id} is a region, not an interactive element"]
    if el.get("best_locator") is None:
        return [f"{where}: {step.element_id} has no unique locator (ask the tester)"]
    role, tag = el.get("role", ""), el.get("tag", "")
    attrs = el.get("attributes", {})
    if step.action == "fill" and not (role in FILLABLE_ROLES or tag in FILLABLE_TAGS):
        return [f"{where}: cannot fill {step.element_id} ({role or tag})"]
    if step.action == "select" and tag != "select":
        return [f"{where}: select needs a <select>, {step.element_id} is {tag}"]
    if step.action in ("check", "uncheck") and not (
        role in ("checkbox", "radio") or attrs.get("type") in ("checkbox", "radio")
    ):
        return [f"{where}: {step.action} needs a checkbox/radio"]
    return []


def _expectation_errors(
    where: str, exp: Expectation, elements: dict[str, dict[str, Any]]
) -> list[str]:
    errors: list[str] = []
    if exp.kind in PAGE_LEVEL_KINDS:
        if not exp.value:
            errors.append(f"{where}: {exp.kind} needs a value")
        return errors
    if exp.element_id is None:
        return [f"{where}: {exp.kind} needs an element_id"]
    el = elements.get(exp.element_id)
    if el is None:
        return [f"{where}: unknown element id {exp.element_id!r}"]
    if el.get("best_locator") is None:
        errors.append(f"{where}: {exp.element_id} has no unique locator (ask the tester)")
    if (
        exp.kind in ("text_equals", "text_contains", "value_equals", "count_equals")
        and not exp.value
    ):
        errors.append(f"{where}: {exp.kind} needs a value")
    if exp.kind == "count_equals" and not exp.value.isdigit():
        errors.append(f"{where}: count_equals needs a whole number")
    if not exp.evidence.strip():
        errors.append(f"{where}: evidence is required")
    return errors


def normalise(plan: TestPlan, previous: TestPlan | None = None) -> TestPlan:
    """Assign stable expectation ids; the model can never set ``confirmed``.

    Expectations that keep their id from ``previous`` keep its confirmation; new ones start
    unconfirmed. Ids look like ``TC-01.x2``.
    """
    prior = {e.id: e for c in (previous.cases if previous else []) for e in c.expected if e.id}
    cases = []
    for case in plan.cases:
        used = {e.id for e in case.expected if e.id.startswith(f"{case.id}.x")}
        counter = 1
        expected = []
        for exp in case.expected:
            eid = exp.id if exp.id.startswith(f"{case.id}.x") else ""
            if not eid:
                while f"{case.id}.x{counter}" in used:
                    counter += 1
                eid = f"{case.id}.x{counter}"
                used.add(eid)
            old = prior.get(eid)
            unchanged = old is not None and old.model_dump(exclude={"confirmed"}) == {
                **exp.model_dump(exclude={"confirmed"}),
                "id": eid,
            }
            expected.append(
                exp.model_copy(
                    update={"id": eid, "confirmed": bool(old and old.confirmed and unchanged)}
                )
            )
        cases.append(case.model_copy(update={"expected": expected}))
    return plan.model_copy(update={"cases": cases})


def unconfirmed_assumptions(plan: TestPlan) -> list[Expectation]:
    return [
        e for c in plan.cases for e in c.expected if e.basis == "assumption" and not e.confirmed
    ]


def describe(exp: Expectation, labels: dict[str, str] | None = None) -> str:
    """Readable form, e.g. ``alert "title-error" (s2.o2) is visible``."""
    target = (labels or {}).get(exp.element_id or "", exp.element_id) or "the page URL"
    verb = {
        "visible": "is visible",
        "hidden": "is hidden",
        "enabled": "is enabled",
        "disabled": "is disabled",
        "checked": "is checked",
        "text_equals": "has the text",
        "text_contains": "contains the text",
        "value_equals": "has the value",
        "url_contains": "contains",
        "count_equals": "has a count of",
    }[exp.kind]
    value = f" {exp.value!r}" if exp.value else ""
    return f"{target} {verb}{value}"


def plan_json(plan: TestPlan) -> str:
    return plan.model_dump_json(indent=2) + "\n"


def propose_plan(
    gateway: LLMGateway,
    *,
    project_id: int,
    goal: str,
    notes: str,
    requirements: list[str],
    answers: list[str],
    elements: list[ScopedElement],
    pages: list[dict[str, str]],
    current: TestPlan | None = None,
    feedback: str = "",
) -> LLMResult[TestPlan]:
    """Ask the model for a (revised) plan; grounding is validated before it is accepted."""
    index = element_index(elements)
    urls = {p["url"] for p in pages}
    revision = ""
    if current is not None:
        revision = (
            "Revise this current plan according to the tester's feedback. Keep expectation ids "
            "for expectations you keep unchanged.\nCurrent plan:\n"
            f"{plan_json(current)}\nTester feedback: {feedback or '(none)'}\n"
        )

    def check(value: TestPlan) -> list[str]:
        return validate_plan(value, index, urls)

    return gateway.complete_structured(
        PLAN_TEMPLATE.id,
        {
            "goal": goal or "(not set)",
            "notes": notes or "(none)",
            "requirements": "\n".join(f"- {r}" for r in requirements) or "- (none given)",
            "answers": "\n".join(f"- {a}" for a in answers) or "- (none yet)",
            "revision": revision,
        },
        TestPlan,
        page_data={"pages": pages, "elements": [e.data for e in elements]},
        project_id=project_id,
        check=check,
    )


# -- offline example (provider "fake"): a small grounded plan built from the page data ------
def _offline_plan(request: ProviderRequest) -> str:
    match = re.search(r"<untrusted_page_data>\n(.*)\n</untrusted_page_data>", request.user, re.S)
    data = json.loads(match.group(1).replace("<\\/untrusted_page_data>", "")) if match else {}
    pages = data.get("pages", [])
    elements = data.get("elements", [])
    cases = []
    for n, page in enumerate(pages, 1):
        on_page = [e for e in elements if e.get("page_url") == page["url"]]
        inputs = [
            e
            for e in on_page
            if e.get("interactive")
            and e.get("best_locator")
            and e.get("tag") in ("input", "textarea")
        ]
        button = next(
            (
                e
                for e in on_page
                if e.get("interactive") and e.get("role") == "button" and e.get("best_locator")
            ),
            None,
        )
        heading = next(
            (e for e in on_page if e.get("role") == "heading" and e.get("best_locator")), None
        )
        alert = next(
            (e for e in on_page if e.get("role") == "alert" and e.get("best_locator")), None
        )
        steps: list[dict[str, Any]] = [{"action": "goto", "value": page["url"]}]
        steps += [{"action": "fill", "element_id": e["id"], "value": "example"} for e in inputs[:2]]
        if button:
            steps.append({"action": "click", "element_id": button["id"]})
        expected: list[dict[str, Any]] = []
        if heading:
            expected.append(
                {
                    "kind": "visible",
                    "element_id": heading["id"],
                    "basis": "observation",
                    "evidence": f"heading '{heading.get('name', '')}' observed on the page",
                }
            )
        if alert:
            expected.append(
                {
                    "kind": "visible",
                    "element_id": alert["id"],
                    "basis": "assumption",
                    "evidence": "assumed: submitting example values shows a message in this region",
                }
            )
        if not expected:
            continue
        cases.append(
            {
                "id": f"TC-{n:02d}",
                "title": f"Offline example for {page.get('title') or page['url']}",
                "priority": "medium",
                "preconditions": [],
                "steps": steps,
                "expected": expected,
                "open_questions": ["Which input values are valid for this form?"] if inputs else [],
            }
        )
    return json.dumps(
        {"cases": cases, "notes": "Offline example (fake provider), not a real model."}
    )


OFFLINE_EXAMPLES[PLAN_TEMPLATE.id] = _offline_plan
