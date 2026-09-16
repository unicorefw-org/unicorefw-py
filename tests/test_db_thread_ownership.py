"""Database process and thread ownership regression tests."""

from __future__ import annotations

import os
import sys
import threading

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

import unicorefw.db as db_module
from unicorefw.db import (
    BackupRestore,
    Database,
    DatabaseError,
    DatabaseImportError,
    DataExporter,
    DataImporter,
    ExportError,
)


def _call_in_thread(operation):
    outcomes = []

    def target():
        try:
            operation()
        except BaseException as exc:  # noqa: BLE001
            outcomes.append(exc)
        else:
            outcomes.append(None)

    worker = threading.Thread(target=target)
    worker.start()
    worker.join(timeout=5)
    assert not worker.is_alive()
    assert len(outcomes) == 1
    return outcomes[0]


@pytest.mark.parametrize(
    "operation",
    [
        lambda db: db.__enter__(),
        lambda db: db.execute("SELECT 1"),
        lambda db: db.begin(),
        lambda db: db.commit(),
        lambda db: db.rollback(),
        lambda db: db.insert("records", {"id": 1}),
        lambda db: db.update("records", {"id": 2}, {"id": 1}),
        lambda db: db.delete("records", {"id": 1}),
        lambda db: db.create_table("records", {"id": "INTEGER"}),
        lambda db: db.drop_table("records"),
        lambda db: db.close(),
    ],
)
def test_database_operations_reject_cross_thread_use_before_driver_access(
    operation,
):
    db = Database(
        engine="sqlite",
        database=":memory:",
        check_same_thread=False,
    )
    try:
        outcome = _call_in_thread(lambda: operation(db))

        assert isinstance(outcome, DatabaseError)
        assert str(outcome) == (
            "Database instances may only be used by their creating thread"
        )
        assert db.fetch_one("SELECT 1 AS value") == {"value": 1}
    finally:
        db.close()


def test_cross_thread_opt_out_requires_driver_support_and_serialization():
    db = Database(
        engine="sqlite",
        database=":memory:",
        check_same_thread=False,
        unsafe_allow_cross_thread=True,
    )
    try:
        outcome = _call_in_thread(
            lambda: db.fetch_one("SELECT 1 AS value")
        )

        assert outcome is None
        assert db._config == {
            "database": ":memory:",
            "check_same_thread": False,
        }
    finally:
        db.close()


@pytest.mark.parametrize("value", [None, 0, 1, "true"])
def test_cross_thread_opt_out_requires_a_boolean(value):
    with pytest.raises(
        DatabaseError,
        match="unsafe_allow_cross_thread must be a boolean",
    ):
        Database(unsafe_allow_cross_thread=value)  # type: ignore[arg-type]


def test_process_ownership_cannot_be_disabled(monkeypatch):
    db = Database(
        engine="sqlite",
        database=":memory:",
        unsafe_allow_cross_thread=True,
    )
    try:
        owner_process_id = os.getpid()
        with monkeypatch.context() as patch:
            patch.setattr(
                db_module.os,
                "getpid",
                lambda: owner_process_id + 1,
            )
            with pytest.raises(
                DatabaseError,
                match="only be used in their creating process",
            ):
                db.execute("SELECT 1")
    finally:
        db.close()


def test_mongodb_helper_rejects_cross_thread_use_before_collection_access():
    collection_accesses = []

    class Connection:
        def __getitem__(self, name):
            collection_accesses.append(name)
            raise AssertionError("driver must not be reached")

        def close(self):
            pass

    db = Database.__new__(Database)
    db.engine = "mongodb"
    db.connection = Connection()
    db.cursor = None
    db._driver_owner = None
    db._pool = None
    db._transaction_active = False
    db._transaction_depth = 0
    db._savepoint_counter = 0
    db._savepoints = []
    db._prev_autocommit = None
    db._owner_process_id = os.getpid()
    db._owner_thread = threading.current_thread()
    db._unsafe_allow_cross_thread = False

    outcome = _call_in_thread(
        lambda: db.insert("records", {"value": "private"})
    )

    assert isinstance(outcome, DatabaseError)
    assert collection_accesses == []
    db.close()


@pytest.mark.parametrize(
    ("operation", "error_type"),
    [
        (
            lambda db, path: DataExporter(db).to_sql("records", str(path)),
            ExportError,
        ),
        (
            lambda db, path: DataImporter(db).from_sql(str(path)),
            DatabaseImportError,
        ),
        (
            lambda db, path: BackupRestore(db)._require_sqlite("Backup"),
            DatabaseError,
        ),
    ],
)
def test_direct_sqlite_driver_paths_enforce_thread_ownership(
    tmp_path,
    operation,
    error_type,
):
    db = Database(
        engine="sqlite",
        database=":memory:",
        check_same_thread=False,
    )
    path = tmp_path / "payload.sql"
    path.write_text("SELECT 1;", encoding="utf-8")
    try:
        outcome = _call_in_thread(lambda: operation(db, path))

        assert isinstance(outcome, error_type)
        ownership_error = outcome
        while (
            "creating thread" not in str(ownership_error)
            and ownership_error.__cause__ is not None
        ):
            ownership_error = ownership_error.__cause__
        assert "creating thread" in str(ownership_error)
    finally:
        db.close()
