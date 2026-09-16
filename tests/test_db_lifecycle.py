"""Database lifecycle, capability, and error-contract regression tests."""

from __future__ import annotations

import os
import sqlite3
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

import unicorefw.db as db_module
from unicorefw.db import (
    ConnectionPool,
    Database,
    DatabaseConnectionError,
    DatabaseError,
    DatabaseImportError,
    QueryError,
)


class _BodyError(Exception):
    pass


class _PoolConnection:
    def __init__(self, *, fail_close=False):
        self.close_calls = 0
        self.fail_close = fail_close

    def close(self):
        self.close_calls += 1
        if self.fail_close:
            raise RuntimeError("driver close included a credential")


class _CloseResource:
    def __init__(self, name, events, fail=False):
        self.name = name
        self.events = events
        self.fail = fail

    def close(self):
        self.events.append(self.name)
        if self.fail:
            raise RuntimeError(f"{self.name} close failed")


class _ClosePool:
    def __init__(self, events, fail=False):
        self.events = events
        self.fail = fail

    def close_all(self):
        self.events.append("pool")
        if self.fail:
            raise RuntimeError("pool close failed")


def test_database_exception_aliases_and_configuration_validation():
    assert db_module.ConnectionError is DatabaseConnectionError
    assert db_module.ImportError is DatabaseImportError
    assert issubclass(DatabaseConnectionError, DatabaseError)
    assert issubclass(DatabaseImportError, DatabaseError)

    for engine in (None, ""):
        with pytest.raises(DatabaseError, match="non-empty string"):
            Database(engine=engine)  # type: ignore[arg-type]

    with pytest.raises(DatabaseError, match="Unsupported or unavailable"):
        Database(engine="unknown")

    with pytest.raises(DatabaseConnectionError, match="must be callable"):
        ConnectionPool(None)  # type: ignore[arg-type]

    for limit in (0, -1, True, 1.5):
        with pytest.raises(DatabaseError, match="positive integer"):
            ConnectionPool(_PoolConnection, max_connections=limit) # type: ignore


def test_connection_pool_reuses_releases_exhausts_and_closes_connections():
    created = []

    def factory():
        connection = _PoolConnection()
        created.append(connection)
        return connection

    pool = ConnectionPool(factory, max_connections=1)
    first = pool._acquire()
    with pytest.raises(DatabaseConnectionError, match="exhausted"):
        pool._acquire()
    pool._release(first)

    with pytest.raises(_BodyError), pool.get_connection() as reused:
        assert reused is first
        raise _BodyError("release on context failure")

    assert pool.pool == [first]
    extra = _PoolConnection()
    pool._release(extra)
    assert extra.close_calls == 1

    pool.close_all()
    assert first.close_calls == 1
    assert pool.pool == []
    assert pool.in_use == set()

    in_use_pool = ConnectionPool(factory, max_connections=1)
    active = in_use_pool._acquire()
    in_use_pool.close_all()
    assert active.close_calls == 1


def test_connection_pool_normalizes_factory_failures_and_empty_results():
    def fail_factory():
        raise RuntimeError("driver failure included a credential")

    pool = ConnectionPool(fail_factory)
    with pytest.raises(
        DatabaseConnectionError,
        match="^Connection factory failed$",
    ) as captured:
        pool._acquire()

    assert isinstance(captured.value.__cause__, RuntimeError)
    assert "credential" not in str(captured.value)

    empty_pool = ConnectionPool(lambda: None)
    with pytest.raises(
        DatabaseConnectionError,
        match="factory returned no connection",
    ):
        empty_pool._acquire()


@pytest.mark.parametrize("fail_close", [False, True, None])
def test_connection_pool_rejects_unhashable_connections_and_cleans_up(
    fail_close,
):
    class UnhashableConnection:
        __hash__ = None # type: ignore

        def __init__(self):
            self.close_calls = 0

        if fail_close is not None:
            def close(self):
                self.close_calls += 1
                if fail_close:
                    raise RuntimeError("driver close included a credential")

    connection = UnhashableConnection()
    pool = ConnectionPool(lambda: connection)
    expected_message = (
        "Pooled connection validation and cleanup failed"
        if fail_close
        else "Pooled connection must be hashable"
    )

    with pytest.raises(
        DatabaseConnectionError,
        match=f"^{expected_message}$",
    ) as captured:
        pool._acquire()

    assert connection.close_calls == (0 if fail_close is None else 1)
    assert isinstance(captured.value.__cause__, (RuntimeError, TypeError))


def test_connection_pool_close_all_attempts_every_resource_after_failures():
    first = _PoolConnection(fail_close=True)
    second = _PoolConnection(fail_close=True)
    pool = ConnectionPool(_PoolConnection, max_connections=2)
    pool.pool = [first]
    pool.in_use = {second}

    with pytest.raises(
        DatabaseConnectionError,
        match="Failed to close one or more pooled connections",
    ) as captured:
        pool.close_all()

    assert first.close_calls == 1
    assert second.close_calls == 1
    assert pool.pool == []
    assert pool.in_use == set()
    assert isinstance(captured.value.__cause__, RuntimeError)


def test_connection_pool_close_all_does_not_close_duplicate_resources_twice():
    connection = _PoolConnection()
    pool = ConnectionPool(_PoolConnection)
    pool.pool = [connection]
    pool.in_use = {connection}

    pool.close_all()

    assert connection.close_calls == 1


def test_connection_pool_normalizes_excess_connection_close_failure():
    pool = ConnectionPool(_PoolConnection, max_connections=1)
    pooled = _PoolConnection()
    excess = _PoolConnection(fail_close=True)
    pool.pool.append(pooled)

    with pytest.raises(
        DatabaseConnectionError,
        match="Failed to close excess pooled connection",
    ) as captured:
        pool._release(excess)

    assert excess.close_calls == 1
    assert isinstance(captured.value.__cause__, RuntimeError)


def test_database_context_commits_or_rolls_back_and_closes(tmp_path):
    database_path = tmp_path / "context.sqlite"

    with Database(engine="sqlite", database=str(database_path)) as db:
        assert db._transaction_depth == 1
        db.create_table("events", {"value": "TEXT"})
        db.execute("INSERT INTO events(value) VALUES (?)", ("committed",))

    assert db.connection is None
    assert db.cursor is None

    with pytest.raises(_BodyError), Database(
        engine="sqlite", database=str(database_path)
    ) as db:
        db.execute("INSERT INTO events(value) VALUES (?)", ("rolled back",))
        raise _BodyError("rollback")

    with sqlite3.connect(str(database_path)) as connection:
        assert connection.execute(
            "SELECT value FROM events ORDER BY rowid"
        ).fetchall() == [("committed",)]


def test_database_context_unwinds_nested_levels_before_close(tmp_path):
    database_path = tmp_path / "nested-context.sqlite"

    with Database(engine="sqlite", database=str(database_path)) as db:
        db.create_table("events", {"value": "TEXT"})
        db.begin()
        db.insert("events", {"value": "nested"})
        assert db._transaction_depth == 2

    assert db._transaction_depth == 0
    with sqlite3.connect(str(database_path)) as connection:
        assert connection.execute("SELECT value FROM events").fetchall() == [
            ("nested",)
        ]


def test_context_enter_closes_connection_when_begin_fails(monkeypatch):
    db = Database(engine="sqlite", database=":memory:")

    def fail_begin():
        raise RuntimeError("begin failed")

    monkeypatch.setattr(db, "begin", fail_begin)

    with pytest.raises(RuntimeError, match="begin failed"):
        db.__enter__()

    assert db.connection is None
    assert db.cursor is None


def test_context_enter_reports_cleanup_failure(monkeypatch):
    db = Database(engine="sqlite", database=":memory:")

    def fail_begin():
        raise RuntimeError("begin failed")

    def fail_close():
        raise RuntimeError("close failed")

    monkeypatch.setattr(db, "begin", fail_begin)
    monkeypatch.setattr(db, "close", fail_close)

    with pytest.raises(
        DatabaseError,
        match="^Failed to enter database context and close resources$",
    ) as captured:
        db.__enter__()

    assert isinstance(captured.value.__cause__, RuntimeError)
    assert str(captured.value.__cause__) == "close failed"


def test_transaction_context_commits_and_rolls_back_body_errors():
    db = Database(engine="sqlite", database=":memory:")
    db.create_table("events", {"value": "TEXT"})
    try:
        with db.transaction():
            db.execute("INSERT INTO events(value) VALUES (?)", ("committed",))

        with pytest.raises(_BodyError), db.transaction():
            db.execute("INSERT INTO events(value) VALUES (?)", ("rolled back",))
            raise _BodyError("rollback")

        assert db.fetch_all("SELECT value FROM events") == [
            {"value": "committed"}
        ]
        assert db._transaction_active is False
    finally:
        db.close()


def test_context_exit_closes_connection_when_commit_fails(monkeypatch):
    db = Database(engine="sqlite", database=":memory:")

    def fail_commit():
        raise RuntimeError("commit failed")

    monkeypatch.setattr(db, "commit", fail_commit)

    with pytest.raises(RuntimeError, match="commit failed"):
        db.__exit__(None, None, None)

    assert db.connection is None
    assert db.cursor is None


def test_closed_database_operations_raise_stable_package_errors():
    db = Database(engine="sqlite", database=":memory:")
    db.close()

    for operation in (db.begin, db.commit, db.rollback):
        with pytest.raises(DatabaseError, match="not available"):
            operation()

    with pytest.raises(QueryError, match="cursor is not available"):
        db.execute("SELECT 1")


@pytest.mark.parametrize("query", [None, "", "   ", "SELECT\x00 1"])
def test_execute_rejects_invalid_query_text(query):
    db = Database(engine="sqlite", database=":memory:")
    try:
        with pytest.raises(QueryError, match="non-empty text"):
            db.execute(query)  # type: ignore[arg-type]
    finally:
        db.close()


def test_query_error_chains_driver_failure_without_echoing_query():
    db = Database(engine="sqlite", database=":memory:")
    query = "SELECT private_secret FROM"
    try:
        with pytest.raises(QueryError, match="^Query execution failed$") as captured:
            db.execute(query)

        assert isinstance(captured.value.__cause__, sqlite3.Error)
        assert query not in str(captured.value)
    finally:
        db.close()


def test_close_attempts_all_owned_resources_and_preserves_first_failure():
    events = []
    db = Database.__new__(Database)
    db.cursor = _CloseResource("cursor", events, fail=True)
    db.connection = _CloseResource("connection", events, fail=True)
    db._driver_owner = _CloseResource("owner", events)
    db._pool = _ClosePool(events, fail=True) # type: ignore

    with pytest.raises(DatabaseError, match="Failed to close") as captured:
        db.close()

    assert events == ["cursor", "connection", "owner", "pool"]
    assert isinstance(captured.value.__cause__, RuntimeError)
    assert str(captured.value.__cause__) == "cursor close failed"
    assert db.cursor is None
    assert db.connection is None
    assert db._driver_owner is None
    assert db._pool is None


def test_close_normalizes_a_pool_only_failure():
    events = []
    db = Database.__new__(Database)
    db.cursor = None
    db.connection = None
    db._driver_owner = None
    db._pool = _ClosePool(events, fail=True) # type: ignore

    with pytest.raises(DatabaseError, match="Failed to close") as captured:
        db.close()

    assert events == ["pool"]
    assert isinstance(captured.value.__cause__, RuntimeError)


def test_close_does_not_close_the_same_owned_resource_twice():
    events = []
    resource = _CloseResource("shared", events)
    db = Database.__new__(Database)
    db.cursor = resource
    db.connection = resource
    db._driver_owner = resource
    db._pool = None

    db.close()

    assert events == ["shared"]


def test_mongodb_client_owner_is_retained_and_closed(monkeypatch):
    events = []
    clients = []

    class FakeMongoClient:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            clients.append(self)

        def __getitem__(self, name):
            events.append(("database", name))
            return object()

        def close(self):
            events.append("client closed")

    monkeypatch.setattr(db_module, "MONGODB_AVAILABLE", True)
    monkeypatch.setattr(
        db_module,
        "pymongo",
        SimpleNamespace(MongoClient=FakeMongoClient),
        raising=False,
    )

    db = Database(
        engine="mongodb",
        database="application",
        host="db.example",
    )
    assert clients[0].kwargs == {"host": "db.example"}
    assert db._driver_owner is clients[0]

    db.close()

    assert events == [("database", "application"), "client closed"]


def test_mongodb_client_closes_when_database_selection_fails(monkeypatch):
    events = []

    class FailingMongoClient:
        def __init__(self, **kwargs):
            del kwargs

        def __getitem__(self, name):
            raise RuntimeError(f"cannot select {name}")

        def close(self):
            events.append("client closed")

    monkeypatch.setattr(db_module, "MONGODB_AVAILABLE", True)
    monkeypatch.setattr(
        db_module,
        "pymongo",
        SimpleNamespace(MongoClient=FailingMongoClient),
        raising=False,
    )

    with pytest.raises(
        DatabaseConnectionError,
        match="^Failed to initialize mongodb database$",
    ) as captured:
        Database(engine="mongodb", database="application")

    assert isinstance(captured.value.__cause__, RuntimeError)
    assert "application" not in str(captured.value)
    assert events == ["client closed"]


def test_sqlite_initialization_failure_is_redacted(monkeypatch):
    def fail_connect(*args, **kwargs):
        del args, kwargs
        raise RuntimeError("driver error exposed a password")

    monkeypatch.setattr(db_module.sqlite3, "connect", fail_connect)

    with pytest.raises(
        DatabaseConnectionError,
        match="^Failed to initialize sqlite database$",
    ) as captured:
        Database(engine="sqlite", database="private.sqlite")

    assert isinstance(captured.value.__cause__, RuntimeError)
    assert "password" not in str(captured.value)
    assert "private.sqlite" not in str(captured.value)


@pytest.mark.parametrize(
    ("engine", "availability_name", "module_name", "module"),
    [
        (
            "postgres",
            "POSTGRES_AVAILABLE",
            "psycopg2",
            SimpleNamespace(
                extras=SimpleNamespace(DictCursor=object()),
            ),
        ),
        (
            "mysql",
            "MYSQL_AVAILABLE",
            "pymysql",
            SimpleNamespace(
                cursors=SimpleNamespace(DictCursor=object()),
            ),
        ),
    ],
)
def test_relational_cursor_initialization_failure_closes_connection(
    monkeypatch,
    engine,
    availability_name,
    module_name,
    module,
):
    events = []

    class FailingConnection:
        def cursor(self, *args, **kwargs):
            del args, kwargs
            raise RuntimeError("cursor failure exposed a password")

        def close(self):
            events.append("connection closed")

    module.connect = lambda **kwargs: FailingConnection()
    monkeypatch.setattr(db_module, availability_name, True)
    monkeypatch.setattr(db_module, module_name, module, raising=False)

    with pytest.raises(
        DatabaseConnectionError,
        match=rf"^Failed to initialize {engine} database$",
    ) as captured:
        Database(engine=engine, password="placeholder")  # pragma: allowlist secret; expires=2027-07-28; rationale=Non-secret fixture verifies credential redaction.

    assert events == ["connection closed"]
    assert isinstance(captured.value.__cause__, RuntimeError)
    assert "password" not in str(captured.value)


def test_postgres_configuration_failure_closes_cursor_and_connection(
    monkeypatch,
):
    events = []

    class Cursor:
        def close(self):
            events.append("cursor closed")

    class FailingConnection:
        def cursor(self, **kwargs):
            del kwargs
            return Cursor()

        @property
        def autocommit(self):
            return False

        @autocommit.setter
        def autocommit(self, value):
            del value
            raise RuntimeError("autocommit failure")

        def close(self):
            events.append("connection closed")

    module = SimpleNamespace(
        connect=lambda **kwargs: FailingConnection(),
        extras=SimpleNamespace(DictCursor=object()),
    )
    monkeypatch.setattr(db_module, "POSTGRES_AVAILABLE", True)
    monkeypatch.setattr(db_module, "psycopg2", module, raising=False)

    with pytest.raises(
        DatabaseConnectionError,
        match="^Failed to initialize postgres database$",
    ):
        Database(engine="postgres")

    assert events == ["cursor closed", "connection closed"]


@pytest.mark.parametrize("engine", ["postgres", "mysql"])
def test_relational_driver_initialization_retains_owned_resources(
    monkeypatch,
    engine,
):
    events = []

    class Cursor:
        def close(self):
            events.append("cursor closed")

    class Connection:
        def __init__(self):
            self.autocommit = False

        def cursor(self, *args, **kwargs):
            events.append(("cursor", args, kwargs))
            return Cursor()

        def close(self):
            events.append("connection closed")

    connection = Connection()
    if engine == "postgres":
        module = SimpleNamespace(
            connect=lambda **kwargs: connection,
            extras=SimpleNamespace(DictCursor="postgres-cursor"),
        )
        monkeypatch.setattr(db_module, "POSTGRES_AVAILABLE", True)
        monkeypatch.setattr(db_module, "psycopg2", module, raising=False)
    else:
        module = SimpleNamespace(
            connect=lambda **kwargs: connection,
            cursors=SimpleNamespace(DictCursor="mysql-cursor"),
        )
        monkeypatch.setattr(db_module, "MYSQL_AVAILABLE", True)
        monkeypatch.setattr(db_module, "pymysql", module, raising=False)

    db = Database(engine=engine, host="db.example")

    assert db.connection is connection
    assert isinstance(db.cursor, Cursor)
    if engine == "postgres":
        assert connection.autocommit is True
        assert events == [
            ("cursor", (), {"cursor_factory": "postgres-cursor"})
        ]
    else:
        assert events == [("cursor", ("mysql-cursor",), {})]

    db.close()
    assert events[-2:] == ["cursor closed", "connection closed"]


def test_initialization_cleanup_failure_is_redacted(monkeypatch):
    class FailingConnection:
        row_factory = None

        def cursor(self):
            raise RuntimeError("cursor initialization failed")

        def close(self):
            raise RuntimeError("cleanup exposed a password")

    monkeypatch.setattr(
        db_module.sqlite3,
        "connect",
        lambda *args, **kwargs: FailingConnection(),
    )

    with pytest.raises(
        DatabaseConnectionError,
        match="^Failed to clean up incomplete database initialization$",
    ) as captured:
        Database(engine="sqlite")

    assert isinstance(captured.value.__cause__, RuntimeError)
    assert "password" not in str(captured.value)


def test_initialization_cleanup_attempts_all_callable_resources():
    events = []
    first = _CloseResource("first", events, fail=True)
    second = _CloseResource("second", events, fail=True)

    with pytest.raises(
        DatabaseConnectionError,
        match="Failed to clean up incomplete database initialization",
    ) as captured:
        Database._close_initialization_resources(
            object(),
            first,
            second,
        )

    assert events == ["first", "second"]
    assert str(captured.value.__cause__) == "first close failed"


def test_initialization_cleanup_preserves_control_flow_exceptions(monkeypatch):
    events = []

    class InterruptedConnection:
        row_factory = None

        def cursor(self):
            raise KeyboardInterrupt()

        def close(self):
            events.append("connection closed")

    monkeypatch.setattr(
        db_module.sqlite3,
        "connect",
        lambda *args, **kwargs: InterruptedConnection(),
    )

    with pytest.raises(KeyboardInterrupt):
        Database(engine="sqlite")

    assert events == ["connection closed"]


def test_mongodb_cleanup_failure_is_redacted(monkeypatch):
    class FailingMongoClient:
        def __init__(self, **kwargs):
            del kwargs

        def __getitem__(self, name):
            raise RuntimeError(f"cannot select {name}")

        def close(self):
            raise RuntimeError("cleanup exposed a password")

    monkeypatch.setattr(db_module, "MONGODB_AVAILABLE", True)
    monkeypatch.setattr(
        db_module,
        "pymongo",
        SimpleNamespace(MongoClient=FailingMongoClient),
        raising=False,
    )

    with pytest.raises(
        DatabaseConnectionError,
        match="^Failed to clean up incomplete database initialization$",
    ) as captured:
        Database(engine="mongodb", database="application")

    assert isinstance(captured.value.__cause__, RuntimeError)
    assert "password" not in str(captured.value)


def test_redis_initialization_failure_is_redacted(monkeypatch):
    def fail_redis(**kwargs):
        del kwargs
        raise RuntimeError("redis failure exposed a password")

    monkeypatch.setattr(db_module, "REDIS_AVAILABLE", True)
    monkeypatch.setattr(
        db_module,
        "redis",
        SimpleNamespace(Redis=fail_redis),
        raising=False,
    )

    with pytest.raises(
        DatabaseConnectionError,
        match="^Failed to initialize redis database$",
    ) as captured:
        Database(engine="redis", password="placeholder")  # pragma: allowlist secret; expires=2027-07-28; rationale=Non-secret fixture verifies credential redaction.

    assert isinstance(captured.value.__cause__, RuntimeError)
    assert "password" not in str(captured.value)


@pytest.mark.parametrize(
    ("method_name", "availability_name", "message"),
    [
        ("_init_postgres", "POSTGRES_AVAILABLE", "psycopg2"),
        ("_init_mysql", "MYSQL_AVAILABLE", "pymysql"),
        ("_init_mongodb", "MONGODB_AVAILABLE", "pymongo"),
        ("_init_redis", "REDIS_AVAILABLE", "redis"),
    ],
)
def test_driver_initializers_reject_missing_optional_dependencies(
    monkeypatch,
    method_name,
    availability_name,
    message,
):
    monkeypatch.setattr(db_module, availability_name, False)
    db = Database.__new__(Database)

    with pytest.raises(DatabaseError, match=message):
        getattr(db, method_name)()


@pytest.mark.parametrize(
    "operation",
    [
        lambda db: db.execute("SELECT 1"),
        lambda db: db.insert("records", {"id": 1}),
        lambda db: db.update("records", {"id": 2}, {"id": 1}),
        lambda db: db.delete("records", {"id": 1}),
        lambda db: db.create_table("records", {"id": "INTEGER"}),
        lambda db: db.drop_table("records"),
    ],
)
def test_database_operations_reject_unsupported_engine_capabilities(operation):
    db = Database(engine="sqlite", database=":memory:")
    db.engine = "redis"
    try:
        with pytest.raises(DatabaseError, match="not supported"):
            operation(db)
    finally:
        db.close()
