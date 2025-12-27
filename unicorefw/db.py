"""
Database utilities for UniCoreFW.

This module provides comprehensive database functionality including connection management,
query execution, migrations, import/export, and support for multiple database engines.

Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info
"""

import json
import csv
import sqlite3
import threading
import time
import hashlib
import os
from typing import Any, Dict, List, Optional, Tuple, Union, Callable, Type
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

# Optional imports for additional database support
try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

try:
    import pymysql
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

try:
    import pymongo
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


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
        self.connection = psycopg2.connect(**kwargs)
        self.cursor = self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    def _init_mysql(self, **kwargs):
        """Initialize MySQL connection."""
        if not MYSQL_AVAILABLE:
            raise DatabaseError("pymysql is not installed")
        self.connection = pymysql.connect(**kwargs)
        self.cursor = self.connection.cursor(pymysql.cursors.DictCursor)
    
    def _init_mongodb(self, **kwargs):
        """Initialize MongoDB connection."""
        if not MONGODB_AVAILABLE:
            raise DatabaseError("pymongo is not installed")
        client = pymongo.MongoClient(**kwargs)
        self.connection = client[kwargs.get("database", "test")]
    
    def _init_redis(self, **kwargs):
        """Initialize Redis connection."""
        if not REDIS_AVAILABLE:
            raise DatabaseError("redis is not installed")
        self.connection = redis.Redis(**kwargs)
    
    def close(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        if self._pool:
            self._pool.close_all()
    
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
                self.cursor.execute("BEGIN")
    
    def commit(self):
        """Commit the current transaction."""
        if self.engine in ["sqlite", "postgres", "mysql"]:
            self.connection.commit()
            self._transaction_active = False
    
    def rollback(self):
        """Rollback the current transaction."""
        if self.engine in ["sqlite", "postgres", "mysql"]:
            self.connection.rollback()
            self._transaction_active = False
    
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
                    self.cursor.execute(query, params)
                else:
                    self.cursor.execute(query)
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
            return [dict(row) for row in self.cursor.fetchall()]
        else:
            return self.cursor.fetchall()
    
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
        result = self.cursor.fetchone()
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
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" if self.engine == "sqlite" else "%s" for _ in data])
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            
            self.execute(query, tuple(data.values()))
            
            if self.engine == "sqlite":
                return self.cursor.lastrowid
            elif self.engine == "postgres":
                self.cursor.execute("SELECT LASTVAL()")
                return self.cursor.fetchone()[0]
            else:  # mysql
                return self.cursor.lastrowid
        elif self.engine == "mongodb":
            result = self.connection[table].insert_one(data)
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
            set_clause = ", ".join([f"{k} = ?" if self.engine == "sqlite" else f"{k} = %s" 
                                   for k in data.keys()])
            where_clause = " AND ".join([f"{k} = ?" if self.engine == "sqlite" else f"{k} = %s" 
                                        for k in where.keys()])
            query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
            
            params = tuple(list(data.values()) + list(where.values()))
            self.execute(query, params)
            return self.cursor.rowcount
        elif self.engine == "mongodb":
            result = self.connection[table].update_many(where, {"$set": data})
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
            where_clause = " AND ".join([f"{k} = ?" if self.engine == "sqlite" else f"{k} = %s" 
                                        for k in where.keys()])
            query = f"DELETE FROM {table} WHERE {where_clause}"
            
            self.execute(query, tuple(where.values()))
            return self.cursor.rowcount
        elif self.engine == "mongodb":
            result = self.connection[table].delete_many(where)
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
                columns.append(f"{name} {dtype}")
            
            query = f"CREATE TABLE IF NOT EXISTS {table} ({', '.join(columns)})"
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
            query = f"DROP TABLE IF EXISTS {table}"
            self.execute(query)
            self.commit()
        elif self.engine == "mongodb":
            self.connection[table].drop()
        else:
            raise DatabaseError(f"Drop table not supported for {self.engine}")


class QueryBuilder:
    """
    Fluent SQL query builder for complex queries.
    """
    
    def __init__(self, db: Optional[Database] = None):
        """
        Initialize query builder.
        
        Args:
            db: Optional Database instance for execution
        """
        self.db = db
        self._select_fields = []
        self._from_table = None
        self._joins = []
        self._where_conditions = []
        self._group_by_fields = []
        self._having_conditions = []
        self._order_by_fields = []
        self._limit_value = None
        self._offset_value = None
    
    def select(self, *fields) -> "QueryBuilder":
        """Add SELECT fields."""
        self._select_fields.extend(fields)
        return self
    
    def from_table(self, table: str) -> "QueryBuilder":
        """Set FROM table."""
        self._from_table = table
        return self
    
    def join(self, table: str, on: str, join_type: str = "INNER") -> "QueryBuilder":
        """Add JOIN clause."""
        self._joins.append(f"{join_type} JOIN {table} ON {on}")
        return self
    
    def where(self, condition: str, *params) -> "QueryBuilder":
        """Add WHERE condition."""
        self._where_conditions.append((condition, params))
        return self
    
    def group_by(self, *fields) -> "QueryBuilder":
        """Add GROUP BY fields."""
        self._group_by_fields.extend(fields)
        return self
    
    def having(self, condition: str) -> "QueryBuilder":
        """Add HAVING condition."""
        self._having_conditions.append(condition)
        return self
    
    def order_by(self, field: str, direction: str = "ASC") -> "QueryBuilder":
        """Add ORDER BY field."""
        self._order_by_fields.append(f"{field} {direction}")
        return self
    
    def limit(self, value: int) -> "QueryBuilder":
        """Set LIMIT value."""
        self._limit_value = value
        return self
    
    def offset(self, value: int) -> "QueryBuilder":
        """Set OFFSET value."""
        self._offset_value = value
        return self
    
    def build(self) -> Tuple[str, Tuple]:
        """
        Build the SQL query.
        
        Returns:
            Tuple of (query_string, parameters)
        """
        parts = []
        params = []
        
        # SELECT
        if self._select_fields:
            parts.append(f"SELECT {', '.join(self._select_fields)}")
        else:
            parts.append("SELECT *")
        
        # FROM
        if self._from_table:
            parts.append(f"FROM {self._from_table}")
        
        # JOIN
        for join in self._joins:
            parts.append(join)
        
        # WHERE
        if self._where_conditions:
            conditions = []
            for condition, cond_params in self._where_conditions:
                conditions.append(condition)
                params.extend(cond_params)
            parts.append(f"WHERE {' AND '.join(conditions)}")
        
        # GROUP BY
        if self._group_by_fields:
            parts.append(f"GROUP BY {', '.join(self._group_by_fields)}")
        
        # HAVING
        if self._having_conditions:
            parts.append(f"HAVING {' AND '.join(self._having_conditions)}")
        
        # ORDER BY
        if self._order_by_fields:
            parts.append(f"ORDER BY {', '.join(self._order_by_fields)}")
        
        # LIMIT
        if self._limit_value is not None:
            parts.append(f"LIMIT {self._limit_value}")
        
        # OFFSET
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
        self.db.create_table("_migrations", {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "version": "VARCHAR(255) UNIQUE",
            "applied_at": "TIMESTAMP",
            "checksum": "VARCHAR(64)"
        })
    
    def apply(self, version: str, up_sql: str, down_sql: Optional[str] = None):
        """
        Apply a migration.
        
        Args:
            version: Migration version identifier
            up_sql: SQL to apply the migration
            down_sql: Optional SQL to rollback the migration
        """
        # Check if already applied
        existing = self.db.fetch_one(
            "SELECT * FROM _migrations WHERE version = ?", 
            (version,)
        )
        
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
    
    def to_json(self, table_or_query: str, file_path: str, 
                params: Optional[Tuple] = None, indent: int = 2):
        """
        Export data to JSON file.
        
        Args:
            table_or_query: Table name or SQL query
            file_path: Output file path
            params: Query parameters if table_or_query is a query
            indent: JSON indentation
        """
        try:
            if " " in table_or_query:  # It's a query
                data = self.db.fetch_all(table_or_query, params)
            else:  # It's a table name
                data = self.db.fetch_all(f"SELECT * FROM {table_or_query}")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, default=str)
        except Exception as e:
            raise ExportError(f"Failed to export to JSON: {e}")
    
    def to_csv(self, table_or_query: str, file_path: str, 
               params: Optional[Tuple] = None, delimiter: str = ','):
        """
        Export data to CSV file.
        
        Args:
            table_or_query: Table name or SQL query
            file_path: Output file path
            params: Query parameters if table_or_query is a query
            delimiter: CSV delimiter
        """
        try:
            if " " in table_or_query:  # It's a query
                data = self.db.fetch_all(table_or_query, params)
            else:  # It's a table name
                data = self.db.fetch_all(f"SELECT * FROM {table_or_query}")
            
            if not data:
                raise ExportError("No data to export")
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys(), delimiter=delimiter)
                writer.writeheader()
                writer.writerows(data)
        except Exception as e:
            raise ExportError(f"Failed to export to CSV: {e}")
    
    def to_excel(self, tables_or_queries: Union[str, Dict[str, str]], 
                 file_path: str, params: Optional[Dict[str, Tuple]] = None):
        """
        Export data to Excel file.
        
        Args:
            tables_or_queries: Table name, query, or dict of sheet_name: query
            file_path: Output file path
            params: Query parameters
        """
        if not PANDAS_AVAILABLE:
            raise ExportError("pandas is required for Excel export")
        
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                if isinstance(tables_or_queries, str):
                    tables_or_queries = {"Sheet1": tables_or_queries}
                
                for sheet_name, table_or_query in tables_or_queries.items():
                    query_params = params.get(sheet_name) if params else None
                    
                    if " " in table_or_query:
                        data = self.db.fetch_all(table_or_query, query_params)
                    else:
                        data = self.db.fetch_all(f"SELECT * FROM {table_or_query}")
                    
                    df = pd.DataFrame(data)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        except Exception as e:
            raise ExportError(f"Failed to export to Excel: {e}")
    
    def to_sql(self, table: str, file_path: str, include_create: bool = True):
        """
        Export table data as SQL INSERT statements.
        
        Args:
            table: Table name
            file_path: Output file path
            include_create: Include CREATE TABLE statement
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if include_create and self.db.engine == "sqlite":
                    # Get table schema
                    schema = self.db.fetch_all(
                        f"SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                        (table,)
                    )
                    if schema:
                        f.write(f"{schema[0]['sql']};\n\n")
                
                # Get data
                data = self.db.fetch_all(f"SELECT * FROM {table}")
                
                for row in data:
                    columns = ', '.join(row.keys())
                    values = ', '.join([f"'{v}'" if v is not None else 'NULL' 
                                      for v in row.values()])
                    f.write(f"INSERT INTO {table} ({columns}) VALUES ({values});\n")
        except Exception as e:
            raise ExportError(f"Failed to export to SQL: {e}")
    
    def to_html(self, table_or_query: str, file_path: str, 
                params: Optional[Tuple] = None, css_style: Optional[str] = None):
        """
        Export data to HTML table.
        
        Args:
            table_or_query: Table name or SQL query
            file_path: Output file path
            params: Query parameters
            css_style: Optional CSS styling
        """
        try:
            if " " in table_or_query:
                data = self.db.fetch_all(table_or_query, params)
            else:
                data = self.db.fetch_all(f"SELECT * FROM {table_or_query}")
            
            html = ['<!DOCTYPE html>', '<html>', '<head>']
            
            if css_style:
                html.append(f'<style>{css_style}</style>')
            else:
                html.append('''<style>
                    table { border-collapse: collapse; width: 100%; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #4CAF50; color: white; }
                    tr:nth-child(even) { background-color: #f2f2f2; }
                </style>''')
            
            html.extend(['</head>', '<body>', '<table>'])
            
            if data:
                # Headers
                html.append('<thead><tr>')
                for key in data[0].keys():
                    html.append(f'<th>{key}</th>')
                html.append('</tr></thead>')
                
                # Data rows
                html.append('<tbody>')
                for row in data:
                    html.append('<tr>')
                    for value in row.values():
                        html.append(f'<td>{value if value is not None else ""}</td>')
                    html.append('</tr>')
                html.append('</tbody>')
            
            html.extend(['</table>', '</body>', '</html>'])
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(html))
        except Exception as e:
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
    
    def from_json(self, file_path: str, table: str, 
                  create_table: bool = True, batch_size: int = 1000):
        """
        Import data from JSON file.
        
        Args:
            file_path: Input file path
            table: Target table name
            create_table: Auto-create table if it doesn't exist
            batch_size: Number of records to insert at once
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                data = [data]
            
            if not data:
                return 0
            
            # Create table if needed
            if create_table:
                schema = self._infer_schema(data[0])
                self.db.create_table(table, schema)
            
            # Insert data in batches
            total_inserted = 0
            with self.db.transaction():
                for i in range(0, len(data), batch_size):
                    batch = data[i:i + batch_size]
                    for record in batch:
                        self.db.insert(table, record)
                        total_inserted += 1
            
            return total_inserted
        except Exception as e:
            raise ImportError(f"Failed to import from JSON: {e}")
    
    def from_csv(self, file_path: str, table: str, 
                 create_table: bool = True, delimiter: str = ',',
                 has_header: bool = True, batch_size: int = 1000):
        """
        Import data from CSV file.
        
        Args:
            file_path: Input file path
            table: Target table name
            create_table: Auto-create table if it doesn't exist
            delimiter: CSV delimiter
            has_header: Whether CSV has header row
            batch_size: Number of records to insert at once
        """
        try:
            total_inserted = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=delimiter) if has_header else csv.reader(f, delimiter=delimiter)
                
                first_row = next(reader, None)
                if not first_row:
                    return 0
                
                # Create table if needed
                if create_table:
                    if has_header:
                        schema = self._infer_schema(first_row)
                    else:
                        schema = {f"column_{i}": "TEXT" for i in range(len(first_row))}
                    self.db.create_table(table, schema)
                
                # Insert data
                with self.db.transaction():
                    # Insert first row
                    if has_header:
                        self.db.insert(table, first_row)
                    else:
                        self.db.insert(table, {f"column_{i}": v for i, v in enumerate(first_row)})
                    total_inserted += 1
                    
                    # Insert remaining rows
                    batch = []
                    for row in reader:
                        if has_header:
                            batch.append(row)
                        else:
                            batch.append({f"column_{i}": v for i, v in enumerate(row)})
                        
                        if len(batch) >= batch_size:
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
            raise ImportError(f"Failed to import from CSV: {e}")
    
    def from_excel(self, file_path: str, table: Optional[str] = None,
                   sheet_name: Optional[Union[str, int]] = 0,
                   create_table: bool = True):
        """
        Import data from Excel file.
        
        Args:
            file_path: Input file path
            table: Target table name (defaults to sheet name)
            sheet_name: Sheet name or index to import
            create_table: Auto-create table if it doesn't exist
        """
        if not PANDAS_AVAILABLE:
            raise ImportError("pandas is required for Excel import")
        
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Use sheet name as table name if not provided
            if table is None:
                if isinstance(sheet_name, str):
                    table = sheet_name
                else:
                    table = f"sheet_{sheet_name}"
            
            # Convert DataFrame to records
            records = df.to_dict('records')
            
            if not records:
                return 0
            
            # Create table if needed
            if create_table:
                schema = self._infer_schema(records[0])
                self.db.create_table(table, schema)
            
            # Insert data
            total_inserted = 0
            with self.db.transaction():
                for record in records:
                    # Convert NaN to None
                    clean_record = {k: (None if pd.isna(v) else v) 
                                  for k, v in record.items()}
                    self.db.insert(table, clean_record)
                    total_inserted += 1
            
            return total_inserted
        except Exception as e:
            raise ImportError(f"Failed to import from Excel: {e}")
    
    def from_sql(self, file_path: str):
        """
        Import data from SQL file.
        
        Args:
            file_path: Input SQL file path
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # Split by semicolon and execute each statement
            statements = sql_content.split(';')
            executed = 0
            
            with self.db.transaction():
                for statement in statements:
                    statement = statement.strip()
                    if statement:
                        self.db.execute(statement)
                        executed += 1
            
            return executed
        except Exception as e:
            raise ImportError(f"Failed to import from SQL: {e}")
    
    def from_dict(self, data: Union[Dict, List[Dict]], table: str,
                  create_table: bool = True):
        """
        Import data from Python dictionary or list of dictionaries.
        
        Args:
            data: Dictionary or list of dictionaries
            table: Target table name
            create_table: Auto-create table if it doesn't exist
        """
        try:
            if isinstance(data, dict):
                data = [data]
            
            if not data:
                return 0
            
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
    Database backup and restore functionality.
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
    
    def backup(self, backup_path: str, format: str = "sql",
               include_schema: bool = True, compress: bool = False):
        """
        Create database backup.
        
        Args:
            backup_path: Backup file path
            format: Backup format ('sql', 'json', 'csv')
            include_schema: Include table schemas
            compress: Compress backup file
        """
        try:
            if self.db.engine == "sqlite":
                if format == "sql":
                    # Get all tables
                    tables = self.db.fetch_all(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    )
                    
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        for table_info in tables:
                            table = table_info['name']
                            
                            if include_schema:
                                # Get CREATE TABLE statement
                                schema = self.db.fetch_one(
                                    "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                                    (table,)
                                )
                                if schema:
                                    f.write(f"{schema['sql']};\n\n")
                            
                            # Get data
                            data = self.db.fetch_all(f"SELECT * FROM {table}")
                            for row in data:
                                columns = ', '.join(row.keys())
                                values = ', '.join([f"'{v}'" if v is not None else 'NULL' 
                                                  for v in row.values()])
                                f.write(f"INSERT INTO {table} ({columns}) VALUES ({values});\n")
                            f.write("\n")
                
                elif format == "json":
                    backup_data = {}
                    tables = self.db.fetch_all(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    )
                    
                    for table_info in tables:
                        table = table_info['name']
                        backup_data[table] = self.db.fetch_all(f"SELECT * FROM {table}")
                    
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        json.dump(backup_data, f, indent=2, default=str)
            
            if compress:
                import gzip
                import shutil
                
                with open(backup_path, 'rb') as f_in:
                    with gzip.open(f"{backup_path}.gz", 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(backup_path)
                return f"{backup_path}.gz"
            
            return backup_path
        except Exception as e:
            raise DatabaseError(f"Backup failed: {e}")
    
    def restore(self, backup_path: str, format: str = "sql",
                clear_existing: bool = True):
        """
        Restore database from backup.
        
        Args:
            backup_path: Backup file path
            format: Backup format ('sql', 'json')
            clear_existing: Clear existing data before restore
        """
        try:
            # Handle compressed files
            if backup_path.endswith('.gz'):
                import gzip
                import tempfile
                
                with gzip.open(backup_path, 'rb') as f_in:
                    content = f_in.read()
                
                with tempfile.NamedTemporaryFile(mode='wb', delete=False, 
                                                suffix=f".{format}") as f_out:
                    f_out.write(content)
                    temp_path = f_out.name
                
                backup_path = temp_path
            
            if format == "sql":
                if clear_existing and self.db.engine == "sqlite":
                    # Drop all existing tables
                    tables = self.db.fetch_all(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    )
                    for table_info in tables:
                        self.db.drop_table(table_info['name'])
                
                # Import SQL file
                self.importer.from_sql(backup_path)
            
            elif format == "json":
                with open(backup_path, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                
                if clear_existing:
                    # Drop existing tables
                    for table in backup_data.keys():
                        self.db.drop_table(table)
                
                # Restore each table
                for table, data in backup_data.items():
                    if data:
                        self.importer.from_dict(data, table, create_table=True)
            
            # Clean up temp file if it exists
            if 'temp_path' in locals():
                os.remove(temp_path)
                
        except Exception as e:
            raise DatabaseError(f"Restore failed: {e}")


class CacheManager:
    """
    Query result caching for performance optimization.
    """
    
    def __init__(self, db: Database, ttl: int = 300):
        """
        Initialize cache manager.
        
        Args:
            db: Database instance
            ttl: Cache time-to-live in seconds
        """
        self.db = db
        self.ttl = ttl
        self.cache = {}
        self._lock = threading.Lock()
    
    def _cache_key(self, query: str, params: Optional[Tuple] = None) -> str:
        """Generate cache key from query and params."""
        key_str = query
        if params:
            key_str += str(params)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, query: str, params: Optional[Tuple] = None) -> Optional[List[Dict]]:
        """
        Get cached query result.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Cached result or None
        """
        with self._lock:
            key = self._cache_key(query, params)
            if key in self.cache:
                result, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl:
                    return result
                else:
                    del self.cache[key]
            return None
    
    def set(self, query: str, result: List[Dict], 
            params: Optional[Tuple] = None):
        """
        Cache query result.
        
        Args:
            query: SQL query
            result: Query result
            params: Query parameters
        """
        with self._lock:
            key = self._cache_key(query, params)
            self.cache[key] = (result, time.time())
    
    def clear(self):
        """Clear all cached results."""
        with self._lock:
            self.cache.clear()
    
    def fetch_with_cache(self, query: str, 
                        params: Optional[Tuple] = None) -> List[Dict]:
        """
        Fetch query result with caching.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Query result
        """
        # Check cache
        result = self.get(query, params)
        if result is not None:
            return result
        
        # Execute query
        result = self.db.fetch_all(query, params)
        
        # Cache result
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