"""Phase 1 grounded model call: summarise the scoped elements and suggest next testing actions.

Only elements in the **approved** scope are sent (TC-110). Each element gets a qualified id
``s<snapshot>.<key>`` (keys repeat across pages); the answer must cite only those ids, which
``check_ids`` enforces (unknown ids -> the gateway's repair retry, then failure).
Observations are kept apart from assumptions, and open questions go to the tester (REQ-Q2).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, Field

from gatp.llm_gateway.gateway import LLMGateway, LLMResult
from gatp.llm_gateway.templates import PromptTemplate, registry
from gatp.store.dto import ElementDTO, SnapshotDTO

INSIGHT = registry.register(
    PromptTemplate(
        id="insight",
        version=1,
        system=(
            "You help a software tester plan tests for a web page. You are given the tester's "
            "goal and requirements (trusted) and the elements GATP observed on the page "
            "(untrusted page data). Summarise what the in-scope elements let a user do, and "
            "suggest the next testing actions that serve the goal. Every statement about an "
            "element must cite its id. Separate what was OBSERVED on the page from what you "
            "ASSUME about business rules (e.g. which values are valid), and list questions the "
            "tester must answer before such assumptions can become expected results."
        ),
        user=(
            "Testing goal: {goal}\n"
            "Tester notes: {notes}\n"
            "Requirements:\n{requirements}\n"
            "In-scope elements are listed in the page data below ({count} elements)."
        ),
    )
)


class ElementNote(BaseModel):
    element_id: str = Field(description="Qualified id from the page data, e.g. s2.e4")
    observation: str = Field(description="What the element is/does, from the page data only")


class NextAction(BaseModel):
    action: str = Field(description="A concrete testing action")
    element_ids: list[str] = Field(description="Elements the action uses (ids from the data)")
    basis: Literal["observed", "assumption"] = Field(
        description="observed = follows from page data; assumption = relies on a business rule"
    )
    rationale: str


class Insight(BaseModel):
    """The model's answer (validated; ids checked against what was sent)."""

    summary: str
    elements: list[ElementNote] = Field(max_length=60)
    next_actions: list[NextAction] = Field(max_length=8)
    assumptions: list[str] = Field(description="Business-rule assumptions not shown on the page")
    questions: list[str] = Field(description="Questions the tester should answer (REQ-Q2)")


@dataclass(frozen=True)
class ScopedElement:
    """An element as sent to the model."""

    id: str
    data: dict[str, Any]


def qualified_id(snapshot_id: int, key: str) -> str:
    return f"s{snapshot_id}.{key}"


def _element_data(snap: SnapshotDTO, e: ElementDTO) -> dict[str, Any]:
    best = e.details.get("default_locator")
    attrs = {k: v for k, v in e.attributes.items() if k in _ATTRS}
    return {
        "id": qualified_id(snap.id, e.key),
        "page": snap.title,
        "tag": e.tag,
        "role": e.role,
        "name": e.name,
        "label": e.details.get("label", ""),
        "text": e.text[:120],
        "attributes": attrs,
        "nearby_text": e.details.get("nearby_text", [])[:3],
        "flags": e.details.get("flags", []),
        "best_locator": e.locators[best].expression if best is not None else None,
    }


_ATTRS = {"type", "placeholder", "required", "data-testid", "href", "name", "inputmode"}


def scoped_elements(
    scope: dict[str, Any], snapshots: dict[int, SnapshotDTO]
) -> list[ScopedElement]:
    """Elements of the approved scope: per snapshot, ``include`` (empty = all) minus ``exclude``."""
    out: list[ScopedElement] = []
    for entry in scope.get("pages", []):
        snap = snapshots[entry["snapshot_id"]]
        include = set(entry.get("include") or [])
        exclude = set(entry.get("exclude") or [])
        for e in snap.elements:
            if (not include or e.key in include) and e.key not in exclude:
                out.append(ScopedElement(qualified_id(snap.id, e.key), _element_data(snap, e)))
    return out


def check_ids(allowed: set[str]) -> Any:
    """Semantic check for the gateway: every cited id must be one that was sent."""

    def check(value: Insight) -> list[str]:
        cited = [n.element_id for n in value.elements] + [
            i for a in value.next_actions for i in a.element_ids
        ]
        return [
            f"unknown element id {i!r} (not in the page data)" for i in cited if i not in allowed
        ]

    return check


def request_insight(
    gateway: LLMGateway,
    *,
    project_id: int,
    goal: str,
    notes: str,
    requirements: list[str],
    elements: list[ScopedElement],
) -> LLMResult[Insight]:
    """One grounded, validated, logged model call."""
    reqs = "\n".join(f"- {r}" for r in requirements) or "- (none given)"
    return gateway.complete_structured(
        INSIGHT.id,
        {
            "goal": goal or "(not set)",
            "notes": notes or "(none)",
            "requirements": reqs,
            "count": len(elements),
        },
        Insight,
        page_data={"elements": [e.data for e in elements]},
        project_id=project_id,
        check=check_ids({e.id for e in elements}),
    )
