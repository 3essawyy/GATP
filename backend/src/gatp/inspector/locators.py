"""Structured locator specs (ADR-006).

Locators travel between modules as data (``LocatorSpec``), never as code strings to evaluate.
``resolve`` turns a spec into a Playwright locator; ``to_python`` renders the equivalent
Playwright Python expression for display and for generated page objects.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

Strategy = Literal["role", "label", "test_id", "placeholder", "text", "css"]
STRATEGY_RANK: dict[str, int] = {
    "role": 1,
    "label": 2,
    "test_id": 3,
    "placeholder": 4,
    "text": 5,
    "css": 6,
}


class LocatorSpec(BaseModel):
    """One locator. ``value`` is the role / label / test id / placeholder / text / CSS."""

    model_config = ConfigDict(frozen=True)

    strategy: Strategy
    value: str
    name: str | None = None  # accessible name, only for strategy == "role"
    exact: bool = True

    def to_python(self, page_var: str = "page") -> str:
        """Equivalent Playwright Python expression, e.g. ``page.get_by_role("button")``."""
        v = _q(self.value)
        if self.strategy == "role":
            args = v
            if self.name is not None:
                args += f", name={_q(self.name)}"
                if self.exact:
                    args += ", exact=True"
            return f"{page_var}.get_by_role({args})"
        if self.strategy == "css":
            return f"{page_var}.locator({v})"
        method = {
            "label": "get_by_label",
            "test_id": "get_by_test_id",
            "placeholder": "get_by_placeholder",
            "text": "get_by_text",
        }[self.strategy]
        exact = ", exact=True" if self.exact and self.strategy != "test_id" else ""
        return f"{page_var}.{method}({v}{exact})"


def resolve(page: Any, spec: LocatorSpec) -> Any:
    """Build the Playwright ``Locator`` for ``spec`` on ``page`` (sync API)."""
    if spec.strategy == "role":
        if spec.name is None:
            return page.get_by_role(spec.value)
        return page.get_by_role(spec.value, name=spec.name, exact=spec.exact)
    if spec.strategy == "label":
        return page.get_by_label(spec.value, exact=spec.exact)
    if spec.strategy == "test_id":
        return page.get_by_test_id(spec.value)
    if spec.strategy == "placeholder":
        return page.get_by_placeholder(spec.value, exact=spec.exact)
    if spec.strategy == "text":
        return page.get_by_text(spec.value, exact=spec.exact)
    return page.locator(spec.value)


def _q(text: str) -> str:
    """Python string literal with double quotes."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
