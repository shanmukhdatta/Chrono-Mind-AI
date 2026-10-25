"""Explicit Alembic schema management; no implicit migration on app startup."""
import os

from dotenv import load_dotenv
load_dotenv(override=False)
from logging.config import fileConfig
from alembic import context
from sqlalchemy import create_engine, engine_from_config, pool
from v2.models import Base

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata


def database_url():
    url = os.getenv("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL required for Alembic")
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[11:]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[13:]
    return url


def offline():
    context.configure(url=database_url(), target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def online():
    connectable = create_engine(database_url(), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    offline()
else:
    online()
