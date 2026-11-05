"""Match elements of an old snapshot to a new one and classify changes (T-016, ADR-007, ADR-024).

Deterministic and explainable; the model is never asked which element matches.

1. **Unchanged:** the old element's default locator is still a usable (unique, verified)
   candidate of some new element.
2. Every other old element is scored against the elements that **appeared** (new elements
   that did not keep an old locator) with a weighted fingerprint similarity.
3. Classification:
   - **clear_match:** best score >= ``CLEAR``, ahead of the runner-up by >= ``MARGIN``, and the
     only plausible replacement (no "split": two appeared elements of the same role in the
     same form, e.g. Save -> Save draft + Publish);
   - **ambiguous:** some candidate >= ``FLOOR`` but not clear: the tester decides;
   - **missing:** nothing >= ``FLOOR``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any

# Weights of fingerprint fields (sum 1.0). Exact-match fields vs. fuzzy text fields.
WEIGHTS: dict[str, float] = {
    "role": 0.14,
    "tag": 0.04,
    "type": 0.06,
    "name": 0.16,
    "label": 0.06,
    "test_id": 0.12,
    "id": 0.10,
    "name_attr": 0.06,
    "placeholder": 0.04,
    "href": 0.04,
    "form": 0.06,
    "index_in_form": 0.04,
    "nearby_text": 0.04,
    "dom_path": 0.02,
    "center": 0.02,
}
EXACT = {"role", "tag", "type", "form", "id", "name_attr"}
CLEAR = 0.70
MARGIN = 0.15
FLOOR = 0.45


@dataclass(frozen=True)
class El:
    """What matching needs to know about one element of a snapshot."""

    key: str  # e3 / o2
    interactive: bool
    fingerprint: dict[str, Any]
    usable: tuple[str, ...]  # expressions of unique, verified candidates
    default: str  # default locator expression ("" if none)

    @property
    def label(self) -> str:
        fp = self.fingerprint
        return f'{fp.get("role") or fp.get("tag")} "{fp.get("name") or fp.get("id") or self.key}"'


@dataclass(frozen=True)
class Candidate:
    key: str
    score: float
    breakdown: list[dict[str, Any]]
    default: str


@dataclass
class ElementChange:
    old_key: str
    status: str  # unchanged | clear_match | ambiguous | missing
    new_key: str | None = None
    reason: str = ""
    candidates: list[Candidate] = field(default_factory=list)
    text_change: str = ""  # e.g. name 'Sign in' -> 'Log in' while the locator still works


def _text(a: Any, b: Any) -> float | None:
    a, b = str(a or "").strip().lower(), str(b or "").strip().lower()
    if not a and not b:
        return None
    return 1.0 if a == b else SequenceMatcher(None, a, b).ratio()


def field_similarity(name: str, old: Any, new: Any) -> float | None:
    """Similarity 0..1 of one fingerprint field, or None when neither side has a value."""
    if name == "center":
        if not old or not new:
            return None
        dist = ((old[0] - new[0]) ** 2 + (old[1] - new[1]) ** 2) ** 0.5
        return float(max(0.0, 1.0 - dist / 300))
    if name == "index_in_form":
        if old in (None, -1) and new in (None, -1):
            return None
        if old == new:
            return 1.0
        return 0.5 if isinstance(old, int) and isinstance(new, int) and abs(old - new) == 1 else 0.0
    if name in EXACT:
        if not old and not new:
            return None
        return 1.0 if old == new else 0.0
    return _text(old, new)


def score(old: dict[str, Any], new: dict[str, Any]) -> tuple[float, list[dict[str, Any]]]:
    """Weighted similarity over the fields present on either side, with its breakdown."""
    total = weight = 0.0
    breakdown = []
    for name, w in WEIGHTS.items():
        sim = field_similarity(name, old.get(name), new.get(name))
        if sim is None:
            continue
        total += w * sim
        weight += w
        breakdown.append(
            {"field": name, "old": old.get(name), "new": new.get(name), "similarity": round(sim, 2)}
        )
    return (round(total / weight, 3) if weight else 0.0), breakdown


def match_page(old: list[El], new: list[El]) -> tuple[dict[str, ElementChange], list[str]]:
    """Classify every old element; also return keys of new elements that matched nothing."""
    by_expression: dict[str, El] = {}
    for n in new:
        for expression in n.usable:
            by_expression.setdefault(expression, n)
    changes: dict[str, ElementChange] = {}
    kept: set[str] = set()
    for o in old:
        same = by_expression.get(o.default) if o.default else None
        if same is not None and same.interactive == o.interactive:
            kept.add(same.key)
            change = ElementChange(o.key, "unchanged", same.key, "default locator still unique")
            old_name, new_name = o.fingerprint.get("name", ""), same.fingerprint.get("name", "")
            if old_name != new_name:
                change.text_change = f"name {old_name!r} -> {new_name!r}"
            changes[o.key] = change
    appeared = [n for n in new if n.key not in kept]
    claimed: set[str] = set()
    for o in old:
        if o.key in changes:
            continue
        pool = [n for n in appeared if n.interactive == o.interactive]
        ranked = sorted(
            (Candidate(n.key, *score(o.fingerprint, n.fingerprint), n.default) for n in pool),
            key=lambda c: c.score,
            reverse=True,
        )
        changes[o.key] = classify(o, ranked, {n.key: n for n in pool})
        if changes[o.key].status == "clear_match" and changes[o.key].new_key:
            claimed.add(str(changes[o.key].new_key))
    unmatched = [n.key for n in appeared if n.key not in claimed]
    return changes, unmatched


def classify(old: El, ranked: list[Candidate], pool: dict[str, El]) -> ElementChange:
    top = ranked[:3]
    plausible = [c for c in ranked if c.score >= FLOOR]
    if not plausible:
        hint = f" (best {ranked[0].score:.2f})" if ranked else ""
        return ElementChange(old.key, "missing", None, f"no candidate scores >= {FLOOR}{hint}", top)
    best = plausible[0]
    runner_up = plausible[1].score if len(plausible) > 1 else 0.0
    fp = old.fingerprint
    split = [
        c
        for c in plausible
        if pool[c.key].fingerprint.get("role") == fp.get("role")
        and pool[c.key].fingerprint.get("form") == fp.get("form")
    ]
    if len(split) >= 2:
        names = ", ".join(pool[c.key].label for c in split)
        return ElementChange(
            old.key,
            "ambiguous",
            None,
            f"{len(split)} similar new elements replace it: {names}",
            top,
        )
    if best.score >= CLEAR and best.score - runner_up >= MARGIN:
        return ElementChange(
            old.key,
            "clear_match",
            best.key,
            f"score {best.score:.2f}, ahead of the next candidate by {best.score - runner_up:.2f}",
            top,
        )
    return ElementChange(
        old.key,
        "ambiguous",
        None,
        f"best score {best.score:.2f} (clear needs >= {CLEAR} and a margin >= {MARGIN})",
        top,
    )
