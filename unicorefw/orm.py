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

from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

SQLALCHEMY_AVAILABLE = False
_SQLALCHEMY_IMPORT_ERROR: BaseException | None = None
_MISSING_SQLALCHEMY_MESSAGE = (
    "SQLAlchemy is required for unicorefw.orm. Install it with "
    "'pip install unicorefw[orm]'."
)


class ORMUnavailableError(ImportError):
    """Raised when the optional SQLAlchemy backend is unavailable."""


def _require_sqlalchemy() -> Any:
    try:
        import sqlalchemy as sa
        return sa
    except ImportError as exc:
        raise ORMUnavailableError(_MISSING_SQLALCHEMY_MESSAGE) from exc


class _MissingSQLAlchemySymbol:
    """Lazy placeholder for optional SQLAlchemy re-exports."""

    def __init__(self, name: str):
        self.__name__ = name

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        raise ORMUnavailableError(
            _MISSING_SQLALCHEMY_MESSAGE
        ) from _SQLALCHEMY_IMPORT_ERROR

    def __getattr__(self, item: str) -> Any:
        raise ORMUnavailableError(
            _MISSING_SQLALCHEMY_MESSAGE
        ) from _SQLALCHEMY_IMPORT_ERROR

    def __repr__(self) -> str:
        return f"<missing SQLAlchemy symbol {self.__name__!r}>"


def _missing_symbol(name: str) -> _MissingSQLAlchemySymbol:
    return _MissingSQLAlchemySymbol(name)


# --- Re-exports (core SQL + ORM primitives) ---------------------------------
try:
    sa = _require_sqlalchemy()
    SQLALCHEMY_AVAILABLE = True

    from sqlalchemy import (  # type: ignore
        ARRAY,
        JSON,
        Boolean,
        CheckConstraint,
        Column,
        Date,
        DateTime,
        Enum,
        Float,
        ForeignKey,
        Index,
        Integer,
        LargeBinary,
        Numeric,
        String,
        Text,
        Time,
        UniqueConstraint,
        and_,
        asc,
        bindparam,
        delete,
        desc,
        func,
        insert,
        or_,
        select,
        text,
        update,
    )
    from sqlalchemy.orm import (  # type: ignore
        Session,
        relationship,
        selectinload,
        sessionmaker,
    )

    # Declarative base (works for both SQLAlchemy 1.4/2.x)
    try:
        from sqlalchemy.orm import DeclarativeBase  # type: ignore

        class Base(DeclarativeBase):
            pass

    except ImportError:
        from sqlalchemy.orm import declarative_base  # type: ignore

        Base = declarative_base()

    # --- Async engine/session helpers ---------------------------------------

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

except ImportError as exc:
    _SQLALCHEMY_IMPORT_ERROR = exc
    sa = None
    Base = _missing_symbol("Base") # type: ignore
    AsyncEngine = _missing_symbol("AsyncEngine")
    AsyncSession = _missing_symbol("AsyncSession")
    Session = _missing_symbol("Session")
    async_sessionmaker = _missing_symbol("async_sessionmaker")
    create_async_engine = _missing_symbol("create_async_engine")
    sessionmaker = _missing_symbol("sessionmaker")

    Boolean = _missing_symbol("Boolean")
    CheckConstraint = _missing_symbol("CheckConstraint")
    Column = _missing_symbol("Column")
    Date = _missing_symbol("Date")
    DateTime = _missing_symbol("DateTime")
    Enum = _missing_symbol("Enum")
    Float = _missing_symbol("Float")
    ForeignKey = _missing_symbol("ForeignKey")
    Integer = _missing_symbol("Integer")
    LargeBinary = _missing_symbol("LargeBinary")
    Numeric = _missing_symbol("Numeric")
    String = _missing_symbol("String")
    Text = _missing_symbol("Text")
    Time = _missing_symbol("Time")
    UniqueConstraint = _missing_symbol("UniqueConstraint")
    Index = _missing_symbol("Index")
    ARRAY = _missing_symbol("ARRAY")
    JSON = _missing_symbol("JSON")
    select = _missing_symbol("select")
    and_ = _missing_symbol("and_")
    or_ = _missing_symbol("or_")
    asc = _missing_symbol("asc")
    desc = _missing_symbol("desc")
    insert = _missing_symbol("insert")
    update = _missing_symbol("update")
    delete = _missing_symbol("delete")
    bindparam = _missing_symbol("bindparam")
    text = _missing_symbol("text")
    func = _missing_symbol("func")
    relationship = _missing_symbol("relationship")
    selectinload = _missing_symbol("selectinload")


def create_async_engine_from_url(
    database_url: str,
    *,
    echo: bool = False,
    pool_pre_ping: bool = True,
    pool_recycle: int = 3600,
    pool_size: int | None = None,
    max_overflow: int | None = None,
    connect_args: dict[str, Any] | None = None,
    future: bool = True,
) -> AsyncEngine: # type: ignore
    """Create an AsyncEngine with hardened defaults.

    - `pool_pre_ping=True` avoids stale-connection failures.
    - `pool_recycle` reduces long-lived connection issues (esp. cloud NAT).

    `pool_size/max_overflow` are ignored by some dialects (e.g., SQLite).
    """
    _require_sqlalchemy()

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
    engine: AsyncEngine, # type: ignore
    *,
    expire_on_commit: bool = False,
) -> async_sessionmaker[AsyncSession]: # type: ignore
    """Create an async session factory with safe defaults."""
    _require_sqlalchemy()

    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=expire_on_commit,
    )


@asynccontextmanager
async def _session_scope_context(
    session_factory: async_sessionmaker[AsyncSession], # type: ignore
) -> AsyncIterator[AsyncSession]: # type: ignore
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


class _AsyncSessionScope:
    """One-shot async context manager with legacy async-iterator support."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]): # type: ignore
        self._context = _session_scope_context(session_factory)
        self._iterator: AsyncGenerator[AsyncSession, None] | None = None # type: ignore

    async def __aenter__(self) -> AsyncSession: # type: ignore
        return await self._context.__aenter__()

    async def __aexit__(
        self,
        exc_type: Any,  # noqa: PYI036
        exc_value: Any,  # noqa: PYI036
        traceback: Any,  # noqa: PYI036
    ) -> Any:
        return await self._context.__aexit__(exc_type, exc_value, traceback)

    def __aiter__(self) -> _AsyncSessionScope:
        if self._iterator is None:
            self._iterator = self._iterate()
        return self

    async def __anext__(self) -> AsyncSession: # type: ignore
        iterator = self._iterator
        if iterator is None:
            iterator = self._iterate()
            self._iterator = iterator
        return await iterator.__anext__()

    async def aclose(self) -> None:
        if self._iterator is not None:
            await self._iterator.aclose()

    async def _iterate(self) -> AsyncGenerator[AsyncSession, None]: # type: ignore
        async with self as session:
            yield session


def session_scope(
    session_factory: async_sessionmaker[AsyncSession], # type: ignore
) -> _AsyncSessionScope:
    """Create a request-scoped async unit-of-work context.

    The context rolls back when the caller raises. Existing ``async for``
    consumption remains available for compatibility, but new code should use
    ``async with`` so exceptions from the body reach the rollback boundary.
    """
    return _AsyncSessionScope(session_factory)


def create_sync_sessionmaker(
    engine_sync: Any,
    *,
    autocommit: bool = False,
    autoflush: bool = False,
) -> sessionmaker[Session]: # type: ignore
    """Create a synchronous sessionmaker.

    Use this for offline scripts or background jobs. Avoid using synchronous
    sessions inside async request handlers unless running in a threadpool.
    """
    _require_sqlalchemy()

    return sessionmaker(bind=engine_sync, autocommit=autocommit, autoflush=autoflush)


# --- Public exports ----------------------------------------------------------

__all__ = [
    "ARRAY",
    "JSON",
    # engine/session
    "AsyncEngine",
    "AsyncSession",
    # base
    "Base",
    # sql primitives
    "Boolean",
    "CheckConstraint",
    "Column",
    "Date",
    "DateTime",
    "Enum",
    "Float",
    "ForeignKey",
    "Index",
    "Integer",
    "LargeBinary",
    "Numeric",
    "ORMUnavailableError",
    "Session",
    "String",
    "Text",
    "Time",
    "UniqueConstraint",
    "and_",
    "asc",
    "async_sessionmaker",
    "bindparam",
    "create_async_engine",
    "create_async_engine_from_url",
    "create_async_sessionmaker",
    "create_sync_sessionmaker",
    "delete",
    "desc",
    "func",
    "insert",
    "or_",
    # orm
    "relationship",
    "select",
    "selectinload",
    "session_scope",
    "sessionmaker",
    "text",
    "update",
]
