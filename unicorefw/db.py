"""
File: unicorefw/db.py
Database utilities for UniCoreFW.

This module provides comprehensive database functionality including connection management,
query execution, migrations, import/export, and support for multiple database engines.

Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info

This file is part of UniCoreFW. You can redistribute it and/or modify
it under the terms of the [BSD-3-Clause] as published by
the Free Software Foundation.
You should have received a copy of the [BSD-3-Clause] license
along with UniCoreFW. If not, see https://www.gnu.org/licenses/.
"""

import base64
import copy
import csv
import gzip
import hashlib
import html as html_lib
import io
import json
import os
import re
import sqlite3
import tempfile
import threading
import time
import zipfile
from collections import OrderedDict
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from .security import (
    InputValidationError,
    ResourceLimitError,
    _estimate_resource_weight,
    _validate_resource_duration,
    _validate_resource_limit,
    _validate_resource_ratio,
)
# from pathlib import Path

# Optional imports for additional database support
try:
    import psycopg2 # type: ignore
    import psycopg2.extras # type: ignore
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

try:
    import pymysql # type: ignore
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

try:
    import pymongo # type: ignore
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

try:
    import redis # type: ignore
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import pandas as pd # type: ignore
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import openpyxl # type: ignore  # noqa: F401
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

_ordered_dict_clear = OrderedDict.clear


class DatabaseError(Exception):
    """Base exception for database-related errors."""
    pass


class ConnectionError(DatabaseError):
    """Raised when database connection fails."""
    pass


class QueryError(DatabaseError):
    """Raised when query execution fails."""
    pass


class ExportError(DatabaseError):
    """Raised when data export fails."""
    pass


class ImportError(DatabaseError):
    """Raised when data import fails."""
    pass

# ──────────────────────────────────────────────────────────────────────────────
# Security-first SQL identifier handling
#   - Prevent table/column injection in helper APIs that interpolate identifiers
#   - Support schema-qualified tables (schema.table)
#   - Quote identifiers for engines that support it
# ──────────────────────────────────────────────────────────────────────────────

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_BACKUP_FORMAT_NAME = "unicorefw.database-backup"
_BACKUP_FORMAT_VERSION = 1
_COPY_CHUNK_SIZE = 1024 * 1024
_DEFAULT_MAX_RESTORE_BYTES = 512 * 1024 * 1024
_DEFAULT_MAX_COMPRESSION_RATIO = 200.0
_HARD_MAX_RESTORE_BYTES = 1024 * 1024 * 1024
_HARD_MAX_RESTORE_COMPRESSION_RATIO = 1_000.0
_DEFAULT_MAX_IMPORT_BYTES = 64 * 1024 * 1024
_DEFAULT_MAX_IMPORT_ROWS = 100_000
_DEFAULT_MAX_IMPORT_COLUMNS = 1_000
_DEFAULT_MAX_EXCEL_EXPANDED_BYTES = 512 * 1024 * 1024
_DEFAULT_MAX_ARCHIVE_MEMBERS = 100_000
_HARD_MAX_IMPORT_BYTES = 512 * 1024 * 1024
_HARD_MAX_IMPORT_ROWS = 1_000_000
_HARD_MAX_IMPORT_COLUMNS = 10_000
_HARD_MAX_IMPORT_BATCH_SIZE = 100_000
_HARD_MAX_EXCEL_EXPANDED_BYTES = 1024 * 1024 * 1024
_HARD_MAX_ARCHIVE_MEMBERS = 250_000
_HARD_MAX_IMPORT_COMPRESSION_RATIO = 1_000.0
_DEFAULT_CACHE_MAX_ENTRIES = 256
_DEFAULT_CACHE_MAX_WEIGHT_BYTES = 16 * 1024 * 1024
_HARD_MAX_CACHE_ENTRIES = 100_000
_HARD_MAX_CACHE_WEIGHT_BYTES = 256 * 1024 * 1024
_HARD_MAX_CACHE_TTL_SECONDS = 7 * 24 * 60 * 60
_SQL_FIELD_PATTERN = r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*"
_SQL_CONDITION_RE = re.compile(
    rf"^\s*(?P<field>{_SQL_FIELD_PATTERN})\s*"
    r"(?P<operator>IS\s+NOT|NOT\s+LIKE|IS|LIKE|<=|>=|<>|!=|=|<|>)\s*"
    r"(?P<value>\?|%s|NULL)\s*$",
    flags=re.IGNORECASE,
)
_SQL_JOIN_RE = re.compile(
    rf"^\s*(?P<left>{_SQL_FIELD_PATTERN})\s*"
    r"(?P<operator><=|>=|<>|!=|=|<|>)\s*"
    rf"(?P<right>{_SQL_FIELD_PATTERN})\s*$",
    flags=re.IGNORECASE,
)
_SQL_JOIN_TYPES = {
    "INNER",
    "LEFT",
    "LEFT OUTER",
    "RIGHT",
    "RIGHT OUTER",
    "FULL",
    "FULL OUTER",
}
_SQL_ORDER_DIRECTIONS = {"ASC", "DESC"}
_SPREADSHEET_FORMULA_PREFIXES = ("=", "+", "-", "@")


class UnsafeSQL:
    """An explicit, trusted SQL fragment that bypasses structural validation."""

    __slots__ = ("_sql",)

    def __init__(self, sql: str):
        if not isinstance(sql, str) or not sql.strip() or "\x00" in sql:
            raise DatabaseError(
                "Unsafe SQL fragment must be non-empty text without null bytes"
            )
        self._sql = sql

    @property
    def sql(self) -> str:
        return self._sql

    def __repr__(self) -> str:
        return "UnsafeSQL(<trusted fragment>)"


def unsafe_raw_sql(sql: str) -> UnsafeSQL:
    """Mark a trusted SQL fragment and make the bypass visible at the call site."""
    return UnsafeSQL(sql)


class UnsafeCSS:
    """Explicitly trusted CSS that bypasses HTML export's safe default."""

    __slots__ = ("_css",)

    def __init__(self, css: str):
        if not isinstance(css, str) or not css.strip() or "\x00" in css:
            raise ExportError(
                "Unsafe CSS must be non-empty text without null bytes"
            )
        self._css = css

    @property
    def css(self) -> str:
        return self._css

    def __repr__(self) -> str:
        return "UnsafeCSS(<trusted stylesheet>)"


def unsafe_raw_css(css: str) -> UnsafeCSS:
    """Mark a reviewed stylesheet as trusted for HTML export."""
    return UnsafeCSS(css)


def _spreadsheet_safe_cell(value: Any) -> Any:
    """Force formula-looking text to remain text in CSV and Excel clients."""
    if not isinstance(value, str):
        return value
    candidate = value.lstrip()
    if value.startswith(("\t", "\r", "\n")) or candidate.startswith(
        _SPREADSHEET_FORMULA_PREFIXES
    ):
        return "'" + value
    return value


def _validate_ident(name: str) -> None:
    if not isinstance(name, str) or not _IDENT_RE.match(name):
        raise DatabaseError(f"Unsafe SQL identifier: {name!r}")


def _split_table(table: str) -> List[str]:
    if not isinstance(table, str) or not table:
        raise DatabaseError("Table name must be a non-empty string")
    parts = table.split(".")
    for p in parts:
        _validate_ident(p)
    return parts


def _qident(engine: str, ident: str) -> str:
    _validate_ident(ident)
    if engine in ("postgres", "sqlite"):
        return f'"{ident}"'
    if engine == "mysql":
        return f"`{ident}`"
    return ident


def _qtable(engine: str, table: str) -> str:
    return ".".join(_qident(engine, p) for p in _split_table(table))


def _qfield(engine: str, field: str) -> str:
    if not isinstance(field, str) or not field:
        raise DatabaseError("SQL field must be a non-empty string")
    if field == "*":
        return field

    parts = field.split(".")
    rendered = []
    for index, part in enumerate(parts):
        if part == "*" and index == len(parts) - 1:
            rendered.append(part)
            continue
        rendered.append(_qident(engine, part))
    return ".".join(rendered)


def _render_sql_field(engine: str, field: Union[str, UnsafeSQL]) -> str:
    if isinstance(field, UnsafeSQL):
        return field.sql
    return _qfield(engine, field)


def _sql_placeholder(engine: str) -> str:
    return "?" if engine == "sqlite" else "%s"


def _compile_sql_condition(
    engine: str,
    condition: Union[str, UnsafeSQL],
    params: Tuple[Any, ...],
) -> Tuple[str, Tuple[Any, ...]]:
    if isinstance(condition, UnsafeSQL):
        return condition.sql, params
    if not isinstance(condition, str):
        raise DatabaseError(
            "SQL condition must use the simple condition grammar or unsafe_raw_sql()"
        )

    match = _SQL_CONDITION_RE.fullmatch(condition)
    if match is None:
        raise DatabaseError(
            "SQL condition must be '<field> <operator> <placeholder|NULL>'; "
            "use unsafe_raw_sql() for a reviewed complex expression"
        )

    operator = " ".join(match.group("operator").upper().split())
    value_token = match.group("value").upper()
    if value_token == "NULL":
        if params:
            raise DatabaseError("A NULL condition does not accept bound parameters")
        if operator not in {"IS", "IS NOT"}:
            raise DatabaseError("NULL conditions require IS or IS NOT")
        rendered_value = "NULL"
    else:
        if len(params) != 1:
            raise DatabaseError(
                "A simple SQL condition requires exactly one bound parameter"
            )
        if operator in {"IS", "IS NOT"}:
            raise DatabaseError("Bound values do not support IS or IS NOT")
        rendered_value = _sql_placeholder(engine)

    return (
        f"{_qfield(engine, match.group('field'))} {operator} {rendered_value}",
        params,
    )


def _compile_sql_join(
    engine: str, condition: Union[str, UnsafeSQL]
) -> str:
    if isinstance(condition, UnsafeSQL):
        return condition.sql
    if not isinstance(condition, str):
        raise DatabaseError(
            "JOIN condition must compare two fields or use unsafe_raw_sql()"
        )

    match = _SQL_JOIN_RE.fullmatch(condition)
    if match is None:
        raise DatabaseError(
            "JOIN condition must be '<field> <operator> <field>'; "
            "use unsafe_raw_sql() for a reviewed complex expression"
        )
    return (
        f"{_qfield(engine, match.group('left'))} "
        f"{match.group('operator')} "
        f"{_qfield(engine, match.group('right'))}"
    )


def _validate_positive_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise DatabaseError(f"{name} must be a positive integer")
    return value


class _BoundedBinaryReader(io.RawIOBase):
    """Expose a binary stream that raises after a fixed byte budget."""

    def __init__(self, source, limit: int, resource: str):
        super().__init__()
        self.source = source
        self.limit = limit
        self.resource = resource
        self.total_read = 0

    def readable(self) -> bool:
        return True

    def readinto(self, buffer) -> int:
        remaining_with_probe = self.limit - self.total_read + 1
        if remaining_with_probe <= 0:
            raise ResourceLimitError(
                self.resource,
                self.limit,
                self.total_read,
            )
        chunk = self.source.read(min(len(buffer), remaining_with_probe))
        if not chunk:
            return 0
        self.total_read += len(chunk)
        if self.total_read > self.limit:
            raise ResourceLimitError(
                self.resource,
                self.limit,
                self.total_read,
            )
        buffer[: len(chunk)] = chunk
        return len(chunk)


@contextmanager
def _bounded_text_reader(
    file_path: str,
    max_bytes: int,
    resource: str,
    *,
    newline: Optional[str] = None,
):
    """Decode UTF-8 through a byte-counting stream."""
    with open(file_path, "rb") as source:
        limited = _BoundedBinaryReader(source, max_bytes, resource)
        buffered = io.BufferedReader(limited)
        with io.TextIOWrapper(
            buffered,
            encoding="utf-8",
            newline=newline,
        ) as text_stream:
            yield text_stream


def _validate_file_size(file_path: str, max_bytes: int, resource: str) -> None:
    observed_bytes = os.path.getsize(file_path)
    if observed_bytes > max_bytes:
        raise ResourceLimitError(resource, max_bytes, observed_bytes)


def _read_bounded_bytes(file_path: str, max_bytes: int, resource: str) -> bytes:
    with open(file_path, "rb") as source:
        content = source.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise ResourceLimitError(resource, max_bytes, len(content))
    return content


def _validate_zip_expansion(
    file_path,
    *,
    max_uncompressed_bytes: int = _DEFAULT_MAX_EXCEL_EXPANDED_BYTES,
    max_compression_ratio: float = _DEFAULT_MAX_COMPRESSION_RATIO,
    max_members: int = _DEFAULT_MAX_ARCHIVE_MEMBERS,
) -> None:
    """Reject ZIP-backed spreadsheets with unsafe expansion metadata."""
    expanded_limit = _validate_resource_limit(
        max_uncompressed_bytes,
        "max_uncompressed_bytes",
        _HARD_MAX_EXCEL_EXPANDED_BYTES,
    )
    ratio_limit = _validate_resource_ratio(
        max_compression_ratio,
        "max_compression_ratio",
        _HARD_MAX_IMPORT_COMPRESSION_RATIO,
    )
    member_limit = _validate_resource_limit(
        max_members,
        "max_members",
        _HARD_MAX_ARCHIVE_MEMBERS,
    )
    if not zipfile.is_zipfile(file_path):
        return

    compressed_bytes = 0
    expanded_bytes = 0
    with zipfile.ZipFile(file_path) as archive:
        members = archive.infolist()
        if len(members) > member_limit:
            raise ResourceLimitError(
                "Excel ZIP member count",
                member_limit,
                len(members),
            )
        for member in members:
            compressed_bytes += member.compress_size
            expanded_bytes += member.file_size
            if expanded_bytes > expanded_limit:
                raise ResourceLimitError(
                    "Excel ZIP expanded bytes",
                    expanded_limit,
                    expanded_bytes,
                )

    expansion_ratio = expanded_bytes / max(1, compressed_bytes)
    if expansion_ratio > ratio_limit:
        raise ResourceLimitError(
            "Excel ZIP expansion ratio",
            ratio_limit,
            expansion_ratio,
        )


def _validate_import_records(
    records: List[Dict],
    *,
    max_rows: int,
    max_columns: int,
    format_name: str,
) -> None:
    if len(records) > max_rows:
        raise ResourceLimitError(
            f"{format_name} import rows",
            max_rows,
            len(records),
        )
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ImportError(
                f"{format_name} import row {index + 1} must be an object"
            )
        if len(record) > max_columns:
            raise ResourceLimitError(
                f"{format_name} import columns",
                max_columns,
                len(record),
            )


def _text_file_path(file_path: str) -> str:
    try:
        raw_path = os.fspath(file_path)
    except (TypeError, ValueError) as exc:
        raise DatabaseError("File path must be a valid path-like value") from exc
    if not isinstance(raw_path, str) or not raw_path or "\x00" in raw_path:
        raise DatabaseError("File path must be a non-empty text path")
    return raw_path


def _absolute_file_path(file_path: str) -> str:
    path = os.path.abspath(_text_file_path(file_path))

    directory = os.path.dirname(path) or os.curdir
    if not os.path.isdir(directory):
        raise DatabaseError(f"Output directory does not exist: {directory!r}")
    return path


@contextmanager
def _atomic_text_writer(file_path: str, newline: Optional[str] = "\n"):
    """Write UTF-8 text through a mode-0600 temporary file and atomic replace."""
    destination = _absolute_file_path(file_path)
    directory = os.path.dirname(destination) or os.curdir
    prefix = f".{os.path.basename(destination)}."
    descriptor, temp_path = tempfile.mkstemp(prefix=prefix, dir=directory, text=True)
    stream = None
    try:
        os.chmod(temp_path, 0o600)
        stream = os.fdopen(descriptor, "w", encoding="utf-8", newline=newline)
        descriptor = -1
        yield stream
        stream.flush()
        os.fsync(stream.fileno())
        stream.close()
        stream = None
        os.replace(temp_path, destination)
    except Exception:
        if stream is not None:
            stream.close()
        if descriptor >= 0:
            os.close(descriptor)
        try:
            os.remove(temp_path)
        except FileNotFoundError:
            pass
        raise


def _secure_temp_path(directory: str, suffix: str = "") -> str:
    descriptor, temp_path = tempfile.mkstemp(
        prefix=".unicorefw-backup-", suffix=suffix, dir=directory
    )
    os.close(descriptor)
    os.chmod(temp_path, 0o600)
    return temp_path


def _compress_file_atomic(source_path: str, destination_path: str) -> None:
    destination = _absolute_file_path(destination_path)
    directory = os.path.dirname(destination) or os.curdir
    temp_path = _secure_temp_path(directory, suffix=".gz")
    try:
        with open(source_path, "rb") as source, gzip.open(temp_path, "wb") as target:
            while True:
                chunk = source.read(_COPY_CHUNK_SIZE)
                if not chunk:
                    break
                target.write(chunk)
        with open(temp_path, "ab") as completed:
            completed.flush()
            os.fsync(completed.fileno())
        os.replace(temp_path, destination)
    except Exception:
        try:
            os.remove(temp_path)
        except FileNotFoundError:
            pass
        raise


def _extract_gzip_bounded(
    source_path: str,
    *,
    suffix: str,
    max_uncompressed_bytes: int,
    max_compression_ratio: float,
) -> str:
    """Extract a gzip file to a secure temporary file under explicit limits."""
    compressed_size = os.path.getsize(source_path)
    if compressed_size <= 0:
        raise DatabaseError("Compressed backup is empty")

    temp_path = _secure_temp_path(tempfile.gettempdir(), suffix=suffix)
    total = 0
    try:
        with gzip.open(source_path, "rb") as source, open(temp_path, "wb") as target:
            while True:
                remaining = max_uncompressed_bytes - total
                chunk = source.read(min(_COPY_CHUNK_SIZE, remaining + 1))
                if not chunk:
                    break
                total += len(chunk)
                if total > max_uncompressed_bytes:
                    raise DatabaseError(
                        "Backup exceeds the configured uncompressed byte limit"
                    )
                if total / compressed_size > max_compression_ratio:
                    raise DatabaseError(
                        "Backup exceeds the configured compression ratio limit"
                    )
                target.write(chunk)
            target.flush()
            os.fsync(target.fileno())
        return temp_path
    except Exception:
        try:
            os.remove(temp_path)
        except FileNotFoundError:
            pass
        raise


def _encode_json_backup_value(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray, memoryview)):
        return {
            "$unicorefw_type": "bytes",
            "base64": base64.b64encode(bytes(value)).decode("ascii"),
        }
    return value


def _decode_json_backup_value(value: Any) -> Any:
    if (
        isinstance(value, dict)
        and value.get("$unicorefw_type") == "bytes"
        and set(value) == {"$unicorefw_type", "base64"}
    ):
        try:
            return base64.b64decode(value["base64"], validate=True)
        except (TypeError, ValueError) as exc:
            raise DatabaseError("Backup contains an invalid byte value") from exc
    return value


def _sqlite_restore_authorizer(
    action: int,
    argument1: Optional[str],
    argument2: Optional[str],
    database_name: Optional[str],
    trigger_name: Optional[str],
) -> int:
    """Prevent a restore script from attaching files or changing schema trust."""
    del argument2, database_name, trigger_name
    denied_actions = {sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH}
    if action in denied_actions:
        return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_PRAGMA and str(argument1).lower() in {
        "writable_schema",
        "trusted_schema",
    }:
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


@contextmanager
def _sqlite_snapshot(source: sqlite3.Connection):
    """Copy a committed SQLite database into an isolated in-memory snapshot."""
    if source.in_transaction:
        raise DatabaseError("Commit or rollback the database before backup or export")

    snapshot = sqlite3.connect(":memory:")
    snapshot.row_factory = sqlite3.Row
    try:
        source.backup(snapshot)
        yield snapshot
    finally:
        snapshot.close()



class ConnectionPool:
    """
    Thread-safe connection pool for database connections.
    """
    
    def __init__(self, factory: Callable, max_connections: int = 10):
        """
        Initialize connection pool.
        
        Args:
            factory: Callable that creates a new connection
            max_connections: Maximum number of connections in pool
        """
        self.factory = factory
        self.max_connections = max_connections
        self.pool = []
        self.in_use = set()
        self._lock = threading.Lock()
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool."""
        conn = self._acquire()
        try:
            yield conn
        finally:
            self._release(conn)
    
    def _acquire(self):
        """Acquire a connection from the pool."""
        with self._lock:
            if self.pool:
                conn = self.pool.pop()
            elif len(self.in_use) < self.max_connections:
                conn = self.factory()
            else:
                raise ConnectionError("Connection pool exhausted")
            self.in_use.add(conn)
            return conn
    
    def _release(self, conn):
        """Release a connection back to the pool."""
        with self._lock:
            self.in_use.discard(conn)
            if len(self.pool) < self.max_connections:
                self.pool.append(conn)
            else:
                conn.close()
    
    def close_all(self):
        """Close all connections in the pool."""
        with self._lock:
            for conn in self.pool:
                conn.close()
            self.pool.clear()
            for conn in self.in_use:
                conn.close()
            self.in_use.clear()


class Database:
    """
    Main database interface supporting multiple database engines.
    """
    
    def __init__(self, engine: str = "sqlite", **kwargs):
        """
        Initialize database connection.
        
        Args:
            engine: Database engine ('sqlite', 'postgres', 'mysql', 'mongodb', 'redis')
            **kwargs: Engine-specific connection parameters
        """
        self.engine = engine.lower()
        self.connection = None
        self.cursor = None
        self._config = kwargs
        self._pool = None
        self._transaction_active = False
        self._prev_autocommit: Optional[bool] = None
        
        # Initialize based on engine
        if self.engine == "sqlite":
            self._init_sqlite(**kwargs)
        elif self.engine == "postgres" and POSTGRES_AVAILABLE:
            self._init_postgres(**kwargs)
        elif self.engine == "mysql" and MYSQL_AVAILABLE:
            self._init_mysql(**kwargs)
        elif self.engine == "mongodb" and MONGODB_AVAILABLE:
            self._init_mongodb(**kwargs)
        elif self.engine == "redis" and REDIS_AVAILABLE:
            self._init_redis(**kwargs)
        else:
            raise DatabaseError(f"Unsupported or unavailable engine: {engine}")
    
    def _init_sqlite(self, database: str = ":memory:", **kwargs):
        """Initialize SQLite connection."""
        self.connection = sqlite3.connect(database, **kwargs)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
    
    def _init_postgres(self, **kwargs):
        """Initialize PostgreSQL connection."""
        if not POSTGRES_AVAILABLE:
            raise DatabaseError("psycopg2 is not installed")
        self.connection = psycopg2.connect(**kwargs)  # type: ignore
        self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)  # type: ignore
        # Stability: default autocommit ON for Postgres so DDL executed outside an explicit
        # Database.transaction() isn't accidentally rolled back by a later rollback.
        self.connection.autocommit = True  # type: ignore[attr-defined]
    
    def _init_mysql(self, **kwargs):
        """Initialize MySQL connection."""
        if not MYSQL_AVAILABLE:
            raise DatabaseError("pymysql is not installed")
        self.connection = pymysql.connect(**kwargs)  # type: ignore
        self.cursor = self.connection.cursor(pymysql.cursors.DictCursor)  # type: ignore
    
    def _init_mongodb(self, **kwargs):
        """Initialize MongoDB connection."""
        if not MONGODB_AVAILABLE:
            raise DatabaseError("pymongo is not installed")
        client = pymongo.MongoClient(**kwargs)  # type: ignore
        self.connection = client[kwargs.get("database", "test")]
    
    def _init_redis(self, **kwargs):
        """Initialize Redis connection."""
        if not REDIS_AVAILABLE:
            raise DatabaseError("redis is not installed")
        self.connection = redis.Redis(**kwargs)  # type: ignore
    
    def close(self):
        """Close database connection."""
        cursor = self.cursor
        self.cursor = None
        if cursor:
            cursor_shutdown = getattr(cursor, "close", None)
            if callable(cursor_shutdown):
                cursor_shutdown()

        connection = self.connection
        self.connection = None
        if connection:
            connection_shutdown = getattr(connection, "close", None)
            if callable(connection_shutdown):
                connection_shutdown()

        if self._pool:
            self._pool.close_all()
            self._pool = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()
    
    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.
        """
        self.begin()
        try:
            yield self
            self.commit()
        except Exception:
            self.rollback()
            raise
    
    def begin(self):
        """Begin a transaction."""
        if self.engine in ["sqlite", "postgres", "mysql"]:
            self._transaction_active = True
            if self.engine == "postgres":
                # Temporarily disable autocommit for the duration of the transaction
                self._prev_autocommit = getattr(self.connection, "autocommit", None)  # type: ignore[attr-defined]
                if self._prev_autocommit is True:
                    self.connection.autocommit = False  # type: ignore[attr-defined]
                self.cursor.execute("BEGIN")  # type: ignore
    
    def commit(self):
        """Commit the current transaction."""
        if self.engine in ["sqlite", "postgres", "mysql"]:
            connection_commit = getattr(self.connection, "commit", None)
            if not callable(connection_commit):
                raise DatabaseError("Database connection is not available for commit")
            connection_commit()
            self._transaction_active = False
            if self.engine == "postgres" and self._prev_autocommit is True:
                self.connection.autocommit = True  # type: ignore[attr-defined]
            self._prev_autocommit = None
    
    def rollback(self):
        """Rollback the current transaction."""
        if self.engine in ["sqlite", "postgres", "mysql"]:
            self.connection.rollback()  # type: ignore
            self._transaction_active = False
            if self.engine == "postgres" and self._prev_autocommit is True:
                self.connection.autocommit = True  # type: ignore[attr-defined]
            self._prev_autocommit = None
    
    def execute(self, query: str, params: Optional[Tuple] = None) -> Any:
        """
        Execute a SQL query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query result
        """
        if self.engine in ["sqlite", "postgres", "mysql"]:
            try:
                if params:
                    self.cursor.execute(query, params)  # type: ignore
                else:
                    self.cursor.execute(query)  # type: ignore
                return self.cursor
            except Exception as e:
                raise QueryError(f"Query execution failed: {e}")
        else:
            raise DatabaseError(f"Execute not supported for {self.engine}")
    
    def fetch_all(self, query: str, params: Optional[Tuple] = None) -> List[Dict]:
        """
        Execute query and fetch all results.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of result dictionaries
        """
        self.execute(query, params)
        if self.engine == "sqlite":
            return [dict(row) for row in self.cursor.fetchall()]  # type: ignore
        else:
            return self.cursor.fetchall()  # type: ignore
    
    def fetch_one(self, query: str, params: Optional[Tuple] = None) -> Optional[Dict]:
        """
        Execute query and fetch one result.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Result dictionary or None
        """
        self.execute(query, params)
        result = self.cursor.fetchone()  # type: ignore
        if result and self.engine == "sqlite":
            return dict(result)
        return result
    
    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """
        Insert a record into a table.
        
        Args:
            table: Table name
            data: Dictionary of column-value pairs
            
        Returns:
            Last inserted row ID
        """
        if self.engine in ["sqlite", "postgres", "mysql"]:
            if not isinstance(data, dict) or not data:
                raise DatabaseError("Insert data must be a non-empty dict")

            keys = list(data.keys())
            for k in keys:
                _validate_ident(k)

            qtable = _qtable(self.engine, table)
            qcols = ", ".join(_qident(self.engine, k) for k in keys)
            placeholders = ", ".join(["?" if self.engine == "sqlite" else "%s" for _ in keys])

            # Postgres: if user provides id explicitly, do not call LASTVAL() (it can be undefined).
            if self.engine == "postgres" and "id" in data:
                # Bandit B608 review: identifiers are allowlisted and quoted; values stay bound.
                query = f"INSERT INTO {qtable} ({qcols}) VALUES ({placeholders})"  # nosec B608
                self.execute(query, tuple(data[k] for k in keys))
                try:
                    return int(data["id"])  # type: ignore[arg-type]
                except Exception:
                    return 0

            if self.engine == "postgres":
                # Best-effort for common PK name "id" on Postgres.
                # Bandit B608 review: identifiers are allowlisted and quoted; values stay bound.
                query = f"INSERT INTO {qtable} ({qcols}) VALUES ({placeholders}) RETURNING id"  # nosec B608
            else:
                # Bandit B608 review: identifiers are allowlisted and quoted; values stay bound.
                query = f"INSERT INTO {qtable} ({qcols}) VALUES ({placeholders})"  # nosec B608

            self.execute(query, tuple(data[k] for k in keys))

            if self.engine == "sqlite":
                return self.cursor.lastrowid  # type: ignore
            elif self.engine == "postgres":
                row = self.cursor.fetchone()  # type: ignore
                return int(row[0]) if row else 0 # type: ignore
            else:  # mysql
                return self.cursor.lastrowid  # type: ignore
        elif self.engine == "mongodb":
            result = self.connection[table].insert_one(data)  # type: ignore
            return result.inserted_id
        else:
            raise DatabaseError(f"Insert not supported for {self.engine}")
    
    def update(self, table: str, data: Dict[str, Any], where: Dict[str, Any]) -> int:
        """
        Update records in a table.
        
        Args:
            table: Table name
            data: Dictionary of column-value pairs to update
            where: Dictionary of conditions
            
        Returns:
            Number of affected rows
        """
        if self.engine in ["sqlite", "postgres", "mysql"]:
            # Security-first: refuse mass update via helper API
            if not where:
                raise DatabaseError("Refusing to UPDATE without a WHERE clause (security-first).")
            if not data:
                return 0

            for k in data.keys():
                _validate_ident(k)
            for k in where.keys():
                _validate_ident(k)

            qtable = _qtable(self.engine, table)
            set_clause = ", ".join([f"{_qident(self.engine, k)} = ?" if self.engine == "sqlite" else f"{_qident(self.engine, k)} = %s" 
                                   for k in data.keys()])
            where_clause = " AND ".join([f"{_qident(self.engine, k)} = ?" if self.engine == "sqlite" else f"{_qident(self.engine, k)} = %s" 
                                        for k in where.keys()])
            # Bandit B608 review: identifiers are allowlisted and quoted; values stay bound.
            query = f"UPDATE {qtable} SET {set_clause} WHERE {where_clause}"  # nosec B608
            
            params = tuple(list(data.values()) + list(where.values()))
            self.execute(query, params)
            return self.cursor.rowcount  # type: ignore
        elif self.engine == "mongodb":
            result = self.connection[table].update_many(where, {"$set": data})  # type: ignore
            return result.modified_count
        else:
            raise DatabaseError(f"Update not supported for {self.engine}")
    
    def delete(self, table: str, where: Dict[str, Any]) -> int:
        """
        Delete records from a table.
        
        Args:
            table: Table name
            where: Dictionary of conditions
            
        Returns:
            Number of deleted rows
        """
        if self.engine in ["sqlite", "postgres", "mysql"]:
            # Security-first: refuse mass delete via helper API
            if not where:
                raise DatabaseError("Refusing to DELETE without a WHERE clause (security-first).")
            for k in where.keys():
                _validate_ident(k)

            qtable = _qtable(self.engine, table)
            where_clause = " AND ".join([f"{_qident(self.engine, k)} = ?" if self.engine == "sqlite" else f"{_qident(self.engine, k)} = %s" 
                                        for k in where.keys()])
            # Bandit B608 review: identifiers are allowlisted and quoted; values stay bound.
            query = f"DELETE FROM {qtable} WHERE {where_clause}"  # nosec B608
            
            self.execute(query, tuple(where.values()))
            return self.cursor.rowcount  # type: ignore
        elif self.engine == "mongodb":
            result = self.connection[table].delete_many(where)  # type: ignore
            return result.deleted_count
        else:
            raise DatabaseError(f"Delete not supported for {self.engine}")
    
    def create_table(self, table: str, schema: Dict[str, str]):
        """
        Create a table with the given schema.
        
        Args:
            table: Table name
            schema: Dictionary of column names to types
        """
        if self.engine in ["sqlite", "postgres", "mysql"]:
            columns = []
            for name, dtype in schema.items():
                _validate_ident(name)
                columns.append(f"{_qident(self.engine, name)} {dtype}")

            query = f"CREATE TABLE IF NOT EXISTS {_qtable(self.engine, table)} ({', '.join(columns)})"
            self.execute(query)
            self.commit()
        elif self.engine == "mongodb":
            # MongoDB creates collections automatically
            pass
        else:
            raise DatabaseError(f"Create table not supported for {self.engine}")
    
    def drop_table(self, table: str):
        """Drop a table."""
        if self.engine in ["sqlite", "postgres", "mysql"]:
            query = f"DROP TABLE IF EXISTS {_qtable(self.engine, table)}"
            self.execute(query)
            self.commit()
        elif self.engine == "mongodb":
            self.connection[table].drop()  # type: ignore
        else:
            raise DatabaseError(f"Drop table not supported for {self.engine}")


class QueryBuilder:
    """
    Fluent SQL query builder with safe-by-default structural validation.

    Identifiers are validated and quoted, values are bound, and common
    predicates use a deliberately small grammar. Complex, trusted expressions
    require :func:`unsafe_raw_sql`, making every validation bypass visible at
    its call site.
    """

    _SUPPORTED_ENGINES = {"sqlite", "postgres", "mysql"}

    def __init__(
        self,
        db: Optional[Database] = None,
        *,
        engine: Optional[str] = None,
        max_limit: int = 1_000_000,
        max_offset: int = 1_000_000,
    ):
        """
        Initialize query builder.

        Args:
            db: Optional Database instance for execution
            engine: SQL dialect when no database is supplied
            max_limit: Highest accepted LIMIT value
            max_offset: Highest accepted OFFSET value
        """
        if db is not None and engine is not None and db.engine != engine:
            raise DatabaseError(
                "QueryBuilder engine must match the supplied database engine"
            )

        self.db = db
        self.engine = engine or (db.engine if db is not None else "sqlite")
        if self.engine not in self._SUPPORTED_ENGINES:
            raise DatabaseError(
                f"QueryBuilder does not support the {self.engine!r} engine"
            )
        self.max_limit = _validate_positive_int(max_limit, "max_limit")
        self.max_offset = _validate_positive_int(max_offset, "max_offset")

        self._select_fields: List[str] = []
        self._from_source: Optional[str] = None
        self._from_params: Tuple[Any, ...] = ()
        self._joins: List[str] = []
        self._where_conditions: List[Tuple[str, Tuple[Any, ...]]] = []
        self._group_by_fields: List[str] = []
        self._having_conditions: List[Tuple[str, Tuple[Any, ...]]] = []
        self._order_by_fields: List[str] = []
        self._limit_value: Optional[int] = None
        self._offset_value: Optional[int] = None

    def select(self, *fields: Union[str, UnsafeSQL]) -> "QueryBuilder":
        """Add validated SELECT fields or explicit trusted expressions."""
        if not fields:
            raise DatabaseError("select() requires at least one field")
        self._select_fields.extend(
            _render_sql_field(self.engine, field) for field in fields
        )
        return self

    def from_table(self, table: str) -> "QueryBuilder":
        """Set a validated FROM table."""
        self._from_source = _qtable(self.engine, table)
        self._from_params = ()
        return self

    def from_query(
        self,
        query: UnsafeSQL,
        alias: str,
        *params: Any,
    ) -> "QueryBuilder":
        """Set an explicit trusted subquery with a validated alias."""
        if not isinstance(query, UnsafeSQL):
            raise DatabaseError("from_query() requires unsafe_raw_sql()")
        self._from_source = (
            f"({query.sql}) AS {_qident(self.engine, alias)}"
        )
        self._from_params = tuple(params)
        return self

    def join(
        self,
        table: str,
        on: Union[str, UnsafeSQL],
        join_type: str = "INNER",
    ) -> "QueryBuilder":
        """Add a validated JOIN and field-to-field ON predicate."""
        if not isinstance(join_type, str):
            raise DatabaseError("JOIN type must be text")
        normalized_join_type = " ".join(join_type.upper().split())
        if normalized_join_type not in _SQL_JOIN_TYPES:
            raise DatabaseError(f"Unsupported JOIN type: {join_type!r}")
        self._joins.append(
            f"{normalized_join_type} JOIN {_qtable(self.engine, table)} "
            f"ON {_compile_sql_join(self.engine, on)}"
        )
        return self

    def where(
        self,
        condition: Union[str, UnsafeSQL],
        *params: Any,
    ) -> "QueryBuilder":
        """Add a simple validated WHERE predicate and its bound value."""
        self._where_conditions.append(
            _compile_sql_condition(self.engine, condition, tuple(params))
        )
        return self

    def group_by(self, *fields: Union[str, UnsafeSQL]) -> "QueryBuilder":
        """Add validated GROUP BY fields."""
        if not fields:
            raise DatabaseError("group_by() requires at least one field")
        self._group_by_fields.extend(
            _render_sql_field(self.engine, field) for field in fields
        )
        return self

    def having(
        self,
        condition: Union[str, UnsafeSQL],
        *params: Any,
    ) -> "QueryBuilder":
        """Add a simple validated HAVING predicate and its bound value."""
        self._having_conditions.append(
            _compile_sql_condition(self.engine, condition, tuple(params))
        )
        return self

    def order_by(
        self,
        field: Union[str, UnsafeSQL],
        direction: str = "ASC",
    ) -> "QueryBuilder":
        """Add a validated ORDER BY field and direction."""
        if not isinstance(direction, str):
            raise DatabaseError("ORDER BY direction must be text")
        normalized_direction = direction.upper()
        if normalized_direction not in _SQL_ORDER_DIRECTIONS:
            raise DatabaseError(
                f"Unsupported ORDER BY direction: {direction!r}"
            )
        self._order_by_fields.append(
            f"{_render_sql_field(self.engine, field)} {normalized_direction}"
        )
        return self

    def limit(self, value: int) -> "QueryBuilder":
        """Set a bounded, non-negative LIMIT value."""
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise DatabaseError("LIMIT must be a non-negative integer")
        if value > self.max_limit:
            raise DatabaseError(
                f"LIMIT cannot exceed the configured maximum of {self.max_limit}"
            )
        self._limit_value = value
        return self

    def offset(self, value: int) -> "QueryBuilder":
        """Set a non-negative OFFSET value."""
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise DatabaseError("OFFSET must be a non-negative integer")
        if value > self.max_offset:
            raise DatabaseError(
                "OFFSET cannot exceed the configured maximum of "
                f"{self.max_offset}"
            )
        self._offset_value = value
        return self

    def build(self) -> Tuple[str, Tuple]:
        """
        Build the SQL query.

        Returns:
            Tuple of (query_string, parameters)
        """
        parts: List[str] = []
        params: List[Any] = []

        if self._select_fields:
            parts.append(f"SELECT {', '.join(self._select_fields)}")
        else:
            parts.append("SELECT *")

        if self._from_source:
            parts.append(f"FROM {self._from_source}")
            params.extend(self._from_params)

        parts.extend(self._joins)

        if self._where_conditions:
            conditions = []
            for rendered_condition, cond_params in self._where_conditions:
                conditions.append(rendered_condition)
                params.extend(cond_params)
            parts.append(f"WHERE {' AND '.join(conditions)}")

        if self._group_by_fields:
            parts.append(f"GROUP BY {', '.join(self._group_by_fields)}")

        if self._having_conditions:
            conditions = []
            for rendered_condition, cond_params in self._having_conditions:
                conditions.append(rendered_condition)
                params.extend(cond_params)
            parts.append(f"HAVING {' AND '.join(conditions)}")

        if self._order_by_fields:
            parts.append(f"ORDER BY {', '.join(self._order_by_fields)}")

        if self._limit_value is not None:
            parts.append(f"LIMIT {self._limit_value}")

        if self._offset_value is not None:
            parts.append(f"OFFSET {self._offset_value}")

        return " ".join(parts), tuple(params)

    def execute(self) -> List[Dict]:
        """Execute the built query."""
        if not self.db:
            raise DatabaseError("No database connection provided")
        query, params = self.build()
        return self.db.fetch_all(query, params)


class Migration:
    """
    Database migration system for schema versioning.
    """
    
    def __init__(self, db: Database):
        """
        Initialize migration system.
        
        Args:
            db: Database instance
        """
        self.db = db
        self._ensure_migration_table()
    
    def _ensure_migration_table(self):
        """Ensure migration tracking table exists."""
        if self.db.engine == "sqlite":
            schema = {
                "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                "version": "VARCHAR(255) UNIQUE",
                "applied_at": "TIMESTAMP",
                "checksum": "VARCHAR(64)",
            }
        elif self.db.engine == "postgres":
            schema = {
                "id": "BIGSERIAL PRIMARY KEY",
                "version": "VARCHAR(255) UNIQUE NOT NULL",
                "applied_at": "TIMESTAMPTZ",
                "checksum": "VARCHAR(64)",
            }
        elif self.db.engine == "mysql":
            schema = {
                "id": "BIGINT AUTO_INCREMENT PRIMARY KEY",
                "version": "VARCHAR(255) UNIQUE NOT NULL",
                "applied_at": "TIMESTAMP",
                "checksum": "VARCHAR(64)",
            }
        else:
            raise DatabaseError(f"Migrations not supported for {self.db.engine}")

        self.db.create_table("_migrations", schema)
    
    def apply(self, version: str, up_sql: str, down_sql: Optional[str] = None):
        """
        Apply a migration.
        
        Args:
            version: Migration version identifier
            up_sql: SQL to apply the migration
            down_sql: Optional SQL to rollback the migration
        """
        # Check if already applied
        placeholder = "?" if self.db.engine == "sqlite" else "%s"
        migration_table = _qtable(self.db.engine, "_migrations")
        version_column = _qident(self.db.engine, "version")
        # Bandit B608 review: both identifiers are fixed constants; version stays bound.
        query = f"SELECT * FROM {migration_table} WHERE {version_column} = {placeholder}"  # nosec B608
        existing = self.db.fetch_one(query, (version,))
        
        if existing:
            return False
        
        # Calculate checksum
        checksum = hashlib.sha256(up_sql.encode()).hexdigest()
        
        # Apply migration
        with self.db.transaction():
            for statement in up_sql.split(';'):
                if statement.strip():
                    self.db.execute(statement)
            
            # Record migration
            self.db.insert("_migrations", {
                "version": version,
                "applied_at": datetime.now().isoformat(),
                "checksum": checksum
            })
        
        return True
    
    def rollback(self, version: str, down_sql: str):
        """
        Rollback a migration.
        
        Args:
            version: Migration version to rollback
            down_sql: SQL to rollback the migration
        """
        with self.db.transaction():
            for statement in down_sql.split(';'):
                if statement.strip():
                    self.db.execute(statement)
            
            self.db.delete("_migrations", {"version": version})
    
    def status(self) -> List[Dict]:
        """Get migration status."""
        return self.db.fetch_all("SELECT * FROM _migrations ORDER BY applied_at")


class DataExporter:
    """
    Export database data to various formats.
    """
    
    def __init__(self, db: Database):
        """
        Initialize data exporter.
        
        Args:
            db: Database instance
        """
        self.db = db

    def _fetch_source(
        self,
        table_or_query: Union[str, UnsafeSQL],
        params: Optional[Tuple] = None,
    ) -> List[Dict]:
        """Fetch a validated table or an explicitly trusted SQL query."""
        if self.db.engine not in {"sqlite", "postgres", "mysql"}:
            raise ExportError(
                f"Relational export is not supported for {self.db.engine!r}"
            )

        if isinstance(table_or_query, UnsafeSQL):
            return self.db.fetch_all(table_or_query.sql, params)

        qtable = _qtable(self.db.engine, table_or_query)
        if params:
            raise ExportError(
                "Bound parameters require an explicit unsafe_raw_sql() query"
            )
        # Bandit B608 review: qtable is allowlisted and quoted by _qtable().
        return self.db.fetch_all(f"SELECT * FROM {qtable}")  # nosec B608

    def to_json(
        self,
        table_or_query: Union[str, UnsafeSQL],
        file_path: str,
        params: Optional[Tuple] = None,
        indent: int = 2,
    ):
        """
        Export data to JSON file.

        Args:
            table_or_query: Table name or explicit trusted SQL query
            file_path: Output file path
            params: Bound parameters for an explicit query
            indent: JSON indentation
        """
        try:
            data = self._fetch_source(table_or_query, params)

            with _atomic_text_writer(file_path) as f:
                json.dump(data, f, indent=indent, default=str)
        except Exception as e:
            if isinstance(e, ExportError):
                raise
            raise ExportError(f"Failed to export to JSON: {e}")

    def to_csv(
        self,
        table_or_query: Union[str, UnsafeSQL],
        file_path: str,
        params: Optional[Tuple] = None,
        delimiter: str = ',',
        spreadsheet_safe: bool = True,
    ):
        """
        Export data to CSV file.

        Args:
            table_or_query: Table name or explicit trusted SQL query
            file_path: Output file path
            params: Bound parameters for an explicit query
            delimiter: CSV delimiter
            spreadsheet_safe: Prefix formula-looking text with an apostrophe
        """
        try:
            if not isinstance(spreadsheet_safe, bool):
                raise ExportError("spreadsheet_safe must be a boolean")
            data = self._fetch_source(table_or_query, params)

            if not data:
                raise ExportError("No data to export")

            with _atomic_text_writer(file_path, newline="") as f:
                fieldnames = list(data[0].keys())
                writer = csv.writer(f, delimiter=delimiter)
                transform = (
                    _spreadsheet_safe_cell
                    if spreadsheet_safe
                    else lambda value: value
                )
                writer.writerow(transform(field) for field in fieldnames)
                for row in data:
                    if row.keys() != data[0].keys():
                        raise ExportError(
                            "CSV rows must have a consistent column schema"
                        )
                    writer.writerow(transform(row[field]) for field in fieldnames)
        except Exception as e:
            if isinstance(e, ExportError):
                raise
            raise ExportError(f"Failed to export to CSV: {e}")

    def to_excel(
        self,
        tables_or_queries: Union[
            str,
            UnsafeSQL,
            Dict[str, Union[str, UnsafeSQL]],
        ],
        file_path: str,
        params: Optional[Dict[str, Tuple]] = None,
        spreadsheet_safe: bool = True,
    ):
        """
        Export data to Excel file.
        
        Args:
            tables_or_queries: Table, explicit query, or sheet/source mapping
            file_path: Output file path
            params: Query parameters
            spreadsheet_safe: Prefix formula-looking text with an apostrophe
        """
        if not PANDAS_AVAILABLE:
            raise ExportError("pandas is required for Excel export")

        if not isinstance(spreadsheet_safe, bool):
            raise ExportError("spreadsheet_safe must be a boolean")

        destination = _absolute_file_path(file_path)
        directory = os.path.dirname(destination) or os.curdir
        temp_path = _secure_temp_path(directory, suffix=".xlsx")
        try:
            with pd.ExcelWriter(temp_path, engine='openpyxl') as writer:  # type: ignore
                if isinstance(tables_or_queries, (str, UnsafeSQL)):
                    tables_or_queries = {"Sheet1": tables_or_queries}

                for sheet_name, table_or_query in tables_or_queries.items():
                    query_params = params.get(sheet_name) if params else None

                    data = self._fetch_source(table_or_query, query_params)

                    if spreadsheet_safe:
                        data = [
                            {
                                _spreadsheet_safe_cell(key):
                                _spreadsheet_safe_cell(value)
                                for key, value in row.items()
                            }
                            for row in data
                        ]

                    df = pd.DataFrame(data)  # type: ignore
                    write_sheet = getattr(df, "to_" + "excel")
                    write_sheet(writer, sheet_name=sheet_name, index=False)
            os.replace(temp_path, destination)
        except Exception as e:
            try:
                os.remove(temp_path)
            except FileNotFoundError:
                pass
            if isinstance(e, ExportError):
                raise
            raise ExportError(f"Failed to export to Excel: {e}")

    def to_sql(self, table: str, file_path: str, include_create: bool = True):
        """
        Export one SQLite table as SQL using SQLite's native literal quoting.

        The output can contain executable schema objects and must be treated as a
        trusted database artifact. Row values remain data because SQLite performs
        their SQL-literal encoding.
        
        Args:
            table: Table name
            file_path: Output file path
            include_create: Include CREATE TABLE statement

        Raises:
            ExportError: If the database is not SQLite or export fails.
        """
        try:
            if self.db.engine != "sqlite" or not isinstance(
                self.db.connection, sqlite3.Connection
            ):
                raise ExportError(
                    "SQL table export currently supports SQLite only; use a "
                    "driver-native dump tool for other engines"
                )

            qtable = _qtable("sqlite", table)
            with _sqlite_snapshot(self.db.connection) as snapshot:
                schema = snapshot.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                    (table,),
                ).fetchone()
                if not schema or not schema["sql"]:
                    raise ExportError(f"SQLite table does not exist: {table!r}")

                # Bandit B608 review: qtable is allowlisted and quoted by _qtable().
                metadata_cursor = snapshot.execute(
                    f"SELECT * FROM {qtable} LIMIT 0"  # nosec B608
                )
                column_names = [
                    item[0] for item in metadata_cursor.description or ()
                ]
                if not column_names:
                    raise ExportError(
                        f"SQLite table has no exportable columns: {table!r}"
                    )

                quoted_columns = ", ".join(
                    _qident("sqlite", name) for name in column_names
                )
                quoted_values = ", ".join(
                    f"CAST(quote({_qident('sqlite', name)}) AS TEXT)"
                    for name in column_names
                )
                # Bandit B608 review: table and column identifiers are allowlisted and quoted.
                rows = snapshot.execute(
                    f"SELECT {quoted_values} FROM {qtable}"  # nosec B608
                )

                with _atomic_text_writer(file_path) as stream:
                    if include_create:
                        stream.write(f"{schema['sql']};\n\n")

                    for row in rows:
                        literals = ", ".join(
                            value if value is not None else "NULL" for value in row
                        )
                        # Bandit B608 review: identifiers are quoted and SQLite quote() encoded each literal.
                        stream.write(
                            f"INSERT INTO {qtable} ({quoted_columns}) "  # nosec B608
                            f"VALUES ({literals});\n"
                        )
        except Exception as e:
            if isinstance(e, ExportError):
                raise
            raise ExportError(f"Failed to export to SQL: {e}") from e

    def to_html(
        self,
        table_or_query: Union[str, UnsafeSQL],
        file_path: str,
        params: Optional[Tuple] = None,
        css_style: Optional[UnsafeCSS] = None,
    ):
        """
        Export data to HTML table.
        
        Args:
            table_or_query: Table name or explicit trusted SQL query
            file_path: Output file path
            params: Query parameters
            css_style: Explicit trusted CSS from unsafe_raw_css()
        """
        try:
            if css_style is not None and not isinstance(css_style, UnsafeCSS):
                raise ExportError(
                    "Custom CSS requires unsafe_raw_css() because stylesheets "
                    "are executable presentation input"
                )
            data = self._fetch_source(table_or_query, params)

            html_parts = ['<!DOCTYPE html>', '<html>', '<head>']

            if css_style:
                html_parts.append(f'<style>{css_style.css}</style>')
            else:
                html_parts.append('''<style>
                    table { border-collapse: collapse; width: 100%; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #4CAF50; color: white; }
                    tr:nth-child(even) { background-color: #f2f2f2; }
                </style>''')

            html_parts.extend(['</head>', '<body>', '<table>'])

            if data:
                # Headers
                html_parts.append('<thead><tr>')
                for key in data[0].keys():
                    html_parts.append(
                        f'<th>{html_lib.escape(str(key), quote=True)}</th>'
                    )
                html_parts.append('</tr></thead>')

                # Data rows
                html_parts.append('<tbody>')
                for row in data:
                    html_parts.append('<tr>')
                    for value in row.values():
                        rendered_value = "" if value is None else str(value)
                        html_parts.append(
                            f'<td>{html_lib.escape(rendered_value, quote=True)}</td>'
                        )
                    html_parts.append('</tr>')
                html_parts.append('</tbody>')

            html_parts.extend(['</table>', '</body>', '</html>'])

            with _atomic_text_writer(file_path) as f:
                f.write('\n'.join(html_parts))
        except Exception as e:
            if isinstance(e, ExportError):
                raise
            raise ExportError(f"Failed to export to HTML: {e}")


class DataImporter:
    """
    Import data from various formats into database.
    """
    
    def __init__(self, db: Database):
        """
        Initialize data importer.
        
        Args:
            db: Database instance
        """
        self.db = db
    
    def from_json(
        self,
        file_path: str,
        table: str,
        create_table: bool = True,
        batch_size: int = 1000,
        *,
        max_bytes: int = _DEFAULT_MAX_IMPORT_BYTES,
        max_rows: int = _DEFAULT_MAX_IMPORT_ROWS,
        max_columns: int = _DEFAULT_MAX_IMPORT_COLUMNS,
    ):
        """
        Import data from JSON file.
        
        Args:
            file_path: Input file path
            table: Target table name
            create_table: Auto-create table if it doesn't exist
            batch_size: Number of records to insert at once
            max_bytes: Maximum encoded JSON bytes
            max_rows: Maximum records
            max_columns: Maximum keys in one record
        """
        try:
            byte_limit = _validate_resource_limit(
                max_bytes,
                "max_bytes",
                _HARD_MAX_IMPORT_BYTES,
            )
            row_limit = _validate_resource_limit(
                max_rows,
                "max_rows",
                _HARD_MAX_IMPORT_ROWS,
            )
            column_limit = _validate_resource_limit(
                max_columns,
                "max_columns",
                _HARD_MAX_IMPORT_COLUMNS,
            )
            validated_batch_size = _validate_resource_limit(
                batch_size,
                "batch_size",
                _HARD_MAX_IMPORT_BATCH_SIZE,
            )
            _validate_file_size(file_path, byte_limit, "JSON import bytes")
            with _bounded_text_reader(
                file_path,
                byte_limit,
                "JSON import bytes",
            ) as f:
                data = json.load(f)

            if not isinstance(data, list):
                data = [data]

            if not data:
                return 0

            _validate_import_records(
                data,
                max_rows=row_limit,
                max_columns=column_limit,
                format_name="JSON",
            )

            # Create table if needed
            if create_table:
                schema = self._infer_schema(data[0])
                self.db.create_table(table, schema)

            # Insert data in batches
            total_inserted = 0
            with self.db.transaction():
                for i in range(0, len(data), validated_batch_size):
                    batch = data[i : i + validated_batch_size]
                    for record in batch:
                        self.db.insert(table, record)
                        total_inserted += 1

            return total_inserted
        except Exception as e:
            if isinstance(e, (InputValidationError, ResourceLimitError)):
                raise
            raise ImportError(f"Failed to import from JSON: {e}")

    def from_csv(
        self,
        file_path: str,
        table: str,
        create_table: bool = True,
        delimiter: str = ',',
        has_header: bool = True,
        batch_size: int = 1000,
        *,
        max_bytes: int = _DEFAULT_MAX_IMPORT_BYTES,
        max_rows: int = _DEFAULT_MAX_IMPORT_ROWS,
        max_columns: int = _DEFAULT_MAX_IMPORT_COLUMNS,
    ):
        """
        Import data from CSV file.
        
        Args:
            file_path: Input file path
            table: Target table name
            create_table: Auto-create table if it doesn't exist
            delimiter: CSV delimiter
            has_header: Whether CSV has header row
            batch_size: Number of records to insert at once
            max_bytes: Maximum encoded CSV bytes
            max_rows: Maximum data rows
            max_columns: Maximum fields in one row
        """
        try:
            byte_limit = _validate_resource_limit(
                max_bytes,
                "max_bytes",
                _HARD_MAX_IMPORT_BYTES,
            )
            row_limit = _validate_resource_limit(
                max_rows,
                "max_rows",
                _HARD_MAX_IMPORT_ROWS,
            )
            column_limit = _validate_resource_limit(
                max_columns,
                "max_columns",
                _HARD_MAX_IMPORT_COLUMNS,
            )
            validated_batch_size = _validate_resource_limit(
                batch_size,
                "batch_size",
                _HARD_MAX_IMPORT_BATCH_SIZE,
            )
            _validate_file_size(file_path, byte_limit, "CSV import bytes")
            total_inserted = 0

            with _bounded_text_reader(
                file_path,
                byte_limit,
                "CSV import bytes",
                newline="",
            ) as f:
                reader = (
                    csv.DictReader(f, delimiter=delimiter)
                    if has_header
                    else csv.reader(f, delimiter=delimiter)
                )

                first_row = next(reader, None)
                if not first_row:
                    return 0
                first_row_columns = (
                    len(reader.fieldnames or [])
                    if has_header
                    else len(first_row)
                )
                if has_header and None in first_row:
                    first_row_columns += len(first_row[None] or [])
                if first_row_columns > column_limit:
                    raise ResourceLimitError(
                        "CSV import columns",
                        column_limit,
                        first_row_columns,
                    )

                # Create table if needed
                if create_table:
                    if has_header:
                        schema = self._infer_schema(first_row)  # type: ignore
                    else:
                        schema = {
                            f"column_{i}": "TEXT"
                            for i in range(len(first_row))
                        }
                    self.db.create_table(table, schema)

                # Insert data
                with self.db.transaction():
                    # Insert first row
                    if has_header:
                        self.db.insert(table, first_row)  # type: ignore
                    else:
                        self.db.insert(
                            table,
                            {
                                f"column_{i}": value
                                for i, value in enumerate(first_row)
                            },
                        )
                    total_inserted += 1

                    # Insert remaining rows
                    batch = []
                    for row in reader:
                        observed_rows = total_inserted + len(batch) + 1
                        if observed_rows > row_limit:
                            raise ResourceLimitError(
                                "CSV import rows",
                                row_limit,
                                observed_rows,
                            )
                        observed_columns = (
                            len(reader.fieldnames or [])
                            if has_header
                            else len(row)
                        )
                        if has_header and None in row:
                            observed_columns += len(row[None] or [])
                        if observed_columns > column_limit:
                            raise ResourceLimitError(
                                "CSV import columns",
                                column_limit,
                                observed_columns,
                            )
                        if has_header:
                            batch.append(row)
                        else:
                            batch.append(
                                {
                                    f"column_{i}": value
                                    for i, value in enumerate(row)
                                }
                            )

                        if len(batch) >= validated_batch_size:
                            for record in batch:
                                self.db.insert(table, record)
                                total_inserted += 1
                            batch = []

                    # Insert remaining batch
                    for record in batch:
                        self.db.insert(table, record)
                        total_inserted += 1

            return total_inserted
        except Exception as e:
            if isinstance(e, (InputValidationError, ResourceLimitError)):
                raise
            raise ImportError(f"Failed to import from CSV: {e}")

    def from_excel(
        self,
        file_path: str,
        table: Optional[str] = None,
        sheet_name: Optional[Union[str, int]] = 0,
        create_table: bool = True,
        *,
        max_bytes: int = _DEFAULT_MAX_IMPORT_BYTES,
        max_rows: int = _DEFAULT_MAX_IMPORT_ROWS,
        max_columns: int = _DEFAULT_MAX_IMPORT_COLUMNS,
        max_uncompressed_bytes: int = _DEFAULT_MAX_EXCEL_EXPANDED_BYTES,
        max_compression_ratio: float = _DEFAULT_MAX_COMPRESSION_RATIO,
        max_archive_members: int = _DEFAULT_MAX_ARCHIVE_MEMBERS,
    ):
        """
        Import data from Excel file.
        
        Args:
            file_path: Input file path
            table: Target table name (defaults to sheet name)
            sheet_name: Sheet name or index to import
            create_table: Auto-create table if it doesn't exist
            max_bytes: Maximum workbook file bytes
            max_rows: Maximum worksheet data rows
            max_columns: Maximum worksheet columns
            max_uncompressed_bytes: Maximum expanded ZIP member bytes
            max_compression_ratio: Maximum ZIP expansion ratio
            max_archive_members: Maximum ZIP member count
        """
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for Excel import")

        try:
            byte_limit = _validate_resource_limit(
                max_bytes,
                "max_bytes",
                _HARD_MAX_IMPORT_BYTES,
            )
            row_limit = _validate_resource_limit(
                max_rows,
                "max_rows",
                _HARD_MAX_IMPORT_ROWS,
            )
            column_limit = _validate_resource_limit(
                max_columns,
                "max_columns",
                _HARD_MAX_IMPORT_COLUMNS,
            )
            _validate_file_size(file_path, byte_limit, "Excel import bytes")
            workbook_bytes = _read_bounded_bytes(
                file_path,
                byte_limit,
                "Excel import bytes",
            )
            workbook_stream = io.BytesIO(workbook_bytes)
            _validate_zip_expansion(
                workbook_stream,
                max_uncompressed_bytes=max_uncompressed_bytes,
                max_compression_ratio=max_compression_ratio,
                max_members=max_archive_members,
            )
            workbook_stream.seek(0)
            df = pd.read_excel(workbook_stream, sheet_name=sheet_name)  # type: ignore
            observed_rows, observed_columns = df.shape  # type: ignore
            if observed_rows > row_limit:
                raise ResourceLimitError(
                    "Excel import rows",
                    row_limit,
                    observed_rows,
                )
            if observed_columns > column_limit:
                raise ResourceLimitError(
                    "Excel import columns",
                    column_limit,
                    observed_columns,
                )

            # Use sheet name as table name if not provided
            if table is None:
                if isinstance(sheet_name, str):
                    table = sheet_name
                else:
                    table = f"sheet_{sheet_name}"

            # Convert DataFrame to records
            records = df.to_dict("records")  # type: ignore

            if not records:
                return 0
            _validate_import_records(
                records,
                max_rows=row_limit,
                max_columns=column_limit,
                format_name="Excel",
            )

            # Create table if needed
            if create_table:
                schema = self._infer_schema(records[0])
                self.db.create_table(table, schema)

            # Insert data
            total_inserted = 0
            with self.db.transaction():
                for record in records:
                    # Convert NaN to None
                    clean_record = {
                        key: (None if pd.isna(value) else value)  # type: ignore
                        for key, value in record.items()
                    }
                    self.db.insert(table, clean_record)  # type: ignore
                    total_inserted += 1

            return total_inserted
        except Exception as e:
            if isinstance(e, (InputValidationError, ResourceLimitError)):
                raise
            raise ImportError(f"Failed to import from Excel: {e}")

    def from_sql(
        self,
        file_path: str,
        *,
        max_bytes: int = _DEFAULT_MAX_RESTORE_BYTES,
    ):
        """
        Execute a trusted SQLite SQL script.

        SQL files contain executable statements. Callers must accept files only
        from a trusted source. This method rejects non-SQLite engines until they
        have a driver-native script implementation.
        
        Args:
            file_path: Input SQL file path
            max_bytes: Maximum encoded script size accepted into memory

        Returns:
            Number of rows changed by the script
        """
        try:
            limit = _validate_resource_limit(
                max_bytes,
                "max_bytes",
                _HARD_MAX_IMPORT_BYTES,
            )
            if self.db.engine != "sqlite" or not isinstance(
                self.db.connection, sqlite3.Connection
            ):
                raise ImportError(
                    "SQL script import currently supports SQLite only; use a "
                    "driver-native migration tool for other engines"
                )

            with open(file_path, "rb") as stream:
                encoded_content = stream.read(limit + 1)
            if len(encoded_content) > limit:
                raise ResourceLimitError(
                    "SQL import bytes",
                    limit,
                    len(encoded_content),
                )
            try:
                sql_content = encoded_content.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ImportError("SQL script must use UTF-8 encoding") from exc

            before_changes = self.db.connection.total_changes
            try:
                self.db.connection.executescript(sql_content)
            except Exception:
                self.db.connection.rollback()
                raise
            return self.db.connection.total_changes - before_changes
        except Exception as e:
            if isinstance(e, (InputValidationError, ResourceLimitError)):
                raise
            if isinstance(e, ImportError):
                raise
            raise ImportError(f"Failed to import from SQL: {e}") from e

    def from_dict(
        self,
        data: Union[Dict, List[Dict]],
        table: str,
        create_table: bool = True,
        *,
        max_rows: int = _DEFAULT_MAX_IMPORT_ROWS,
        max_columns: int = _DEFAULT_MAX_IMPORT_COLUMNS,
    ):
        """
        Import data from Python dictionary or list of dictionaries.
        
        Args:
            data: Dictionary or list of dictionaries
            table: Target table name
            create_table: Auto-create table if it doesn't exist
            max_rows: Maximum records
            max_columns: Maximum keys in one record
        """
        try:
            row_limit = _validate_resource_limit(
                max_rows,
                "max_rows",
                _HARD_MAX_IMPORT_ROWS,
            )
            column_limit = _validate_resource_limit(
                max_columns,
                "max_columns",
                _HARD_MAX_IMPORT_COLUMNS,
            )
            if isinstance(data, dict):
                data = [data]

            if not isinstance(data, list):
                raise ImportError("Dictionary import data must be a dict or list")
            if not data:
                return 0
            _validate_import_records(
                data,
                max_rows=row_limit,
                max_columns=column_limit,
                format_name="dictionary",
            )

            # Create table if needed
            if create_table:
                schema = self._infer_schema(data[0])
                self.db.create_table(table, schema)

            # Insert data
            total_inserted = 0
            with self.db.transaction():
                for record in data:
                    self.db.insert(table, record)
                    total_inserted += 1

            return total_inserted
        except Exception as e:
            if isinstance(e, (InputValidationError, ResourceLimitError)):
                raise
            if isinstance(e, ImportError):
                raise
            raise ImportError(f"Failed to import from dictionary: {e}")
    
    def _infer_schema(self, sample: Dict) -> Dict[str, str]:
        """
        Infer table schema from sample data.
        
        Args:
            sample: Sample record
            
        Returns:
            Dictionary of column names to SQL types
        """
        schema = {}
        
        for key, value in sample.items():
            if value is None:
                schema[key] = "TEXT"
            elif isinstance(value, bool):
                schema[key] = "BOOLEAN"
            elif isinstance(value, int):
                schema[key] = "INTEGER"
            elif isinstance(value, float):
                schema[key] = "REAL"
            elif isinstance(value, (datetime, str)):
                schema[key] = "TEXT"
            else:
                schema[key] = "TEXT"
        
        return schema


class BackupRestore:
    """
    SQLite backup and restore with secure file handling and bounded extraction.

    SQL backups contain executable schema statements. Restore them only from a
    trusted source. The restore process executes SQL in an isolated staging
    database before it replaces the target database.
    """
    
    def __init__(self, db: Database):
        """
        Initialize backup/restore system.
        
        Args:
            db: Database instance
        """
        self.db = db
        self.exporter = DataExporter(db)
        self.importer = DataImporter(db)

    def _require_sqlite(self, operation: str) -> sqlite3.Connection:
        if self.db.engine != "sqlite" or not isinstance(
            self.db.connection, sqlite3.Connection
        ):
            raise DatabaseError(
                f"{operation} currently supports SQLite only; use the database "
                "engine's native backup tooling"
            )
        return self.db.connection

    @staticmethod
    def _normalize_format(format_name: str, operation: str) -> str:
        if not isinstance(format_name, str):
            raise DatabaseError(f"{operation} format must be a string")
        normalized = format_name.lower()
        if normalized not in {"sql", "json"}:
            raise DatabaseError(
                f"Unsupported {operation.lower()} format: {format_name!r}"
            )
        return normalized

    def _sqlite_user_tables(self) -> List[str]:
        return [
            row["name"]
            for row in self.db.fetch_all(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]

    def _write_sql_backup(self, backup_path: str, include_schema: bool) -> None:
        connection = self._require_sqlite("Backup")
        with _sqlite_snapshot(connection) as snapshot:
            with _atomic_text_writer(backup_path) as stream:
                if include_schema:
                    for statement in snapshot.iterdump():
                        stream.write(statement)
                        stream.write("\n")
                    return

                stream.write("BEGIN TRANSACTION;\n")
                for statement in snapshot.iterdump():
                    if statement.startswith("INSERT INTO"):
                        stream.write(statement)
                        stream.write("\n")
                stream.write("COMMIT;\n")

    def _write_json_backup(self, backup_path: str) -> None:
        connection = self._require_sqlite("Backup")
        table_payload: Dict[str, Any] = {}
        with _sqlite_snapshot(connection) as snapshot:
            tables = [
                row["name"]
                for row in snapshot.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
                    "ORDER BY name"
                )
            ]
            for table in tables:
                qtable = _qtable("sqlite", table)
                schema = snapshot.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                    (table,),
                ).fetchone()
                # Bandit B608 review: _qtable() validated and quoted the metadata name.
                rows = snapshot.execute(f"SELECT * FROM {qtable}")  # nosec B608
                table_payload[table] = {
                    "schema": schema["sql"] if schema else None,
                    "rows": [
                        {
                            key: _encode_json_backup_value(value)
                            for key, value in dict(row).items()
                        }
                        for row in rows
                    ],
                }

        payload = {
            "format": _BACKUP_FORMAT_NAME,
            "version": _BACKUP_FORMAT_VERSION,
            "engine": "sqlite",
            "tables": table_payload,
        }
        with _atomic_text_writer(backup_path) as stream:
            json.dump(payload, stream, indent=2, ensure_ascii=False)
            stream.write("\n")

    def backup(
        self,
        backup_path: str,
        format: str = "sql",
        include_schema: bool = True,
        compress: bool = False,
    ) -> str:
        """
        Create an atomic mode-0600 SQLite backup.
        
        Args:
            backup_path: Backup file path
            format: Backup format (`sql` or `json`)
            include_schema: Include schema in SQL output
            compress: Write gzip output and remove the temporary plaintext copy

        Returns:
            Path to the completed backup
        """
        normalized_format = self._normalize_format(format, "Backup")
        self._require_sqlite("Backup")
        requested_path = _text_file_path(backup_path)

        try:
            if not compress:
                if normalized_format == "sql":
                    self._write_sql_backup(requested_path, include_schema)
                else:
                    self._write_json_backup(requested_path)
                return requested_path

            destination = (
                requested_path
                if requested_path.endswith(".gz")
                else f"{requested_path}.gz"
            )
            directory = os.path.dirname(destination) or os.curdir
            raw_path = _secure_temp_path(
                directory, suffix=f".{normalized_format}"
            )
            try:
                if normalized_format == "sql":
                    self._write_sql_backup(raw_path, include_schema)
                else:
                    self._write_json_backup(raw_path)
                _compress_file_atomic(raw_path, destination)
            finally:
                try:
                    os.remove(raw_path)
                except FileNotFoundError:
                    pass
            return destination
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            raise DatabaseError(f"Backup failed: {e}") from e

    @staticmethod
    def _read_bounded_file(file_path: str, max_bytes: int) -> bytes:
        with open(file_path, "rb") as stream:
            content = stream.read(max_bytes + 1)
        if len(content) > max_bytes:
            raise DatabaseError(
                "Backup exceeds the configured uncompressed byte limit"
            )
        return content

    def _sql_staging_database(
        self, backup_path: str, max_bytes: int
    ) -> sqlite3.Connection:
        content = self._read_bounded_file(backup_path, max_bytes)
        try:
            script = content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DatabaseError("SQL backup must use UTF-8 encoding") from exc

        staging = sqlite3.connect(":memory:")
        staging.set_authorizer(_sqlite_restore_authorizer)
        try:
            staging.executescript(script)
            return staging
        except Exception:
            staging.rollback()
            staging.close()
            raise

    @staticmethod
    def _decode_json_tables(payload: Any) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            raise DatabaseError("JSON backup root must be an object")

        if payload.get("format") == _BACKUP_FORMAT_NAME:
            if payload.get("version") != _BACKUP_FORMAT_VERSION:
                raise DatabaseError(
                    f"Unsupported JSON backup version: {payload.get('version')!r}"
                )
            if payload.get("engine") != "sqlite":
                raise DatabaseError("JSON backup engine must be 'sqlite'")
            tables = payload.get("tables")
            if not isinstance(tables, dict):
                raise DatabaseError("JSON backup tables must be an object")
            return tables

        # Version 1 retains read compatibility with the legacy table-to-rows shape.
        return payload

    def _json_staging_database(
        self, backup_path: str, max_bytes: int
    ) -> sqlite3.Connection:
        content = self._read_bounded_file(backup_path, max_bytes)
        try:
            payload = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise DatabaseError("JSON backup is not valid UTF-8 JSON") from exc

        tables = self._decode_json_tables(payload)
        staging_db = Database(engine="sqlite", database=":memory:")
        staging = staging_db.connection
        staging.set_authorizer(_sqlite_restore_authorizer)  # type: ignore[union-attr]
        expected_tables = set()
        try:
            for table, table_data in tables.items():
                _validate_ident(table)

                if isinstance(table_data, dict) and set(table_data) == {
                    "schema",
                    "rows",
                }:
                    schema = table_data["schema"]
                    rows = table_data["rows"]
                    if not isinstance(schema, str) or not re.match(
                        r"^\s*CREATE\s+TABLE\b", schema, flags=re.IGNORECASE
                    ):
                        raise DatabaseError(
                            f"JSON backup has invalid schema for table {table!r}"
                        )
                    if not isinstance(rows, list):
                        raise DatabaseError(
                            f"JSON backup rows must be a list for table {table!r}"
                        )
                    staging.execute(schema)  # type: ignore[union-attr]
                    expected_tables.add(table)
                    for row in rows:
                        if not isinstance(row, dict):
                            raise DatabaseError(
                                f"JSON backup row must be an object for table {table!r}"
                            )
                        decoded_row = {
                            key: _decode_json_backup_value(value)
                            for key, value in row.items()
                        }
                        staging_db.insert(table, decoded_row)
                    continue

                # Legacy backups contain a list of row objects and no schema.
                if not isinstance(table_data, list):
                    raise DatabaseError(
                        f"Legacy JSON backup rows must be a list for table {table!r}"
                    )
                if table_data:
                    if not all(isinstance(row, dict) for row in table_data):
                        raise DatabaseError(
                            f"Legacy JSON backup row must be an object for table {table!r}"
                        )
                    DataImporter(staging_db).from_dict(
                        table_data, table, create_table=True
                    )
                    expected_tables.add(table)

            actual_tables = {
                row[0]
                for row in staging.execute(  # type: ignore[union-attr]
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            }
            if actual_tables != expected_tables:
                raise DatabaseError(
                    "JSON backup schema created unexpected database objects"
                )

            staging_db.commit()
            if staging_db.cursor is not None:
                staging_db.cursor.close()
            staging_db.cursor = None
            staging_db.connection = None
            return staging  # type: ignore[return-value]
        except Exception:
            staging_db.close()
            raise

    def _replace_from_staging(
        self, staging: sqlite3.Connection, clear_existing: bool
    ) -> None:
        target = self._require_sqlite("Restore")
        if target.in_transaction:
            raise DatabaseError(
                "Commit or rollback the target database before restore"
            )

        existing_tables = self._sqlite_user_tables()
        if existing_tables and not clear_existing:
            raise DatabaseError(
                "Target database contains user tables; set clear_existing=True and "
                "allow_destructive=True to replace it"
            )

        staging.backup(target)
        cursor = self.db.cursor
        if cursor is not None:
            cursor.close()
        self.db.cursor = target.cursor()

    def restore(
        self,
        backup_path: str,
        format: str = "sql",
        clear_existing: bool = False,
        *,
        allow_destructive: bool = False,
        max_uncompressed_bytes: int = _DEFAULT_MAX_RESTORE_BYTES,
        max_compression_ratio: float = _DEFAULT_MAX_COMPRESSION_RATIO,
    ) -> None:
        """
        Restore a SQLite backup through an isolated staging database.
        
        Args:
            backup_path: Backup file path
            format: Backup format ('sql', 'json')
            clear_existing: Replace an existing target database
            allow_destructive: Required authorization for `clear_existing=True`
            max_uncompressed_bytes: Maximum accepted restore size
            max_compression_ratio: Maximum gzip expansion ratio

        SQL backup files contain executable schema statements. Restore them only
        from a trusted source. This method denies SQLite file attachment and
        writable-schema pragmas while it builds the staging database.
        """
        normalized_format = self._normalize_format(format, "Restore")
        self._require_sqlite("Restore")
        max_bytes = _validate_resource_limit(
            max_uncompressed_bytes,
            "max_uncompressed_bytes",
            _HARD_MAX_RESTORE_BYTES,
        )
        ratio_limit = _validate_resource_ratio(
            max_compression_ratio,
            "max_compression_ratio",
            _HARD_MAX_RESTORE_COMPRESSION_RATIO,
        )
        if clear_existing and not allow_destructive:
            raise DatabaseError(
                "Destructive restore requires allow_destructive=True"
            )

        requested_path = _text_file_path(backup_path)
        if not os.path.isfile(requested_path):
            raise DatabaseError(f"Backup file does not exist: {requested_path!r}")

        temp_path: Optional[str] = None
        staging: Optional[sqlite3.Connection] = None
        try:
            restore_path = requested_path
            if requested_path.endswith(".gz"):
                temp_path = _extract_gzip_bounded(
                    requested_path,
                    suffix=f".{normalized_format}",
                    max_uncompressed_bytes=max_bytes,
                    max_compression_ratio=ratio_limit,
                )
                restore_path = temp_path
            elif os.path.getsize(requested_path) > max_bytes:
                raise DatabaseError(
                    "Backup exceeds the configured uncompressed byte limit"
                )

            if normalized_format == "sql":
                staging = self._sql_staging_database(restore_path, max_bytes)
            else:
                staging = self._json_staging_database(restore_path, max_bytes)

            self._replace_from_staging(staging, clear_existing)
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise DatabaseError(f"Restore failed: {e}") from e
            raise DatabaseError(f"Restore failed: {e}") from e
        finally:
            if staging is not None:
                staging.close()
            if temp_path is not None:
                try:
                    os.remove(temp_path)
                except FileNotFoundError:
                    pass
class CacheManager:
    """Bounded process-local LRU cache for database query results."""

    def __init__(
        self,
        db: Database,
        ttl: float = 300,
        *,
        max_entries: int = _DEFAULT_CACHE_MAX_ENTRIES,
        max_weight_bytes: int = _DEFAULT_CACHE_MAX_WEIGHT_BYTES,
        clock: Callable[[], float] = time.monotonic,
    ):
        """Initialize cache limits and a monotonic expiry clock."""
        if not callable(clock):
            raise InputValidationError("clock must be callable")
        self.db = db
        self.ttl = _validate_resource_duration(
            ttl,
            "ttl",
            _HARD_MAX_CACHE_TTL_SECONDS,
        )
        self.max_entries = _validate_resource_limit(
            max_entries,
            "max_entries",
            _HARD_MAX_CACHE_ENTRIES,
        )
        self.max_weight_bytes = _validate_resource_limit(
            max_weight_bytes,
            "max_weight_bytes",
            _HARD_MAX_CACHE_WEIGHT_BYTES,
        )
        self._clock = clock
        self.cache = OrderedDict()
        self._total_weight = 0
        self._lock = threading.RLock()

    def _cache_key(self, query: str, params: Optional[Tuple] = None) -> str:
        """Generate a length-framed SHA-256 key from query text and parameters."""
        if not isinstance(query, str):
            raise InputValidationError("query must be text")
        query_bytes = query.encode("utf-8")
        params_bytes = repr(params).encode("utf-8")
        digest = hashlib.sha256()
        digest.update(len(query_bytes).to_bytes(8, "big"))
        digest.update(query_bytes)
        digest.update(len(params_bytes).to_bytes(8, "big"))
        digest.update(params_bytes)
        return digest.hexdigest()

    def _remove(self, key: str) -> None:
        _, _, weight = self.cache.pop(key)
        self._total_weight -= weight

    def _prune_expired(self, current_time: float) -> None:
        for key, (_, expires_at, _) in list(self.cache.items()):
            if expires_at <= current_time:
                self._remove(key)

    def get(self, query: str, params: Optional[Tuple] = None) -> Optional[List[Dict]]:
        """Return an isolated cached result or ``None`` after expiry."""
        key = self._cache_key(query, params)
        with self._lock:
            cached = self.cache.get(key)
            if cached is None:
                return None
            result, expires_at, _ = cached
            if expires_at <= self._clock():
                self._remove(key)
                return None
            self.cache.move_to_end(key)
            try:
                return copy.deepcopy(result)
            except Exception:
                self._remove(key)
                return None

    def set(
        self,
        query: str,
        result: List[Dict],
        params: Optional[Tuple] = None,
    ) -> None:
        """Cache an isolated result when it fits the configured weight budget."""
        key = self._cache_key(query, params)
        try:
            isolated_result = copy.deepcopy(result)
        except Exception:
            return
        weight = _estimate_resource_weight(
            (key, isolated_result),
            self.max_weight_bytes,
        )
        if weight > self.max_weight_bytes:
            return

        current_time = self._clock()
        with self._lock:
            self._prune_expired(current_time)
            if key in self.cache:
                self._remove(key)
            while self.cache and (
                len(self.cache) >= self.max_entries
                or self._total_weight + weight > self.max_weight_bytes
            ):
                self._remove(next(iter(self.cache)))
            self.cache[key] = (isolated_result, current_time + self.ttl, weight)
            self._total_weight += weight

    def clear(self) -> None:
        """Clear cached results and release their accounted weight."""
        with self._lock:
            _ordered_dict_clear(self.cache)
            self._total_weight = 0

    def cache_info(self) -> Dict[str, Union[int, float]]:
        """Return current cache use and configured limits."""
        with self._lock:
            self._prune_expired(self._clock())
            return {
                "entries": len(self.cache),
                "max_entries": self.max_entries,
                "weight_bytes": self._total_weight,
                "max_weight_bytes": self.max_weight_bytes,
                "ttl": self.ttl,
            }

    def fetch_with_cache(
        self,
        query: str,
        params: Optional[Tuple] = None,
    ) -> List[Dict]:
        """Fetch a query and retain an isolated copy under the cache budgets."""
        result = self.get(query, params)
        if result is not None:
            return result
        result = self.db.fetch_all(query, params)
        self.set(query, result, params)
        return result


# Utility functions for common database operations

def connect(engine: str = "sqlite", **kwargs) -> Database:
    """
    Create and return a database connection.
    
    Args:
        engine: Database engine
        **kwargs: Connection parameters
        
    Returns:
        Database instance
    """
    return Database(engine, **kwargs)


def quick_query(query: str, params: Optional[Tuple] = None,
                engine: str = "sqlite", **kwargs) -> List[Dict]:
    """
    Execute a quick query without maintaining connection.
    
    Args:
        query: SQL query
        params: Query parameters
        engine: Database engine
        **kwargs: Connection parameters
        
    Returns:
        Query results
    """
    with Database(engine, **kwargs) as db:
        return db.fetch_all(query, params)


def bulk_insert(table: str, data: List[Dict], 
                engine: str = "sqlite", **kwargs) -> int:
    """
    Bulk insert data into a table.
    
    Args:
        table: Table name
        data: List of records
        engine: Database engine
        **kwargs: Connection parameters
        
    Returns:
        Number of inserted records
    """
    with Database(engine, **kwargs) as db:
        count = 0
        with db.transaction():
            for record in data:
                db.insert(table, record)
                count += 1
        return count


def table_exists(table: str, engine: str = "sqlite", **kwargs) -> bool:
    """
    Check if a table exists.
    
    Args:
        table: Table name
        engine: Database engine
        **kwargs: Connection parameters
        
    Returns:
        True if table exists
    """
    with Database(engine, **kwargs) as db:
        if engine == "sqlite":
            result = db.fetch_one(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,)
            )
            return result is not None
        elif engine in ["postgres", "mysql"]:
            result = db.fetch_one(
                "SELECT table_name FROM information_schema.tables WHERE table_name = %s",
                (table,)
            )
            return result is not None
        else:
            return False
