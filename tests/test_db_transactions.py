"""Nested database transaction and savepoint regression tests."""

from __future__ import annotations

import os
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

from unicorefw.db import Database, DatabaseError


class _BodyError(Exception):
    pass


class _Abort(BaseException):
    pass


class _DriverState:
    def __init__(self):
        self.events = []
        self.failures = {}

    def record(self, event):
        self.events.append(event)
        remaining = self.failures.get(event, 0)
        if remaining:
            self.failures[event] = remaining - 1
            raise RuntimeError(f"{event} failed")


class _DriverCursor:
    def __init__(self, state):
        self.state = state

    def execute(self, statement):
        self.state.record(statement)


class _DriverConnection:
    def __init__(self, state, autocommit=False):
        self.state = state
        self._autocommit = autocommit

    @property
    def autocommit(self):
        return self._autocommit

    @autocommit.setter
    def autocommit(self, value):
        self.state.record(f"autocommit={value}")
        self._autocommit = value

    def begin(self):
        self.state.record("connection.begin")

    def commit(self):
        self.state.record("connection.commit")

    def rollback(self):
        self.state.record("connection.rollback")


class _ConnectionWithoutBegin:
    def __init__(self, state):
        self.state = state

    def commit(self):
        self.state.record("connection.commit")

    def rollback(self):
        self.state.record("connection.rollback")


def _driver_database(engine, *, autocommit=False):
    state = _DriverState()
    db = Database.__new__(Database)
    db.engine = engine
    db.connection = _DriverConnection(state, autocommit=autocommit)
    db.cursor = _DriverCursor(state)
    db._transaction_active = False
    db._transaction_depth = 0
    db._savepoint_counter = 0
    db._savepoints = []
    db._prev_autocommit = None
    return db, state


def _values(db):
    return [
        row["value"]
        for row in db.fetch_all("SELECT value FROM events ORDER BY rowid")
    ]


def test_nested_sqlite_transactions_commit_each_level():
    db = Database(engine="sqlite", database=":memory:")
    db.create_table("events", {"value": "TEXT"})
    try:
        with db.transaction():
            db.insert("events", {"value": "outer-before"})
            assert db._transaction_depth == 1

            with db.transaction():
                db.insert("events", {"value": "inner"})
                assert db._transaction_depth == 2
                assert db._savepoints == ["unicorefw_sp_1"]

            assert db._transaction_depth == 1
            assert db._transaction_active is True
            db.insert("events", {"value": "outer-after"})

        assert _values(db) == ["outer-before", "inner", "outer-after"]
        assert db._transaction_depth == 0
        assert db._transaction_active is False
        assert db._savepoints == []
    finally:
        db.close()


def test_inner_sqlite_failure_rolls_back_only_its_savepoint():
    db = Database(engine="sqlite", database=":memory:")
    db.create_table("events", {"value": "TEXT"})
    try:
        with db.transaction():
            db.insert("events", {"value": "outer-before"})

            with pytest.raises(_BodyError), db.transaction():
                db.insert("events", {"value": "inner"})
                db.create_table("inner_table", {"id": "INTEGER"})
                raise _BodyError("rollback inner")

            assert _values(db) == ["outer-before"]
            assert db.fetch_one(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name = 'inner_table'"
            ) is None
            db.insert("events", {"value": "outer-after"})

        assert _values(db) == ["outer-before", "outer-after"]
    finally:
        db.close()


def test_outer_sqlite_failure_rolls_back_released_inner_savepoint():
    db = Database(engine="sqlite", database=":memory:")
    db.create_table("events", {"value": "TEXT"})
    try:
        with pytest.raises(_BodyError), db.transaction():
            db.insert("events", {"value": "outer"})
            with db.transaction():
                db.insert("events", {"value": "inner"})
            raise _BodyError("rollback outer")

        assert _values(db) == []
        assert db._transaction_depth == 0
    finally:
        db.close()


def test_transaction_rolls_back_base_exceptions():
    db = Database(engine="sqlite", database=":memory:")
    db.create_table("events", {"value": "TEXT"})
    try:
        with pytest.raises(_Abort), db.transaction():
            db.insert("events", {"value": "interrupted"})
            raise _Abort()

        assert _values(db) == []
        assert db._transaction_active is False
    finally:
        db.close()


def test_manual_nested_begin_commit_and_rollback_use_savepoints():
    db = Database(engine="sqlite", database=":memory:")
    db.create_table("events", {"value": "TEXT"})
    try:
        db.begin()
        db.insert("events", {"value": "outer-kept"})
        db.begin()
        db.insert("events", {"value": "inner-removed"})
        db.rollback()

        assert _values(db) == ["outer-kept"]
        assert db._transaction_depth == 1
        db.commit()

        db.begin()
        db.insert("events", {"value": "outer-removed"})
        db.begin()
        db.insert("events", {"value": "inner-released"})
        db.commit()
        db.rollback()

        assert _values(db) == ["outer-kept"]
        assert db._transaction_depth == 0
    finally:
        db.close()


def test_transaction_context_closes_manual_nested_levels():
    db = Database(engine="sqlite", database=":memory:")
    db.create_table("events", {"value": "TEXT"})
    try:
        with db.transaction():
            db.begin()
            db.insert("events", {"value": "nested"})
            assert db._transaction_depth == 2

        assert _values(db) == ["nested"]
        assert db._transaction_depth == 0

        with db.transaction():
            db.insert("events", {"value": "manual-commit"})
            db.commit()

        assert _values(db) == ["nested", "manual-commit"]
    finally:
        db.close()


def test_begin_adopts_existing_sqlite_transaction():
    db = Database(engine="sqlite", database=":memory:")
    db.create_table("events", {"value": "TEXT"})
    try:
        db.insert("events", {"value": "implicit"})
        assert db.connection.in_transaction is True # type: ignore
        assert db._transaction_depth == 0

        db.begin()
        assert db._transaction_depth == 1
        db.rollback()

        assert _values(db) == []
    finally:
        db.close()


def test_postgres_nested_transactions_restore_autocommit():
    db, state = _driver_database("postgres", autocommit=True)

    db.begin()
    db.begin()
    db.commit()
    db.rollback()

    assert state.events == [
        "autocommit=False",
        "BEGIN",
        "SAVEPOINT unicorefw_sp_1",
        "RELEASE SAVEPOINT unicorefw_sp_1",
        "connection.rollback",
        "autocommit=True",
    ]
    assert db._transaction_depth == 0
    assert db._prev_autocommit is None


def test_mysql_nested_transactions_use_savepoint_rollback():
    db, state = _driver_database("mysql")

    db.begin()
    db.begin()
    db.rollback()
    db.commit()

    assert state.events == [
        "connection.begin",
        "SAVEPOINT unicorefw_sp_1",
        "ROLLBACK TO SAVEPOINT unicorefw_sp_1",
        "RELEASE SAVEPOINT unicorefw_sp_1",
        "connection.commit",
    ]
    assert db._transaction_depth == 0


def test_mysql_adopts_driver_without_explicit_begin_method():
    db, state = _driver_database("mysql")
    db.connection = _ConnectionWithoutBegin(state)

    db.begin()
    assert db._transaction_depth == 1
    db.commit()

    assert state.events == ["connection.commit"]


def test_mysql_begin_failure_does_not_change_transaction_state():
    db, state = _driver_database("mysql")
    state.failures["connection.begin"] = 1

    with pytest.raises(
        DatabaseError,
        match="^Failed to begin database transaction$",
    ) as caught:
        db.begin()

    assert isinstance(caught.value.__cause__, RuntimeError)
    assert db._transaction_depth == 0
    assert db._transaction_active is False
    assert db._prev_autocommit is None


def test_begin_preserves_control_flow_exceptions():
    db, state = _driver_database("mysql")

    def interrupt():
        state.events.append("connection.begin")
        raise KeyboardInterrupt()

    db.connection.begin = interrupt # type: ignore

    with pytest.raises(KeyboardInterrupt):
        db.begin()

    assert state.events == ["connection.begin"]
    assert db._transaction_depth == 0
    assert db._transaction_active is False


def test_unsupported_engine_transaction_controls_remain_no_ops():
    db, state = _driver_database("redis")

    db.begin()
    db.commit()
    db.rollback()

    assert state.events == []
    assert db._transaction_depth == 0


def test_depth_zero_commit_and_rollback_retain_driver_behavior():
    db, state = _driver_database("mysql")

    db.commit()
    db.rollback()

    assert state.events == ["connection.commit", "connection.rollback"]
    assert db._transaction_depth == 0


def test_transaction_rolls_back_after_root_commit_failure():
    db, state = _driver_database("mysql")
    state.failures["connection.commit"] = 1

    with pytest.raises(
        DatabaseError,
        match="^Failed to commit database transaction$",
    ) as caught, db.transaction():
        pass

    assert isinstance(caught.value.__cause__, RuntimeError)
    assert state.events == [
        "connection.begin",
        "connection.commit",
        "connection.rollback",
    ]
    assert db._transaction_depth == 0


def test_postgres_preserves_disabled_autocommit():
    db, state = _driver_database("postgres", autocommit=False)

    with db.transaction():
        pass

    assert state.events == ["BEGIN", "connection.commit"]
    assert db.connection.autocommit is False # type: ignore


def test_failed_savepoint_creation_does_not_change_transaction_depth():
    db, state = _driver_database("mysql")
    db.begin()
    state.failures["SAVEPOINT unicorefw_sp_1"] = 1

    with pytest.raises(DatabaseError, match="create transaction savepoint") as caught:
        db.begin()

    assert isinstance(caught.value.__cause__, RuntimeError)
    assert db._transaction_depth == 1
    assert db._savepoints == []
    db.rollback()


def test_nested_transaction_requires_an_available_cursor():
    db, state = _driver_database("mysql")
    db.begin()
    db.cursor = None

    with pytest.raises(DatabaseError, match="cursor is not available"):
        db.begin()

    assert state.events == ["connection.begin"]
    assert db._transaction_depth == 1
    db.cursor = _DriverCursor(state)
    db.rollback()


def test_failed_savepoint_release_rolls_back_nested_scope():
    db, state = _driver_database("mysql")
    db.begin()
    state.failures["RELEASE SAVEPOINT unicorefw_sp_1"] = 1

    with pytest.raises(DatabaseError, match="release transaction savepoint"), db.transaction():
        pass

    assert state.events[-3:] == [
        "RELEASE SAVEPOINT unicorefw_sp_1",
        "ROLLBACK TO SAVEPOINT unicorefw_sp_1",
        "RELEASE SAVEPOINT unicorefw_sp_1",
    ]
    assert db._transaction_depth == 1
    db.rollback()


def test_rollback_failure_reports_both_transaction_failures():
    db, state = _driver_database("mysql")
    db.begin()

    with pytest.raises(
        DatabaseError,
        match="Transaction failed and rollback failed",
    ) as caught, db.transaction():
        state.failures["ROLLBACK TO SAVEPOINT unicorefw_sp_1"] = 1
        raise ValueError("body failed")

    assert isinstance(caught.value.__cause__, DatabaseError)
    assert isinstance(caught.value.__cause__.__cause__, RuntimeError)
    assert db._transaction_depth == 2

    db.rollback()
    db.rollback()


def test_postgres_begin_failure_restores_autocommit_and_state():
    db, state = _driver_database("postgres", autocommit=True)
    state.failures["BEGIN"] = 1

    with pytest.raises(
        DatabaseError,
        match="^Failed to begin database transaction$",
    ) as caught:
        db.begin()

    assert isinstance(caught.value.__cause__, RuntimeError)
    assert state.events == ["autocommit=False", "BEGIN", "autocommit=True"]
    assert db.connection.autocommit is True # type: ignore
    assert db._transaction_depth == 0
    assert db._transaction_active is False
    assert db._prev_autocommit is None


def test_root_rollback_failure_is_redacted_and_preserves_state():
    db, state = _driver_database("mysql")
    db.begin()
    state.failures["connection.rollback"] = 1

    with pytest.raises(
        DatabaseError,
        match="^Failed to roll back database transaction$",
    ) as caught:
        db.rollback()

    assert isinstance(caught.value.__cause__, RuntimeError)
    assert db._transaction_depth == 1
    assert db._transaction_active is True
    db.rollback()


@pytest.mark.parametrize("operation", ["commit", "rollback"])
def test_postgres_autocommit_restore_failure_is_normalized(operation):
    db, state = _driver_database("postgres", autocommit=True)
    db.begin()
    state.failures["autocommit=True"] = 1

    with pytest.raises(
        DatabaseError,
        match="^Failed to restore database transaction mode$",
    ) as caught:
        getattr(db, operation)()

    assert isinstance(caught.value.__cause__, RuntimeError)
    assert db._transaction_depth == 0
    assert db._transaction_active is False
    assert db._prev_autocommit is None


def test_postgres_begin_and_autocommit_restore_failure_is_normalized():
    db, state = _driver_database("postgres", autocommit=True)
    state.failures["BEGIN"] = 1
    state.failures["autocommit=True"] = 1

    with pytest.raises(
        DatabaseError,
        match="^Failed to begin transaction and restore autocommit$",
    ) as caught:
        db.begin()

    assert isinstance(caught.value.__cause__, RuntimeError)
    assert state.events == ["autocommit=False", "BEGIN", "autocommit=True"]
    assert db._transaction_depth == 0
    assert db._transaction_active is False
    assert db._prev_autocommit is None


def test_postgres_begin_reports_autocommit_restore_failure():
    db, state = _driver_database("postgres", autocommit=True)
    state.failures["BEGIN"] = 1
    state.failures["autocommit=True"] = 1

    with pytest.raises(
        DatabaseError,
        match="begin transaction and restore autocommit",
    ) as caught:
        db.begin()

    assert isinstance(caught.value.__cause__, RuntimeError)
    assert state.events == ["autocommit=False", "BEGIN", "autocommit=True"]
    assert db._transaction_depth == 0
    assert db._prev_autocommit is None


def test_close_resets_nested_state_and_rolls_back_driver_transaction(tmp_path):
    database_path = tmp_path / "close.sqlite"
    db = Database(engine="sqlite", database=str(database_path))
    db.create_table("events", {"value": "TEXT"})
    db.begin()
    db.insert("events", {"value": "outer"})
    db.begin()
    db.insert("events", {"value": "inner"})

    db.close()

    assert db._transaction_depth == 0
    assert db._transaction_active is False
    assert db._savepoints == []
    with sqlite3.connect(str(database_path)) as connection:
        assert connection.execute("SELECT value FROM events").fetchall() == []
