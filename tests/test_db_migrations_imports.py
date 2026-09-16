"""Migration and importer integrity regression tests."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

import unicorefw.db as db_module
from unicorefw.db import (
    Database,
    DatabaseError,
    DatabaseImportError,
    DataImporter,
    Migration,
    QueryError,
)


class _DriverMigrationDatabase:
    """Minimal DB-API facade for driver-native migration assertions."""

    def __init__(self, engine: str):
        self.engine = engine
        self.created_schema = None
        self.executed = []
        self.inserted = []
        self.deleted = []

    def create_table(self, table, schema):
        self.created_schema = (table, schema)

    def fetch_one(self, query, params):
        self.executed.append((query, params))

    def execute(self, query, params=None):
        self.executed.append((query, params))

    def insert(self, table, data):
        self.inserted.append((table, data))

    def delete(self, table, where):
        self.deleted.append((table, where))

    def fetch_all(self, query):
        self.executed.append((query, None))
        return []

    @contextmanager
    def transaction(self):
        yield self


def _table_exists(db: Database, table: str) -> bool:
    return (
        db.fetch_one(
            "SELECT 1 AS present FROM sqlite_master "
            "WHERE type = 'table' AND name = ?",
            (table,),
        )
        is not None
    )


def test_migration_preserves_semicolons_and_verifies_checksum():
    db = Database(engine="sqlite", database=":memory:")
    migration = Migration(db)
    up_sql = """
        CREATE TABLE notes (id INTEGER PRIMARY KEY, body TEXT);
        CREATE TABLE note_audit (body TEXT);
        CREATE TRIGGER notes_after_insert
        AFTER INSERT ON notes
        BEGIN
            INSERT INTO note_audit(body) VALUES (NEW.body || ';logged');
        END;
        INSERT INTO notes(id, body) VALUES (1, 'alpha;beta');
    """
    try:
        assert migration.apply("001", up_sql) is True
        assert db.fetch_one("SELECT body FROM notes") == {"body": "alpha;beta"}
        assert db.fetch_one("SELECT body FROM note_audit") == {
            "body": "alpha;beta;logged"
        }

        status = migration.status()
        assert status[0]["version"] == "001"
        assert status[0]["checksum"] == hashlib.sha256(
            up_sql.encode("utf-8")
        ).hexdigest()
        assert migration.apply("001", up_sql) is False

        with pytest.raises(DatabaseError, match="checksum"):
            migration.apply("001", "SELECT 1")

        migration.rollback(
            "001",
            "DROP TRIGGER notes_after_insert;"
            "DROP TABLE note_audit;"
            "DROP TABLE notes;",
        )
        assert migration.status() == []
        assert not _table_exists(db, "notes")
    finally:
        db.close()


def test_failed_migration_rolls_back_schema_data_and_tracking_row():
    db = Database(engine="sqlite", database=":memory:")
    migration = Migration(db)
    try:
        with pytest.raises(QueryError):
            migration.apply(
                "broken",
                "CREATE TABLE transient_items (id INTEGER);"
                "INSERT INTO transient_items(id) VALUES (1);"
                "INSERT INTO missing_table(id) VALUES (2);",
            )

        assert not _table_exists(db, "transient_items")
        assert migration.status() == []
    finally:
        db.close()


@pytest.mark.parametrize("version", [None, "", "  ", "bad\x00value", "x" * 256])
def test_migration_rejects_invalid_versions(version):
    db = Database(engine="sqlite", database=":memory:")
    try:
        migration = Migration(db)
        with pytest.raises(DatabaseError, match="Migration version"):
            migration.apply(version, "SELECT 1")  # type: ignore[arg-type]
    finally:
        db.close()


@pytest.mark.parametrize("script", [None, "", "  ", "SELECT\x00 1"])
def test_migration_rejects_invalid_up_and_down_scripts(script):
    db = Database(engine="sqlite", database=":memory:")
    try:
        migration = Migration(db)
        with pytest.raises(DatabaseError, match="Migration up SQL"):
            migration.apply("001", script)  # type: ignore[arg-type]
        with pytest.raises(DatabaseError, match="Migration down SQL"):
            migration.rollback("001", script)  # type: ignore[arg-type]
    finally:
        db.close()


@pytest.mark.parametrize(
    ("engine", "expected_primary_key"),
    [
        ("sqlite", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("postgres", "BIGSERIAL PRIMARY KEY"),
        ("mysql", "BIGINT AUTO_INCREMENT PRIMARY KEY"),
    ],
)
def test_migration_uses_engine_specific_tracking_schema(
    engine,
    expected_primary_key,
):
    db = _DriverMigrationDatabase(engine)
    Migration(db)  # type: ignore[arg-type]
    assert db.created_schema[0] == "_migrations" # type: ignore
    assert db.created_schema[1]["id"] == expected_primary_key # type: ignore


def test_migration_rejects_unsupported_engine():
    with pytest.raises(DatabaseError, match="not supported"):
        Migration(_DriverMigrationDatabase("redis"))  # type: ignore[arg-type]


def test_non_sqlite_migration_delegates_complete_script_to_driver():
    db = _DriverMigrationDatabase("postgres")
    migration = Migration(db)  # type: ignore[arg-type]
    script = "DO $$ BEGIN PERFORM 'alpha;beta'; END $$;"

    assert migration.apply("001", script) is True
    assert (script, None) in db.executed
    assert db.inserted[0][0] == "_migrations"

    down_script = "DO $$ BEGIN PERFORM 'down;value'; END $$;"
    migration.rollback("001", down_script)
    assert (down_script, None) in db.executed
    assert db.deleted == [("_migrations", {"version": "001"})]


def test_mysql_migration_preserves_multi_statement_compatibility():
    db = _DriverMigrationDatabase("mysql")
    migration = Migration(db)  # type: ignore[arg-type]
    script = (
        "INSERT INTO messages(value) VALUES ('alpha;beta');"
        r"INSERT INTO messages(value) VALUES ('escaped\';semi');"
        "-- keep this ; comment\n"
        'UPDATE messages SET value = "gamma;delta";'
        "/* block ; comment */"
        "DELETE FROM `archive;2025` WHERE value = 'it''s;old';"
        "SELECT 1--2;"
    )

    assert migration.apply("001", script) is True
    executed_statements = [
        query
        for query, params in db.executed
        if params is None
    ]
    assert len(executed_statements) == 5
    assert "'alpha;beta'" in executed_statements[0]
    assert r"'escaped\';semi'" in executed_statements[1]
    assert '"gamma;delta"' in executed_statements[2]
    assert "`archive;2025`" in executed_statements[3]
    assert "'it''s;old'" in executed_statements[3]
    assert executed_statements[4] == "SELECT 1--2;"


def test_transactional_create_and_drop_roll_back_with_body_failure():
    db = Database(engine="sqlite", database=":memory:")
    db.create_table("preserved", {"id": "INTEGER"})
    try:
        with pytest.raises(RuntimeError, match="abort"), db.transaction():
            db.create_table("transient", {"id": "INTEGER"})
            db.drop_table("preserved")
            raise RuntimeError("abort")

        assert not _table_exists(db, "transient")
        assert _table_exists(db, "preserved")
    finally:
        db.close()


def test_json_import_supports_single_records_batches_and_empty_lists(tmp_path: Path):
    single_path = tmp_path / "single.json"
    single_path.write_text(json.dumps({"id": 1, "name": "alpha"}), encoding="utf-8")
    batch_path = tmp_path / "batch.json"
    batch_path.write_text(
        json.dumps([{"id": 2, "name": "beta"}, {"id": 3, "name": "gamma"}]),
        encoding="utf-8",
    )
    empty_path = tmp_path / "empty.json"
    empty_path.write_text("[]", encoding="utf-8")

    db = Database(engine="sqlite", database=":memory:")
    importer = DataImporter(db)
    try:
        assert importer.from_json(str(single_path), "items") == 1
        assert (
            importer.from_json(
                str(batch_path),
                "items",
                create_table=False,
                batch_size=1,
            )
            == 2
        )
        assert importer.from_json(str(empty_path), "unused") == 0
        assert db.fetch_one("SELECT COUNT(*) AS count FROM items") == {"count": 3}
        assert not _table_exists(db, "unused")
    finally:
        db.close()


def test_json_import_redacts_parse_failures_and_chains_cause(tmp_path: Path):
    input_path = tmp_path / "private-customer-records.json"
    input_path.write_text("{invalid", encoding="utf-8")
    db = Database(engine="sqlite", database=":memory:")
    try:
        with pytest.raises(DatabaseImportError) as caught:
            DataImporter(db).from_json(str(input_path), "items")

        assert str(caught.value) == "JSON import failed"
        assert input_path.name not in str(caught.value)
        assert isinstance(caught.value.__cause__, json.JSONDecodeError)
    finally:
        db.close()


def test_json_import_rolls_back_auto_created_table_on_insert_failure(tmp_path: Path):
    input_path = tmp_path / "items.json"
    input_path.write_text(
        json.dumps([{"id": 1}, {"invalid-name": 2}]),
        encoding="utf-8",
    )
    db = Database(engine="sqlite", database=":memory:")
    try:
        with pytest.raises(DatabaseImportError, match="JSON import failed") as caught:
            DataImporter(db).from_json(str(input_path), "items")

        assert isinstance(caught.value.__cause__, DatabaseError)
        assert not _table_exists(db, "items")
    finally:
        db.close()


def test_csv_import_without_header_batches_rows(tmp_path: Path):
    input_path = tmp_path / "items.csv"
    input_path.write_text("1,alpha\n2,beta\n3,gamma\n", encoding="utf-8")
    db = Database(engine="sqlite", database=":memory:")
    try:
        inserted = DataImporter(db).from_csv(
            str(input_path),
            "items",
            has_header=False,
            batch_size=1,
        )
        assert inserted == 3
        assert db.fetch_all("SELECT * FROM items ORDER BY column_0") == [
            {"column_0": "1", "column_1": "alpha"},
            {"column_0": "2", "column_1": "beta"},
            {"column_0": "3", "column_1": "gamma"},
        ]
    finally:
        db.close()


def test_csv_import_redacts_parser_errors_and_rolls_back_created_table(
    tmp_path: Path,
):
    invalid_delimiter = tmp_path / "delimiter.csv"
    invalid_delimiter.write_text("id\n1\n", encoding="utf-8")
    invalid_row = tmp_path / "rows.csv"
    invalid_row.write_text("id\n1\n2,unexpected\n", encoding="utf-8")
    db = Database(engine="sqlite", database=":memory:")
    importer = DataImporter(db)
    try:
        with pytest.raises(DatabaseImportError) as caught:
            importer.from_csv(str(invalid_delimiter), "items", delimiter="::")
        assert str(caught.value) == "CSV import failed"
        assert isinstance(caught.value.__cause__, TypeError)

        with pytest.raises(DatabaseImportError, match="CSV import failed"):
            importer.from_csv(str(invalid_row), "items")
        assert not _table_exists(db, "items")
    finally:
        db.close()


def test_excel_import_uses_sheet_table_names_and_normalizes_nan(tmp_path: Path):
    pandas = pytest.importorskip("pandas")
    pytest.importorskip("openpyxl")
    input_path = tmp_path / "inventory.xlsx"
    pandas.DataFrame(
        [{"name": "alpha", "quantity": 1}, {"name": "beta", "quantity": None}]
    ).to_excel(input_path, index=False, sheet_name="Inventory")

    db = Database(engine="sqlite", database=":memory:")
    importer = DataImporter(db)
    try:
        assert (
            importer.from_excel(
                str(input_path),
                sheet_name="Inventory",
            )
            == 2
        )
        assert db.fetch_all("SELECT * FROM Inventory ORDER BY name") == [
            {"name": "alpha", "quantity": 1.0},
            {"name": "beta", "quantity": None},
        ]

        assert importer.from_excel(str(input_path), sheet_name=0) == 2
        assert _table_exists(db, "sheet_0")
    finally:
        db.close()


def test_excel_import_dependency_and_parser_failures_are_stable(
    tmp_path: Path,
    monkeypatch,
):
    db = Database(engine="sqlite", database=":memory:")
    importer = DataImporter(db)
    try:
        monkeypatch.setattr(db_module, "PANDAS_AVAILABLE", False)
        with pytest.raises(DatabaseImportError, match="pandas is required"):
            importer.from_excel(str(tmp_path / "missing.xlsx"))

        monkeypatch.setattr(db_module, "PANDAS_AVAILABLE", True)
        input_path = tmp_path / "private-workbook.xlsx"
        input_path.write_bytes(b"not an Excel workbook")
        with pytest.raises(DatabaseImportError) as caught:
            importer.from_excel(str(input_path))
        assert str(caught.value) == "Excel import failed"
        assert input_path.name not in str(caught.value)
        assert caught.value.__cause__ is not None
    finally:
        db.close()


def test_sql_import_is_atomic_and_preserves_semicolons(tmp_path: Path):
    success_path = tmp_path / "success.sql"
    success_path.write_text(
        "CREATE TABLE imported (value TEXT);"
        "INSERT INTO imported(value) VALUES ('alpha;beta');",
        encoding="utf-8",
    )
    failure_path = tmp_path / "failure.sql"
    failure_path.write_text(
        "INSERT INTO imported(value) VALUES ('must roll back');"
        "INSERT INTO missing_table(value) VALUES ('failure');",
        encoding="utf-8",
    )
    db = Database(engine="sqlite", database=":memory:")
    importer = DataImporter(db)
    try:
        assert importer.from_sql(str(success_path)) == 1
        assert db.fetch_all("SELECT value FROM imported") == [
            {"value": "alpha;beta"}
        ]

        with pytest.raises(DatabaseImportError, match="SQL import failed") as caught:
            importer.from_sql(str(failure_path))
        assert isinstance(caught.value.__cause__, sqlite3.DatabaseError)
        assert db.fetch_all("SELECT value FROM imported") == [
            {"value": "alpha;beta"}
        ]
    finally:
        db.close()


def test_sql_import_blocks_external_attachment(tmp_path: Path):
    attached_path = tmp_path / "should-not-exist.sqlite"
    script_path = tmp_path / "attach.sql"
    script_path.write_text(
        f"ATTACH DATABASE '{attached_path}' AS external;",
        encoding="utf-8",
    )
    db = Database(engine="sqlite", database=":memory:")
    try:
        with pytest.raises(DatabaseImportError, match="SQL import failed"):
            DataImporter(db).from_sql(str(script_path))
        assert not attached_path.exists()
    finally:
        db.close()


def test_sql_import_validates_encoding_engine_and_paths(tmp_path: Path):
    invalid_path = tmp_path / "invalid.sql"
    invalid_path.write_bytes(b"\xff")
    db = Database(engine="sqlite", database=":memory:")
    importer = DataImporter(db)
    try:
        with pytest.raises(DatabaseImportError, match="UTF-8") as caught:
            importer.from_sql(str(invalid_path))
        assert isinstance(caught.value.__cause__, UnicodeDecodeError)

        db.engine = "postgres"
        with pytest.raises(DatabaseImportError, match="SQLite only"):
            importer.from_sql(str(invalid_path))
        db.engine = "sqlite"

        with pytest.raises(DatabaseImportError) as missing:
            importer.from_sql(str(tmp_path / "private-missing.sql"))
        assert str(missing.value) == "SQL import failed"
        assert isinstance(missing.value.__cause__, OSError)
    finally:
        db.close()


def test_dictionary_import_infers_types_and_handles_empty_data():
    db = Database(engine="sqlite", database=":memory:")
    importer = DataImporter(db)
    sample = {
        "missing": None,
        "enabled": True,
        "count": 3,
        "ratio": 1.5,
        "created": datetime(2026, 7, 23),  # noqa: DTZ001
        "name": "alpha",
        "payload": object(),
    }
    try:
        assert importer._infer_schema(sample) == {
            "missing": "TEXT",
            "enabled": "BOOLEAN",
            "count": "INTEGER",
            "ratio": "REAL",
            "created": "TEXT",
            "name": "TEXT",
            "payload": "TEXT",
        }
        assert importer.from_dict({"id": 1, "name": "alpha"}, "items") == 1
        assert importer.from_dict([], "unused") == 0
        assert not _table_exists(db, "unused")
    finally:
        db.close()


def test_dictionary_import_validation_and_insert_failure_are_atomic():
    db = Database(engine="sqlite", database=":memory:")
    importer = DataImporter(db)
    try:
        with pytest.raises(DatabaseImportError, match="dict or list"):
            importer.from_dict("invalid", "items")  # type: ignore[arg-type]

        with pytest.raises(
            DatabaseImportError,
            match="dictionary import failed",
        ) as caught:
            importer.from_dict([{"id": 1}, {"invalid-name": 2}], "items")
        assert isinstance(caught.value.__cause__, DatabaseError)
        assert not _table_exists(db, "items")
    finally:
        db.close()


@pytest.mark.parametrize(
    ("method_name", "format_name"),
    [
        ("from_json", "JSON"),
        ("from_csv", "CSV"),
        ("from_excel", "Excel"),
    ],
)
def test_file_importers_reject_non_text_paths(method_name, format_name):
    if method_name == "from_excel" and not db_module.PANDAS_AVAILABLE:
        pytest.skip("pandas is not installed")
    db = Database(engine="sqlite", database=":memory:")
    importer = DataImporter(db)
    try:
        with pytest.raises(DatabaseImportError) as caught:
            getattr(importer, method_name)(None, "items")  # type: ignore[arg-type]
        assert str(caught.value) == f"{format_name} import failed"
        assert isinstance(caught.value.__cause__, DatabaseError)
    finally:
        db.close()
