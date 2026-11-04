"""ORM-level guards that make immutable rows read-only (ADR-005).

SQLite triggers in the initial migration give the same guarantee at the database level, so
even raw SQL cannot rewrite history. These guards fail earlier with a clear Python error.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import event
from sqlalchemy.orm import Mapper

from gatp.store import models


class ImmutableRowError(RuntimeError):
    """Raised when code tries to update or delete an immutable row."""


_IMMUTABLE = (
    models.InspectionSnapshot,
    models.Element,
    models.LocatorCandidate,
    models.ArtifactVersion,
)
_installed = False


def _reject(_mapper: Mapper[Any], _connection: Any, target: Any) -> None:
    raise ImmutableRowError(f"{type(target).__name__} rows are immutable; create a new one")


def install_guards() -> None:
    """Register before_update/before_delete listeners once per process."""
    global _installed
    if _installed:
        return
    for cls in _IMMUTABLE:
        event.listen(cls, "before_update", _reject)
        event.listen(cls, "before_delete", _reject)
    _installed = True
