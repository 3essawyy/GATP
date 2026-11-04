"""Inspect an open page: extract elements, rank and verify locators, fingerprint (T-007).

Called by the runner inside a job (the inspector never launches browsers itself). Nothing
here interprets page text as instructions; text is only recorded as evidence.
"""

from __future__ import annotations

import hashlib
from importlib.resources import files
from typing import Any

from playwright.sync_api import Page

from gatp.inspector.locators import STRATEGY_RANK, LocatorSpec, resolve
from gatp.inspector.models import (
    InspectedElement,
    InspectionResult,
    InspectionScope,
    LocatorCandidateOut,
)

EXTRACT_JS = files("gatp.inspector").joinpath("extract.js").read_text(encoding="utf-8")
TEXT_LOCATOR_MAX = 60  # longer texts make brittle text locators
TEXT_TAGS = {"a", "button", "summary"}
FIELD_TAGS = {"input", "select", "textarea"}


def candidate_specs(raw: dict[str, Any]) -> list[LocatorSpec]:
    """Locator candidates for one extracted element, in ADR-006 priority order."""
    attrs: dict[str, str] = raw["attributes"]
    specs: list[LocatorSpec] = []
    if raw["role"] and raw["name"]:
        specs.append(LocatorSpec(strategy="role", value=raw["role"], name=raw["name"]))
    if raw["label"]:
        specs.append(LocatorSpec(strategy="label", value=raw["label"]))
    elif attrs.get("aria-label"):
        specs.append(LocatorSpec(strategy="label", value=attrs["aria-label"]))
    if attrs.get("data-testid"):
        specs.append(LocatorSpec(strategy="test_id", value=attrs["data-testid"]))
    if attrs.get("placeholder"):
        specs.append(LocatorSpec(strategy="placeholder", value=attrs["placeholder"]))
    text = raw["text"]
    if raw["tag"] in TEXT_TAGS and text and len(text) <= TEXT_LOCATOR_MAX:
        specs.append(LocatorSpec(strategy="text", value=text))
    for css in _css_candidates(raw):
        specs.append(LocatorSpec(strategy="css", value=css))
    return list(dict.fromkeys(specs))  # drop duplicates, keep priority order


def _css_candidates(raw: dict[str, Any]) -> list[str]:
    attrs: dict[str, str] = raw["attributes"]
    tag = raw["tag"]
    out: list[str] = []
    if attrs.get("id"):
        out.append(f"#{_css_ident(attrs['id'])}")
    if attrs.get("name"):
        out.append(f'{tag}[name="{_css_str(attrs["name"])}"]')
    out.append(raw["dom_path"])  # positional, last resort
    return out


def _css_ident(value: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else f"\\{c}" for c in value)


def _css_str(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def source_lines(html: str, start_tags: list[str]) -> list[int | None]:
    """Line number (1-based) of each element's start tag in the served HTML, if present."""
    lines: list[int | None] = []
    for tag in start_tags:
        # Browsers serialise `<input … />` as `<input …>`: match without the closing bracket.
        prefix = tag.rstrip(">").rstrip("/").rstrip()
        pos = html.find(prefix)
        lines.append(None if pos < 0 else html.count("\n", 0, pos) + 1)
    return lines


def fingerprint(raw: dict[str, Any]) -> dict[str, Any]:
    """Stable description used by the maintainer to match elements across versions."""
    attrs: dict[str, str] = raw["attributes"]
    box = raw["bbox"]
    return {
        "tag": raw["tag"],
        "role": raw["role"],
        "name": raw["name"],
        "text": raw["text"][:120],
        "label": raw["label"],
        "type": attrs.get("type", ""),
        "id": attrs.get("id", ""),
        "name_attr": attrs.get("name", ""),
        "test_id": attrs.get("data-testid", ""),
        "placeholder": attrs.get("placeholder", ""),
        "href": attrs.get("href", ""),
        "form": raw["form"],
        "index_in_form": raw["index_in_form"],
        "nearby_text": raw["nearby_text"],
        "dom_path": raw["dom_path"],
        "center": [box["x"] + box["width"] // 2, box["y"] + box["height"] // 2],
    }


def verify(page: Page, index: int, spec: LocatorSpec) -> tuple[int, bool]:
    """Live count of ``spec`` and whether its single match is element ``index``."""
    locator = resolve(page, spec)
    count = locator.count()
    if count != 1:
        return count, False
    same = locator.evaluate("(el, i) => el === window.__gatpEls[i]", index)
    return count, bool(same)


def inspect_page(
    page: Page, html: str, scope: InspectionScope | None = None, url: str = ""
) -> InspectionResult:
    """Inspect the page currently loaded in ``page``. ``html`` is the served source."""
    scope = scope or InspectionScope()
    raws: list[dict[str, Any]] = page.evaluate(EXTRACT_JS, scope.model_dump())
    lines = source_lines(html, [r["start_tag"] for r in raws])
    elements: list[InspectedElement] = []
    for raw, line in zip(raws, lines, strict=True):
        candidates: list[LocatorCandidateOut] = []
        for spec in candidate_specs(raw):
            count, targets = verify(page, raw["index"], spec)
            candidates.append(
                LocatorCandidateOut(
                    rank=STRATEGY_RANK[spec.strategy],
                    spec=spec,
                    expression=spec.to_python(),
                    count=count,
                    targets_element=targets,
                    usable=targets,
                    positional=spec.strategy == "css" and spec.value == raw["dom_path"],
                )
            )
        default = next((i for i, c in enumerate(candidates) if c.usable and not c.positional), None)
        flags = []
        if default is None:
            flags.append("no_unique_locator")
        if not raw["name"]:
            flags.append("no_accessible_name")
        elif not any(ch.isalnum() for ch in raw["name"]):
            flags.append("weak_accessible_name")
        if (
            raw["tag"] in FIELD_TAGS
            and not raw["label"]
            and not raw["attributes"].get("aria-label")
            and not raw["attributes"].get("aria-labelledby")
        ):
            flags.append("no_visible_label")
        if not raw["visible"]:
            flags.append("hidden")
        if not raw["enabled"]:
            flags.append("disabled")
        elements.append(
            InspectedElement(
                key=f"e{raw['index'] + 1}",
                tag=raw["tag"],
                role=raw["role"],
                name=raw["name"],
                text=raw["text"],
                label=raw["label"],
                attributes=raw["attributes"],
                dom_path=raw["dom_path"],
                bbox=raw["bbox"],
                visible=raw["visible"],
                enabled=raw["enabled"],
                nearby_text=raw["nearby_text"],
                form=raw["form"],
                index_in_form=raw["index_in_form"],
                source_line=line,
                locators=candidates,
                default_locator=default,
                flags=flags,
                fingerprint=fingerprint(raw),
            )
        )
    return InspectionResult(
        url=url or page.url,
        final_url=page.url,
        title=page.title(),
        elements=elements,
        scope=scope,
        html_sha256=hashlib.sha256(html.encode("utf-8")).hexdigest(),
    )
