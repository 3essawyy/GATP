"""Alembic environment. The URL comes from the Alembic config set by ``gatp.store.db``."""

from alembic import context
from sqlalchemy import engine_from_config, pool

from gatp.store.models import Base

config = context.config
target_metadata = Base.metadata


def run_migrations() -> None:
    """Run migrations online against the configured URL (render_as_batch for SQLite ALTERs)."""
    connectable = config.attributes.get("connection")
    if connectable is not None:
        context.configure(
            connection=connectable, target_metadata=target_metadata, render_as_batch=True
        )
        with context.begin_transaction():
            context.run_migrations()
        return
    engine = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with engine.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, render_as_batch=True
        )
        with context.begin_transaction():
            context.run_migrations()


run_migrations()
