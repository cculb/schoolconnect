"""Database connection management for PowerSchool data."""

import asyncio
import sqlite3
from pathlib import Path
from typing import Any

import aiosqlite


class Database:
    """SQLite database connection manager with async support."""

    def __init__(self, db_path: str | Path = "powerschool.db"):
        self.db_path = Path(db_path)
        self._connection: aiosqlite.Connection | None = None

    async def connect(self) -> "Database":
        """Establish database connection."""
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(self.db_path)
        self._connection.row_factory = aiosqlite.Row
        # Enable foreign keys
        await self._connection.execute("PRAGMA foreign_keys = ON")
        return self

    async def close(self) -> None:
        """Close database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def __aenter__(self) -> "Database":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    @property
    def connection(self) -> aiosqlite.Connection:
        """Get the current connection, raising if not connected."""
        if self._connection is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._connection

    async def execute(self, sql: str, params: tuple = ()) -> aiosqlite.Cursor:
        """Execute a single SQL statement."""
        return await self.connection.execute(sql, params)

    async def executemany(self, sql: str, params_list: list[tuple]) -> aiosqlite.Cursor:
        """Execute a SQL statement with multiple parameter sets."""
        return await self.connection.executemany(sql, params_list)

    async def executescript(self, sql: str) -> None:
        """Execute multiple SQL statements."""
        await self.connection.executescript(sql)

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.connection.commit()

    async def fetch_one(self, sql: str, params: tuple = ()) -> dict[str, Any] | None:
        """Fetch a single row as a dictionary."""
        cursor = await self.execute(sql, params)
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    async def fetch_all(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        """Fetch all rows as a list of dictionaries."""
        cursor = await self.execute(sql, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def init_schema(self) -> None:
        """Initialize the database schema from SQL files."""
        schema_path = Path(__file__).parent / "schema.sql"
        views_path = Path(__file__).parent / "views.sql"

        # Read and execute schema
        schema_sql = schema_path.read_text()
        await self.executescript(schema_sql)

        # Read and execute views
        views_sql = views_path.read_text()
        await self.executescript(views_sql)

        await self.commit()

    async def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        result = await self.fetch_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        return result is not None

    async def get_table_count(self, table_name: str) -> int:
        """Get the number of rows in a table."""
        result = await self.fetch_one(f"SELECT COUNT(*) as count FROM {table_name}")
        return result["count"] if result else 0


def get_sync_connection(db_path: str | Path = "powerschool.db") -> sqlite3.Connection:
    """Get a synchronous database connection (for CLI commands)."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db_sync(db_path: str | Path = "powerschool.db") -> None:
    """Initialize database synchronously (for CLI commands)."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    schema_path = Path(__file__).parent / "schema.sql"
    views_path = Path(__file__).parent / "views.sql"

    conn = get_sync_connection(db_path)
    try:
        conn.executescript(schema_path.read_text())
        conn.executescript(views_path.read_text())
        conn.commit()
    finally:
        conn.close()
