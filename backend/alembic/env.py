"""Alembic environment.

Foundation rules baked in here:
  * The migration URL comes from MIGRATION_DATABASE_URL (the DDL/migration role), never hard-coded.
  * A strict naming_convention enforces deterministic index/constraint/FK/PK names.
  * Autogenerate is NOT relied upon for RLS policies, functions, partial indexes, or grants —
    those are written by hand with op.execute (see docs/guides/migrations.md).
  * target_metadata is None until S2 wires the SQLAlchemy models (Base.metadata).
"""
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, MetaData
from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Migration/DDL connection — uses the migration role, not the runtime app role.
DATABASE_URL = os.getenv("MIGRATION_DATABASE_URL") or os.getenv("DATABASE_URL")
if DATABASE_URL:
    config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Deterministic naming for all constraints/indexes (matches the naming-conventions doc).
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# S2 will replace this with the application's Base.metadata for autogenerate.
target_metadata = MetaData(naming_convention=NAMING_CONVENTION)


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
