"""Security and round-trip tests for database export and restore helpers."""

from __future__ import annotations

import gzip
import json
import os
import tempfile
from pathlib import Path

import pytest

from unicorefw.db import (
    BackupRestore,
    Database,
    DatabaseError,
    DataExporter,
    DataImporter,
)

ADVERSARIAL_TEXT = "x'); DROP TABLE items; --"


def _create_items_database() -> Database:
    db = Database(engine="sqlite", database=":memory:")
    db.create_table(
        "items",
        {
            "id": "INTEGER PRIMARY KEY",
            "text_value": "TEXT",
            "blob_value": "BLOB",
            "number_value": "REAL",
            "nullable_value": "TEXT",
        },
    )
    db.insert(
        "items",
        {
            "id": 1,
            "text_value": ADVERSARIAL_TEXT,
            "blob_value": b"\x00\xffbinary",
            "number_value": 12.5,
            "nullable_value": None,
        },
    )
    db.insert(
        "items",
        {
            "id": 2,
            "text_value": "O'Reilly\nsecond line",
            "blob_value": b"",
            "number_value": -7,
            "nullable_value": "present",
        },
    )
    db.commit()
    return db


def _item_rows(db: Database):
    return db.fetch_all("SELECT * FROM items ORDER BY id")


def test_sql_export_round_trips_adversarial_values(tmp_path: Path):
    source = _create_items_database()
    target = Database(engine="sqlite", database=":memory:")
    dump_path = tmp_path / "items.sql"

    try:
        DataExporter(source).to_sql("items", str(dump_path))
        dump_text = dump_path.read_text(encoding="utf-8")

        assert "DROP TABLE items" in dump_text
        assert "x''); DROP TABLE items; --" in dump_text

        DataImporter(target).from_sql(str(dump_path))
        assert _item_rows(target) == _item_rows(source)
    finally:
        source.close()
        target.close()


def test_compressed_sql_backup_round_trips_and_removes_plaintext(tmp_path: Path):
    source = _create_items_database()
    target = Database(engine="sqlite", database=":memory:")
    plain_path = tmp_path / "snapshot.sql"

    try:
        compressed_path = BackupRestore(source).backup(
            str(plain_path), format="sql", compress=True
        )

        assert compressed_path == f"{plain_path}.gz"
        assert Path(compressed_path).is_file()
        assert not plain_path.exists()

        BackupRestore(target).restore(compressed_path, format="sql")
        assert _item_rows(target) == _item_rows(source)
    finally:
        source.close()
        target.close()


def test_destructive_restore_requires_explicit_authorization(tmp_path: Path):
    source = _create_items_database()
    target = Database(engine="sqlite", database=":memory:")
    target.create_table("items", {"id": "INTEGER PRIMARY KEY", "marker": "TEXT"})
    target.insert("items", {"id": 99, "marker": "keep"})
    target.commit()
    backup_path = tmp_path / "snapshot.sql"

    try:
        BackupRestore(source).backup(str(backup_path), format="sql")

        with pytest.raises(DatabaseError, match="allow_destructive=True"):
            BackupRestore(target).restore(
                str(backup_path), format="sql", clear_existing=True
            )

        assert target.fetch_one("SELECT marker FROM items WHERE id = 99") == {
            "marker": "keep"
        }

        BackupRestore(target).restore(
            str(backup_path),
            format="sql",
            clear_existing=True,
            allow_destructive=True,
        )
        assert _item_rows(target) == _item_rows(source)
    finally:
        source.close()
        target.close()


def test_restore_default_preserves_existing_tables_on_conflict(tmp_path: Path):
    source = _create_items_database()
    target = Database(engine="sqlite", database=":memory:")
    target.create_table("items", {"id": "INTEGER PRIMARY KEY", "marker": "TEXT"})
    target.insert("items", {"id": 99, "marker": "keep"})
    target.commit()
    backup_path = tmp_path / "snapshot.sql"

    try:
        BackupRestore(source).backup(str(backup_path), format="sql")

        with pytest.raises(DatabaseError, match="Restore failed"):
            BackupRestore(target).restore(str(backup_path), format="sql")

        assert target.fetch_one("SELECT marker FROM items WHERE id = 99") == {
            "marker": "keep"
        }
    finally:
        source.close()
        target.close()


def test_restore_rejects_gzip_output_over_byte_limit(tmp_path: Path):
    backup_path = tmp_path / "oversized.sql.gz"
    with gzip.open(backup_path, "wb") as stream:
        stream.write(b"A" * 4096)

    db = Database(engine="sqlite", database=":memory:")
    try:
        with pytest.raises(DatabaseError, match="uncompressed byte limit"):
            BackupRestore(db).restore(
                str(backup_path),
                format="sql",
                max_uncompressed_bytes=128,
            )
    finally:
        db.close()


def test_failed_gzip_restore_removes_secure_temporary_file(tmp_path: Path, monkeypatch):
    backup_path = tmp_path / "oversized.sql.gz"
    with gzip.open(backup_path, "wb") as stream:
        stream.write(b"A" * 4096)

    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    db = Database(engine="sqlite", database=":memory:")
    try:
        with pytest.raises(DatabaseError, match="uncompressed byte limit"):
            BackupRestore(db).restore(
                str(backup_path),
                format="sql",
                max_uncompressed_bytes=128,
            )
        assert list(tmp_path.glob(".unicorefw-backup-*")) == []
    finally:
        db.close()


def test_restore_rejects_gzip_over_compression_ratio_limit(tmp_path: Path):
    backup_path = tmp_path / "ratio.sql.gz"
    with gzip.open(backup_path, "wb") as stream:
        stream.write(b"A" * 64_000)

    db = Database(engine="sqlite", database=":memory:")
    try:
        with pytest.raises(DatabaseError, match="compression ratio limit"):
            BackupRestore(db).restore(
                str(backup_path),
                format="sql",
                max_uncompressed_bytes=128_000,
                max_compression_ratio=2.0,
            )
    finally:
        db.close()


def test_backup_and_restore_reject_unsupported_formats(tmp_path: Path):
    db = Database(engine="sqlite", database=":memory:")
    try:
        with pytest.raises(DatabaseError, match="Unsupported backup format"):
            BackupRestore(db).backup(str(tmp_path / "snapshot.csv"), format="csv")

        with pytest.raises(DatabaseError, match="Unsupported restore format"):
            BackupRestore(db).restore(str(tmp_path / "snapshot.yaml"), format="yaml")
    finally:
        db.close()


def test_backup_rejects_engines_without_native_dump_support(tmp_path: Path):
    db = Database(engine="sqlite", database=":memory:")
    db.engine = "postgres"
    try:
        with pytest.raises(DatabaseError, match="SQLite"):
            BackupRestore(db).backup(str(tmp_path / "snapshot.sql"), format="sql")
    finally:
        db.close()


def test_backup_rejects_uncommitted_database_state(tmp_path: Path):
    db = Database(engine="sqlite", database=":memory:")
    db.execute("CREATE TABLE items(value TEXT)")
    db.execute("INSERT INTO items(value) VALUES (?)", ("uncommitted",))
    backup_path = tmp_path / "snapshot.sql"

    try:
        with pytest.raises(DatabaseError, match="Commit or rollback"):
            BackupRestore(db).backup(str(backup_path), format="sql")
        assert not backup_path.exists()
    finally:
        db.rollback()
        db.close()


def test_json_backup_has_versioned_envelope_and_restores(tmp_path: Path):
    source = _create_items_database()
    target = Database(engine="sqlite", database=":memory:")
    backup_path = tmp_path / "snapshot.json"

    try:
        BackupRestore(source).backup(str(backup_path), format="json")
        payload = json.loads(backup_path.read_text(encoding="utf-8"))

        assert payload["format"] == "unicorefw.database-backup"
        assert payload["version"] == 1
        assert payload["engine"] == "sqlite"
        assert "items" in payload["tables"]

        BackupRestore(target).restore(str(backup_path), format="json")
        restored = _item_rows(target)
        expected = _item_rows(source)

        assert restored == expected
    finally:
        source.close()
        target.close()


def test_restore_accepts_legacy_json_backup(tmp_path: Path):
    backup_path = tmp_path / "legacy.json"
    backup_path.write_text(
        json.dumps({"items": [{"id": 1, "text_value": "legacy"}]}),
        encoding="utf-8",
    )
    db = Database(engine="sqlite", database=":memory:")

    try:
        BackupRestore(db).restore(str(backup_path), format="json")
        assert db.fetch_one("SELECT id, text_value FROM items") == {
            "id": 1,
            "text_value": "legacy",
        }
    finally:
        db.close()


def test_drop_table_rejects_injected_identifier():
    db = Database(engine="sqlite", database=":memory:")
    db.create_table("safe", {"id": "INTEGER"})
    db.create_table("victim", {"id": "INTEGER"})

    try:
        with pytest.raises(DatabaseError, match="Unsafe SQL identifier"):
            db.drop_table("safe; DROP TABLE victim; --")

        names = {
            row["name"]
            for row in db.fetch_all(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
        }
        assert {"safe", "victim"}.issubset(names)
    finally:
        db.close()


def test_sql_restore_denies_database_attachment(tmp_path: Path):
    attached_path = tmp_path / "attached.db"
    backup_path = tmp_path / "untrusted.sql"
    backup_path.write_text(
        f"ATTACH DATABASE '{attached_path}' AS attached; "
        "CREATE TABLE attached.exfiltrated(value TEXT);",
        encoding="utf-8",
    )
    db = Database(engine="sqlite", database=":memory:")

    try:
        with pytest.raises(DatabaseError, match="not authorized"):
            BackupRestore(db).restore(str(backup_path), format="sql")
        assert not attached_path.exists()
    finally:
        db.close()


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits are not portable")
def test_backup_file_uses_owner_only_permissions(tmp_path: Path):
    db = _create_items_database()
    backup_path = tmp_path / "snapshot.sql"

    try:
        BackupRestore(db).backup(str(backup_path), format="sql")
        assert backup_path.stat().st_mode & 0o777 == 0o600
    finally:
        db.close()
