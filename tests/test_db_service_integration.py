"""Opt-in PostgreSQL and MySQL lifecycle integration tests.

The suite fails closed unless it targets the dedicated loopback-only CI
database and least-privilege test user. Set ``UNICORE_FW_DATABASE_INTEGRATION``
to ``1`` only after provisioning both services with the values below.
"""

from __future__ import annotations

import os
import secrets
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

from unicorefw.db import Database, QueryError

_ENGINES = ("postgres", "mysql")
_DATABASE_NAME = "unicorefw_test"
_DATABASE_USER = "unicorefw"
_EXPECTED_PORTS = {"postgres": 5432, "mysql": 3306}

pytestmark = pytest.mark.database_integration


class _BodyError(Exception):
    """Expected transaction-body failure."""


def _service_kwargs(engine: str) -> dict[str, object]:
    if os.environ.get("UNICORE_FW_DATABASE_INTEGRATION") != "1":
        pytest.skip("database integration services are not enabled")

    prefix = f"UNICORE_FW_{engine.upper()}"
    host = os.environ.get(f"{prefix}_HOST")
    database = os.environ.get(f"{prefix}_DATABASE")
    user = os.environ.get(f"{prefix}_USER")
    password = os.environ.get(f"{prefix}_PASSWORD")
    port_text = os.environ.get(f"{prefix}_PORT")

    if host != "127.0.0.1":
        raise RuntimeError("database integration host must be 127.0.0.1")
    if database != _DATABASE_NAME:
        raise RuntimeError("database integration database is not the test database")
    if user != _DATABASE_USER:
        raise RuntimeError("database integration user is not the test user")
    if not password:
        raise RuntimeError("database integration password is required")
    try:
        port = int(port_text or "")
    except ValueError as exc:
        raise RuntimeError("database integration port must be an integer") from exc
    if port != _EXPECTED_PORTS[engine]:
        raise RuntimeError("database integration port is not the expected local port")

    common: dict[str, object] = {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "connect_timeout": 5,
    }
    if engine == "postgres":
        common.update(
            {
                "dbname": database,
                "application_name": "unicorefw-integration-tests",
                "sslmode": "disable",
            }
        )
    else:
        common.update(
            {
                "database": database,
                "charset": "utf8mb4",
                "read_timeout": 5,
                "write_timeout": 5,
            }
        )
    return common


def _connect(engine: str) -> Database:
    return Database(engine=engine, **_service_kwargs(engine)) # type: ignore


def _table_name() -> str:
    return f"unicorefw_it_{secrets.token_hex(8)}"


def _enable_service_config(monkeypatch, engine: str) -> str:
    prefix = f"UNICORE_FW_{engine.upper()}"
    monkeypatch.setenv("UNICORE_FW_DATABASE_INTEGRATION", "1")
    monkeypatch.setenv(f"{prefix}_HOST", "127.0.0.1")
    monkeypatch.setenv(f"{prefix}_PORT", str(_EXPECTED_PORTS[engine]))
    monkeypatch.setenv(f"{prefix}_DATABASE", _DATABASE_NAME)
    monkeypatch.setenv(f"{prefix}_USER", _DATABASE_USER)
    monkeypatch.setenv(f"{prefix}_PASSWORD", "integration-only-password")
    return prefix


def _values(db: Database, table: str):
    quote = '"' if db.engine == "postgres" else "`"
    return [
        row["value"]
        for row in db.fetch_all(
            f"SELECT value FROM {quote}{table}{quote} ORDER BY id"
        )
    ]


def test_service_configuration_requires_explicit_opt_in(monkeypatch):
    monkeypatch.delenv("UNICORE_FW_DATABASE_INTEGRATION", raising=False)

    with pytest.raises(pytest.skip.Exception):
        _service_kwargs("postgres")


@pytest.mark.parametrize(
    ("suffix", "value", "message"),
    [
        ("HOST", "db.example", "host"),
        ("PORT", "1", "port"),
        ("DATABASE", "production", "test database"),
        ("USER", "root", "test user"),
        ("PASSWORD", "", "password"),
    ],
)
def test_service_configuration_rejects_unsafe_targets(
    monkeypatch,
    suffix,
    value,
    message,
):
    prefix = _enable_service_config(monkeypatch, "postgres")
    monkeypatch.setenv(f"{prefix}_{suffix}", value)

    with pytest.raises(RuntimeError, match=message):
        _service_kwargs("postgres")


@pytest.mark.parametrize("engine", _ENGINES)
def test_service_configuration_builds_bounded_driver_options(monkeypatch, engine):
    _enable_service_config(monkeypatch, engine)

    options = _service_kwargs(engine)

    assert options["host"] == "127.0.0.1"
    assert options["port"] == _EXPECTED_PORTS[engine]
    assert options["connect_timeout"] == 5
    if engine == "postgres":
        assert options["dbname"] == _DATABASE_NAME
        assert options["sslmode"] == "disable"
    else:
        assert options["database"] == _DATABASE_NAME
        assert options["read_timeout"] == 5
        assert options["write_timeout"] == 5


@pytest.fixture(params=_ENGINES)
def service_db(request):
    db = _connect(request.param)
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def service_table(service_db):
    table = _table_name()
    primary_key = (
        "BIGSERIAL PRIMARY KEY"
        if service_db.engine == "postgres"
        else "BIGINT AUTO_INCREMENT PRIMARY KEY"
    )
    service_db.create_table(
        table,
        {
            "id": primary_key,
            "value": "TEXT NOT NULL",
        },
    )
    try:
        yield service_db, table
    finally:
        while service_db._transaction_depth:
            service_db.rollback()
        service_db.drop_table(table)


def test_context_rolls_back_body_failure_and_closes_connection(service_db):
    engine = service_db.engine
    table = _table_name()
    service_db.create_table(
        table,
        {
            "id": (
                "BIGSERIAL PRIMARY KEY"
                if engine == "postgres"
                else "BIGINT AUTO_INCREMENT PRIMARY KEY"
            ),
            "value": "TEXT NOT NULL",
        },
    )
    service_db.close()

    failed_connection = None
    try:
        with pytest.raises(_BodyError), _connect(engine) as transaction_db:
            failed_connection = transaction_db.connection
            transaction_db.insert(table, {"value": "rolled back"})
            raise _BodyError("rollback")

        assert failed_connection is not None
        if engine == "postgres":
            assert failed_connection.closed # type: ignore
        else:
            assert not failed_connection.open # type: ignore

        with _connect(engine) as verification_db:
            assert _values(verification_db, table) == []
    finally:
        cleanup_db = _connect(engine)
        try:
            cleanup_db.drop_table(table)
        finally:
            cleanup_db.close()


def test_bound_adversarial_value_round_trips_as_data(service_table):
    db, table = service_table
    value = "雪'); DROP TABLE audit; --\nsecond line"

    with db.transaction():
        db.insert(table, {"value": value})

    assert _values(db, table) == [value]


def test_inner_rollback_preserves_outer_work(service_table):
    db, table = service_table

    with db.transaction():
        db.insert(table, {"value": "outer"})
        with pytest.raises(_BodyError), db.transaction():
            db.insert(table, {"value": "inner"})
            raise _BodyError("rollback inner")

    assert _values(db, table) == ["outer"]


def test_outer_rollback_discards_released_inner_work(service_table):
    db, table = service_table

    with pytest.raises(_BodyError), db.transaction():
        db.insert(table, {"value": "outer"})
        with db.transaction():
            db.insert(table, {"value": "inner"})
        raise _BodyError("rollback outer")

    assert _values(db, table) == []


def test_failed_query_rolls_back_and_connection_recovers(service_table):
    db, table = service_table
    quote = '"' if db.engine == "postgres" else "`"

    with pytest.raises(QueryError, match="^Query execution failed$"), db.transaction():
            db.execute(
                f"INSERT INTO {quote}{table}{quote} "
                f"({quote}missing{quote}) VALUES (%s)",
                ("invalid",),
            )

    assert db._transaction_depth == 0
    assert db._transaction_active is False

    with db.transaction():
        db.insert(table, {"value": "recovered"})

    assert _values(db, table) == ["recovered"]
