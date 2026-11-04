"""Engine, sessions and schema migration (ADR-005, ADR-015).

``Database`` owns one SQLAlchemy engine. ``Database.migrate()`` runs Alembic to ``head``,
so a fresh database is created automatically on first run and older ones are upgraded.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from gatp.config import Settings, get_settings
from gatp.store.immutability import install_guards

MIGRATIONS = "gatp.store:migrations"


def alembic_config(url: str) -> Config:
    """Alembic config pointing at the packaged migrations and the given database URL."""
    cfg = Config()
    cfg.set_main_option("script_location", MIGRATIONS)
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def _sqlite_pragmas(dbapi_connection: Any, _record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


class Database:
    """Connection + session factory for the GATP store."""

    def __init__(self, url: str) -> None:
        self.url = url
        if url.startswith("sqlite:///"):
            Path(url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
        self.engine: Engine = create_engine(url, connect_args={"check_same_thread": False})
        if url.startswith("sqlite"):
            event.listen(self.engine, "connect", _sqlite_pragmas)
        self._sessions = sessionmaker(self.engine, expire_on_commit=False)
        install_guards()

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> Database:
        """Database configured from ``GATP_*`` settings."""
        return cls((settings or get_settings()).resolved_database_url())

    def migrate(self) -> None:
        """Create or upgrade the schema to the latest migration."""
        cfg = alembic_config(self.url)
        with self.engine.begin() as connection:
            cfg.attributes["connection"] = connection
            command.upgrade(cfg, "head")

    @contextmanager
    def session(self) -> Iterator[Session]:
        """A unit of work: commits on success, rolls back on error."""
        s = self._sessions()
        try:
            yield s
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()
