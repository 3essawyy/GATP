"""Convert runner inspection results into store snapshots (api glue, T-007)."""

from __future__ import annotations

from gatp.inspector.models import InspectionResult
from gatp.store.dto import ElementIn, LocatorIn, SnapshotIn


def to_snapshot_in(
    page_id: int, result: InspectionResult, files: dict[str, str], duration_ms: int = 0
) -> SnapshotIn:
    """Map an ``InspectionResult`` (+ artifact paths from the job) to a ``SnapshotIn``."""
    return SnapshotIn(
        page_id=page_id,
        url=result.final_url,
        title=result.title,
        screenshot_path=files.get("screenshot", ""),
        html_path=files.get("html", ""),
        html_sha256=result.html_sha256,
        meta={
            "requested_url": result.url,
            "scope": result.scope.model_dump(),
            "browser_ms": duration_ms,  # runner time, shown apart from model time (REQ-Q8)
        },
        elements=tuple(
            ElementIn(
                key=e.key,
                tag=e.tag,
                role=e.role,
                name=e.name,
                text=e.text,
                attributes=dict(e.attributes),
                bbox=dict(e.bbox),
                fingerprint=dict(e.fingerprint),
                source_line=e.source_line,
                details={
                    "interactive": e.interactive,
                    "label": e.label,
                    "dom_path": e.dom_path,
                    "visible": e.visible,
                    "enabled": e.enabled,
                    "nearby_text": e.nearby_text,
                    "form": e.form,
                    "index_in_form": e.index_in_form,
                    "flags": e.flags,
                    "default_locator": e.default_locator,
                },
                locators=tuple(
                    LocatorIn(
                        rank=c.rank,
                        strategy=c.spec.strategy,
                        expression=c.expression,
                        match_count=c.count,
                        spec={**c.spec.model_dump(), "positional": c.positional},
                        targets_element=c.targets_element,
                    )
                    for c in e.locators
                ),
            )
            for e in result.elements
        ),
    )
