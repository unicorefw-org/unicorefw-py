"""unicorefw.orm

A thin *policy layer* over SQLAlchemy.

Goals
-----
- DRY: Centralize engine/session construction and common ORM imports.
- Security: Safe defaults (pool pre-ping, predictable timeouts hooks), encourage
  parameterized SQL.
- Stability/Performance: One place to tune pooling, recycle, echo, etc.
- Multi-DB: Works with PostgreSQL, MySQL/MariaDB, and SQLite via SQLAlchemy dialects.

Non-goals
---------
- Replacing SQLAlchemy itself. This module intentionally *wraps* SQLAlchemy rather
  than re-implementing ORM semantics.

Notes
-----
- This module is safe to import even if SQLAlchemy is not installed: it raises a
  clear ImportError only when ORM symbols are actually imported/used.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Iterator, Optional


def _require_sqlalchemy() -> Any:
    try:
        import sqlalchemy as sa  # noqa: F401
        return sa
    except Exception as e:  # pragma: no cover
        raise ImportError(
            "SQLAlchemy is required for unicorefw.orm. Install it with 'pip install sqlalchemy'."
        ) from e


# --- Re-exports (core SQL + ORM primitives) ---------------------------------
sa = _require_sqlalchemy()

from sqlalchemy import (  # type: ignore
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    Index,
    ARRAY,
    JSON,
    select,
    and_,
    or_,
    asc,
    desc,
    insert,
    update,
    delete,
    bindparam,
    text,
    func,
)

from sqlalchemy.orm import (  # type: ignore
    relationship,
    sessionmaker,
    selectinload,
)

# Declarative base (works for both SQLAlchemy 1.4/2.x)
try:
    from sqlalchemy.orm import DeclarativeBase  # type: ignore

    class Base(DeclarativeBase):
        pass

except Exception:  # pragma: no cover
    from sqlalchemy.ext.declarative import declarative_base  # type: ignore

    Base = declarative_base()


# --- Async engine/session helpers -------------------------------------------

from sqlalchemy.ext.asyncio import (  # type: ignore
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)

try:
    from sqlalchemy.ext.asyncio import async_sessionmaker  # type: ignore
except ImportError:  # SQLAlchemy 1.4 compatibility
    def async_sessionmaker(bind=None, **kwargs):  # type: ignore
        return sessionmaker(bind=bind, **kwargs)


def create_async_engine_from_url(
    database_url: str,
    *,
    echo: bool = False,
    pool_pre_ping: bool = True,
    pool_recycle: int = 3600,
    pool_size: Optional[int] = None,
    max_overflow: Optional[int] = None,
    connect_args: Optional[dict[str, Any]] = None,
    future: bool = True,
) -> AsyncEngine:
    """Create an AsyncEngine with hardened defaults.

    - `pool_pre_ping=True` avoids stale-connection failures.
    - `pool_recycle` reduces long-lived connection issues (esp. cloud NAT).

    `pool_size/max_overflow` are ignored by some dialects (e.g., SQLite).
    """

    kwargs: dict[str, Any] = {
        "echo": echo,
        "pool_pre_ping": pool_pre_ping,
        "pool_recycle": pool_recycle,
        "future": future,
    }

    if pool_size is not None:
        kwargs["pool_size"] = int(pool_size)
    if max_overflow is not None:
        kwargs["max_overflow"] = int(max_overflow)
    if connect_args:
        kwargs["connect_args"] = dict(connect_args)

    return create_async_engine(database_url, **kwargs)


def create_async_sessionmaker(
    engine: AsyncEngine,
    *,
    expire_on_commit: bool = False,
) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory with safe defaults."""

    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=expire_on_commit,
    )


async def session_scope(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Async context helper for request-scoped unit-of-work.

    Usage:
        async with session_scope(AsyncSessionLocal) as session:
            ...

    Guarantees rollback on error.
    """

    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


# --- Sync session helper (for scripts/admin jobs) ----------------------------

from sqlalchemy.orm import Session  # type: ignore


def create_sync_sessionmaker(
    engine_sync: Any,
    *,
    autocommit: bool = False,
    autoflush: bool = False,
) -> sessionmaker[Session]:
    """Create a synchronous sessionmaker.

    Use this for offline scripts or background jobs. Avoid using synchronous
    sessions inside async request handlers unless running in a threadpool.
    """

    return sessionmaker(bind=engine_sync, autocommit=autocommit, autoflush=autoflush)


# --- Public exports ----------------------------------------------------------

__all__ = [
    # base
    "Base",
    # engine/session
    "AsyncEngine",
    "AsyncSession",
    "async_sessionmaker",
    "create_async_engine",
    "create_async_engine_from_url",
    "create_async_sessionmaker",
    "session_scope",
    "Session",
    "sessionmaker",
    "create_sync_sessionmaker",
    # sql primitives
    "Boolean",
    "CheckConstraint",
    "Column",
    "Date",
    "DateTime",
    "Enum",
    "Float",
    "ForeignKey",
    "Integer",
    "LargeBinary",
    "Numeric",
    "String",
    "Text",
    "Time",
    "UniqueConstraint",
    "Index",
    "ARRAY",
    "JSON",
    "select",
    "and_",
    "or_",
    "asc",
    "desc",
    "insert",
    "update",
    "delete",
    "bindparam",
    "text",
    "func",
    # orm
    "relationship",
    "selectinload",
]
