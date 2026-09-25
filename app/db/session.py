"""Async SQLAlchemy engine for the Supabase transaction pooler (pgbouncer).

The engine is created lazily so the app can still boot (and bind its port / serve
/health) even if the database env vars are not set yet. pgbouncer transaction mode
does not support server-side prepared statements, so we disable asyncpg's statement
cache and give every prepared statement a unique name, and use NullPool because
pgbouncer already pools for us.
"""
from __future__ import annotations

import ssl
import uuid
from collections.abc import AsyncGenerator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def _normalize_database_url(raw: str) -> str:
    if not raw:
        raise RuntimeError(
            "DATABASE_URL is not set. Add it in your host's environment variables "
            "(use the Supabase 'Connection Pooling' / Transaction string, port 6543)."
        )
    url = raw
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]
    # asyncpg does not accept the libpq `sslmode` query param; strip it (SSL via connect_args)
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query) if k.lower() != "sslmode"]
    return urlunsplit(parts._replace(query=urlencode(query)))


def _unique_statement_name() -> str:
    return f"__folio_{uuid.uuid4().hex}__"


def _build_ssl_context() -> ssl.SSLContext:
    """TLS for the Supabase pooler. The pooler presents a Supabase-CA (self-signed
    chain) certificate that isn't in the host trust store, so we encrypt without chain
    verification — equivalent to libpq `sslmode=require`. The traffic is still encrypted."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        connect_args: dict = {
            "statement_cache_size": 0,
            "prepared_statement_name_func": _unique_statement_name,
        }
        if settings.DB_SSL:
            connect_args["ssl"] = _build_ssl_context()
        _engine = create_async_engine(
            _normalize_database_url(settings.DATABASE_URL),
            poolclass=NullPool,
            connect_args=connect_args,
            echo=False,
            future=True,
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _sessionmaker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with get_sessionmaker()() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None
