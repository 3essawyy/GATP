"""Schema migration CLI.

``uv run poe db-upgrade`` applies all migrations (the API also does this on startup).
``uv run poe db-revision "add runs.retries"`` autogenerates a new migration from models.py.
"""

from __future__ import annotations

import sys

from alembic import command

from gatp.store.db import Database, alembic_config


def main(argv: list[str] | None = None) -> int:
    """Dispatch ``upgrade`` or ``revision <message>``."""
    args = sys.argv[1:] if argv is None else argv
    db = Database.from_settings()
    if args == ["upgrade"]:
        db.migrate()
        print(f"database at head: {db.url}")
        return 0
    if len(args) == 2 and args[0] == "revision":
        db.migrate()
        command.revision(alembic_config(db.url), message=args[1], autogenerate=True)
        return 0
    print('usage: python -m gatp.store.migrate upgrade | revision "<message>"', file=sys.stderr)
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
