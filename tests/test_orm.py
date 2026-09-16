"""Lifecycle and dependency-boundary tests for the SQLAlchemy policy layer."""

from __future__ import annotations

import asyncio
import builtins
import importlib.util
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

from unicorefw import orm


class _BodyError(Exception):
    pass


class _FakeAsyncSession:
    def __init__(self, events):
        self.events = events

    async def __aenter__(self):
        self.events.append("enter")
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        del exc_value, traceback
        self.events.append(("exit", exc_type))
        return False

    async def rollback(self):
        self.events.append("rollback")


def _session_factory(events):
    return lambda: _FakeAsyncSession(events)


def _load_orm_module(module_name):
    spec = importlib.util.spec_from_file_location(module_name, Path(orm.__file__))
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sqlalchemy_reexports_and_sync_sessionmaker_work_with_sqlite():
    pytest.importorskip("sqlalchemy")
    assert orm.SQLALCHEMY_AVAILABLE is True
    assert issubclass(orm.ORMUnavailableError, ImportError)

    engine = orm.sa.create_engine("sqlite:///:memory:")
    session_factory = orm.create_sync_sessionmaker(engine)
    try:
        with session_factory() as session:
            assert session.execute(orm.text("SELECT 1")).scalar_one() == 1
    finally:
        engine.dispose()


def test_async_engine_wrapper_applies_defaults_and_copies_optional_settings(
    monkeypatch,
):
    pytest.importorskip("sqlalchemy")
    calls = []
    sentinel = object()

    def fake_create_async_engine(database_url, **kwargs):
        calls.append((database_url, kwargs))
        return sentinel

    monkeypatch.setattr(orm, "create_async_engine", fake_create_async_engine)

    assert orm.create_async_engine_from_url("sqlite+aiosqlite://") is sentinel
    connect_args = {"timeout": 5}
    assert (
        orm.create_async_engine_from_url(
            "postgresql+asyncpg://db.example/app",
            echo=True,
            pool_pre_ping=False,
            pool_recycle=120,
            pool_size=4,
            max_overflow=8,
            connect_args=connect_args,
            future=False,
        )
        is sentinel
    )

    assert calls[0] == (
        "sqlite+aiosqlite://",
        {
            "echo": False,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
            "future": True,
        },
    )
    assert calls[1][1] == {
        "echo": True,
        "pool_pre_ping": False,
        "pool_recycle": 120,
        "pool_size": 4,
        "max_overflow": 8,
        "connect_args": connect_args,
        "future": False,
    }
    assert calls[1][1]["connect_args"] is not connect_args


def test_async_sessionmaker_wrapper_uses_async_session_and_expiry_policy(monkeypatch):
    pytest.importorskip("sqlalchemy")
    calls = []
    sentinel = object()

    def fake_sessionmaker(engine, **kwargs):
        calls.append((engine, kwargs))
        return sentinel

    monkeypatch.setattr(orm, "async_sessionmaker", fake_sessionmaker)
    engine = object()

    assert orm.create_async_sessionmaker(engine) is sentinel
    assert orm.create_async_sessionmaker(engine, expire_on_commit=True) is sentinel
    assert calls == [
        (
            engine,
            {"class_": orm.AsyncSession, "expire_on_commit": False},
        ),
        (
            engine,
            {"class_": orm.AsyncSession, "expire_on_commit": True},
        ),
    ]


def test_session_scope_supports_documented_async_context_manager():
    events = []

    async def scenario():
        async with orm.session_scope(_session_factory(events)) as session:
            assert isinstance(session, _FakeAsyncSession)
            events.append("body")

    asyncio.run(scenario())

    assert events == ["enter", "body", ("exit", None)]


def test_session_scope_rolls_back_and_preserves_body_exception():
    events = []

    async def scenario():
        with pytest.raises(_BodyError):
            async with orm.session_scope(_session_factory(events)):
                events.append("body")
                raise _BodyError("stop")

    asyncio.run(scenario())

    assert events == [
        "enter",
        "body",
        "rollback",
        ("exit", _BodyError),
    ]


def test_session_scope_preserves_legacy_async_iteration_and_close():
    iterated_events = []
    closed_events = []

    async def scenario():
        scope = orm.session_scope(_session_factory(iterated_events))
        assert scope.__aiter__() is scope
        assert scope.__aiter__() is scope
        async for session in scope:
            assert isinstance(session, _FakeAsyncSession)
            iterated_events.append("body")

        unopened = orm.session_scope(_session_factory([]))
        await unopened.aclose()

        direct_scope = orm.session_scope(_session_factory(closed_events))
        session = await direct_scope.__anext__()
        assert isinstance(session, _FakeAsyncSession)
        await direct_scope.aclose()

    asyncio.run(scenario())

    assert iterated_events == ["enter", "body", ("exit", None)]
    assert closed_events[0] == "enter"
    assert closed_events[1][0] == "exit"


def test_missing_sqlalchemy_uses_lazy_placeholders_and_stable_error(
    monkeypatch,
):
    original_import = builtins.__import__

    def import_without_sqlalchemy(name, *args, **kwargs):
        if name == "sqlalchemy" or name.startswith("sqlalchemy."):
            raise ImportError("blocked for missing-dependency test")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_sqlalchemy)
    module = _load_orm_module("unicorefw_orm_without_backend")

    assert module.SQLALCHEMY_AVAILABLE is False
    assert module.sa is None
    assert repr(module.Base) == "<missing SQLAlchemy symbol 'Base'>"

    for operation in (
        module._require_sqlalchemy,
        module.Base,
        lambda: module.Base.metadata,
        lambda: module.create_sync_sessionmaker(object()),
        lambda: module.create_async_sessionmaker(object()),
        lambda: module.create_async_engine_from_url("sqlite+aiosqlite://"),
    ):
        with pytest.raises(
            module.ORMUnavailableError,
            match=r"unicorefw\[orm\]",
        ) as captured:
            operation()
        assert isinstance(captured.value, ImportError)
        assert captured.value.__cause__ is not None


def test_sqlalchemy_14_fallback_symbols_remain_import_compatible(monkeypatch):
    pytest.importorskip("sqlalchemy")
    original_import = builtins.__import__

    def import_without_modern_session_symbols(
        name,
        globals=None,
        locals=None,
        fromlist=(),
        level=0,
    ):
        if name == "sqlalchemy.orm" and "DeclarativeBase" in fromlist:
            raise ImportError("DeclarativeBase unavailable")
        if name == "sqlalchemy.ext.asyncio" and "async_sessionmaker" in fromlist:
            raise ImportError("async_sessionmaker unavailable")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(
        builtins,
        "__import__",
        import_without_modern_session_symbols,
    )
    module = _load_orm_module("unicorefw_orm_sqlalchemy_14_compat")

    assert module.SQLALCHEMY_AVAILABLE is True
    assert module.Base.metadata is not None
    assert callable(module.async_sessionmaker())
