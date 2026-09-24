"""Async SQLAlchemy engine configured for the Supabase transaction pooler (pgbouncer).

pgbouncer in transaction mode does not support server-side prepared statements, so we
disable asyncpg's statement cache and give every prepared statement a unique name.
We also use NullPool because pgbouncer already pools connections for us.
"""
from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings


def _normalize_database_url(raw: str) -> str:
    if not raw:
        raise RuntimeError("DATABASE_URL is not set")
    url = raw
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]
    # asyncpg does not accept the libpq `sslmode` query param; strip it (SSL handled in connect_args)
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query) if k.lower() != "sslmode"]
    return urlunsplit(parts._replace(query=urlencode(query)))


def _unique_statement_name() -> str:
    return f"__folio_{uuid.uuid4().hex}__"


connect_args: dict = {
    "statement_cache_size": 0,
    "prepared_statement_name_func": _unique_statement_name,
}
if settings.DB_SSL:
    connect_args["ssl"] = True

engine = create_async_engine(
    _normalize_database_url(settings.DATABASE_URL),
    poolclass=NullPool,
    connect_args=connect_args,
    echo=False,
    future=True,
)

SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
