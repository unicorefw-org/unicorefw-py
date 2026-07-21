"""Security tests for SQL query construction and export source selection."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from unicorefw.db import (
    Database,
    DatabaseError,
    DataExporter,
    ExportError,
    QueryBuilder,
    unsafe_raw_sql,
)


def _create_users_database() -> Database:
    db = Database(engine="sqlite", database=":memory:")
    db.create_table(
        "users",
        {
            "id": "INTEGER PRIMARY KEY",
            "name": "TEXT",
            "age": "INTEGER",
            "active": "BOOLEAN",
        },
    )
    db.insert("users", {"id": 1, "name": "Alice", "age": 30, "active": True})
    db.insert("users", {"id": 2, "name": "Bob", "age": 17, "active": False})
    db.commit()
    return db


def test_query_builder_quotes_identifiers_and_binds_values():
    db = _create_users_database()
    hostile_value = "Alice' OR 1=1 --"
    try:
        builder = (
            QueryBuilder(db)
            .select("users.id", "users.name")
            .from_table("users")
            .where("users.name = ?", hostile_value)
            .where("users.active = ?", True)
            .order_by("users.id", "DESC")
            .limit(10)
            .offset(0)
        )

        query, params = builder.build()

        assert query == (
            'SELECT "users"."id", "users"."name" FROM "users" '
            'WHERE "users"."name" = ? AND "users"."active" = ? '
            'ORDER BY "users"."id" DESC LIMIT 10 OFFSET 0'
        )
        assert params == (hostile_value, True)
        assert hostile_value not in query
        assert builder.execute() == []
    finally:
        db.close()


def test_query_builder_executes_safe_predicates():
    db = _create_users_database()
    try:
        result = (
            QueryBuilder(db)
            .select("id", "name")
            .from_table("users")
            .where("age >= ?", 18)
            .where("active = ?", True)
            .order_by("id")
            .execute()
        )
        assert result == [{"id": 1, "name": "Alice"}]
    finally:
        db.close()


def test_query_builder_supports_null_predicate_and_safe_join():
    builder = (
        QueryBuilder(engine="postgres")
        .select("users.id", "profiles.bio")
        .from_table("users")
        .join("profiles", "users.id = profiles.user_id", "LEFT")
        .where("users.deleted_at IS NULL")
        .group_by("users.id", "profiles.bio")
        .having("users.id >= %s", 1)
    )

    query, params = builder.build()

    assert query == (
        'SELECT "users"."id", "profiles"."bio" FROM "users" '
        'LEFT JOIN "profiles" ON "users"."id" = "profiles"."user_id" '
        'WHERE "users"."deleted_at" IS NULL '
        'GROUP BY "users"."id", "profiles"."bio" '
        'HAVING "users"."id" >= %s'
    )
    assert params == (1,)


@pytest.mark.parametrize(
    "build",
    [
        lambda: QueryBuilder().select("id; DROP TABLE users; --"),
        lambda: QueryBuilder().from_table("users; DROP TABLE users; --"),
        lambda: QueryBuilder().join("profiles; DROP TABLE users; --", "a.id = b.id"),
        lambda: QueryBuilder().join("profiles", "1=1; DROP TABLE users; --"),
        lambda: QueryBuilder().where("name = ?; DROP TABLE users; --", "Alice"),
        lambda: QueryBuilder().group_by("id; DROP TABLE users; --"),
        lambda: QueryBuilder().having("COUNT(*) > 0; DROP TABLE users; --"),
        lambda: QueryBuilder().order_by("id; DROP TABLE users; --"),
        lambda: QueryBuilder().order_by("id", "ASC; DROP TABLE users; --"),
        lambda: QueryBuilder().limit("1; DROP TABLE users; --"),
        lambda: QueryBuilder().offset("0; DROP TABLE users; --"),
    ],
)
def test_query_builder_rejects_raw_injection_fragments(build):
    with pytest.raises((DatabaseError, TypeError, ValueError)):
        build()


@pytest.mark.parametrize("value", [-1, True, 1_000_001])
def test_query_builder_rejects_invalid_limits(value):
    with pytest.raises(DatabaseError):
        QueryBuilder(max_limit=1_000_000).limit(value)


@pytest.mark.parametrize("value", [-1, True, 1_000_001])
def test_query_builder_rejects_invalid_offsets(value):
    with pytest.raises(DatabaseError):
        QueryBuilder(max_offset=1_000_000).offset(value)


def test_query_builder_rejects_placeholder_parameter_mismatch():
    with pytest.raises(DatabaseError, match="exactly one bound parameter"):
        QueryBuilder().where("name = ?")

    with pytest.raises(DatabaseError, match="does not accept bound parameters"):
        QueryBuilder().where("deleted_at IS NULL", None)


def test_explicit_unsafe_sql_escape_hatch_is_visible_in_call_site():
    builder = (
        QueryBuilder()
        .select(unsafe_raw_sql("COUNT(*) AS total"))
        .from_table("users")
        .where(unsafe_raw_sql('"age" > ?'), 18)
        .order_by(unsafe_raw_sql("COUNT(*)"), "DESC")
    )

    query, params = builder.build()

    assert query == (
        'SELECT COUNT(*) AS total FROM "users" WHERE "age" > ? '
        "ORDER BY COUNT(*) DESC"
    )
    assert params == (18,)


@pytest.mark.parametrize("sql", ["", "   ", "SELECT 1\x00"])
def test_unsafe_sql_rejects_empty_or_null_containing_fragments(sql):
    with pytest.raises(DatabaseError):
        unsafe_raw_sql(sql)


def test_exporter_requires_table_name_or_explicit_unsafe_query(tmp_path: Path):
    db = _create_users_database()
    output_path = tmp_path / "users.json"
    try:
        with pytest.raises(ExportError, match="Unsafe SQL identifier"):
            DataExporter(db).to_json("SELECT * FROM users", str(output_path), params=())

        DataExporter(db).to_json(
            unsafe_raw_sql("SELECT id, name FROM users WHERE age >= ?"),
            str(output_path),
            params=(18,),
        )
        assert json.loads(output_path.read_text(encoding="utf-8")) == [
            {"id": 1, "name": "Alice"}
        ]
    finally:
        db.close()


def test_exporter_rejects_injected_table_name_without_touching_database(
    tmp_path: Path,
):
    db = _create_users_database()
    try:
        with pytest.raises(ExportError, match="Unsafe SQL identifier"):
            DataExporter(db).to_json(
                "users; DROP TABLE users; --", str(tmp_path / "users.json")
            )

        assert db.fetch_one("SELECT COUNT(*) AS count FROM users") == {"count": 2}
    finally:
        db.close()
