"""TC-104: schema creation, migrations and database-level immutability."""

from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

from gatp.config import Settings
from gatp.store.db import Database
from gatp.store.models import IMMUTABLE_TABLES, Base


def test_fresh_database_created_on_first_run(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "data")
    db = Database.from_settings(settings)
    db.migrate()
    assert (tmp_path / "data" / "gatp.sqlite").exists()
    tables = sa.inspect(db.engine).get_table_names()
    assert {"projects", "artifact_versions", "llm_calls", "alembic_version"} <= set(tables)


def test_migrate_is_idempotent(db: Database) -> None:
    db.migrate()  # second run is a no-op


def test_models_match_migrations(db: Database) -> None:
    """Fails if someone changes models.py without adding an Alembic migration."""
    with db.engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    assert diff == []


@pytest.mark.parametrize("table", IMMUTABLE_TABLES)
@pytest.mark.parametrize("action", ["UPDATE", "DELETE"])
def test_triggers_block_raw_sql_changes(db: Database, table: str, action: str) -> None:
    with db.engine.connect() as conn:
        triggers = {
            row[0]
            for row in conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='trigger'"))
        }
    assert f"{table}_no_{action.lower()}" in triggers


def test_migrate_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from gatp.config import get_settings
    from gatp.store import migrate

    monkeypatch.setenv("GATP_DATA_DIR", str(tmp_path / "d"))
    get_settings.cache_clear()
    try:
        assert migrate.main(["upgrade"]) == 0
        assert (tmp_path / "d" / "gatp.sqlite").exists()
        assert migrate.main(["bogus"]) == 2
    finally:
        get_settings.cache_clear()
