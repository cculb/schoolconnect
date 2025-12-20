"""Database connection management for PowerSchool Portal."""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "powerschool.db"
DB_PATH = Path(os.getenv("DATABASE_PATH", str(DEFAULT_DB_PATH)))


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Get a database connection with row factory enabled."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db(db_path: Optional[Path] = None):
    """Context manager for database connections."""
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database(db_path: Optional[Path] = None, force: bool = False) -> Path:
    """Initialize the database with schema and views.

    Args:
        db_path: Path to database file (uses default if not provided)
        force: If True, delete existing database and recreate

    Returns:
        Path to the database file
    """
    path = db_path or DB_PATH

    if force and path.exists():
        path.unlink()

    # Read schema and views
    schema_path = Path(__file__).parent / "schema.sql"
    views_path = Path(__file__).parent / "views.sql"

    with get_db(path) as conn:
        # Execute schema
        if schema_path.exists():
            schema_sql = schema_path.read_text()
            conn.executescript(schema_sql)
            print(f"Schema created from {schema_path}")

        # Execute views
        if views_path.exists():
            views_sql = views_path.read_text()
            conn.executescript(views_sql)
            print(f"Views created from {views_path}")

    print(f"Database initialized at {path}")
    return path


def verify_database(db_path: Optional[Path] = None) -> dict:
    """Verify database tables exist and return table info."""
    path = db_path or DB_PATH

    if not path.exists():
        return {"exists": False, "tables": [], "error": "Database file not found"}

    try:
        with get_db(path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row["name"] for row in cursor.fetchall()]

            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='view' ORDER BY name"
            )
            views = [row["name"] for row in cursor.fetchall()]

            # Get row counts
            counts = {}
            for table in tables:
                cursor = conn.execute(f"SELECT COUNT(*) as cnt FROM {table}")
                counts[table] = cursor.fetchone()["cnt"]

            return {
                "exists": True,
                "path": str(path),
                "tables": tables,
                "views": views,
                "row_counts": counts,
            }
    except Exception as e:
        return {"exists": True, "error": str(e)}


if __name__ == "__main__":
    # Test database initialization
    print("Initializing database...")
    init_database(force=True)
    print("\nVerifying database...")
    info = verify_database()
    print(f"Tables: {info.get('tables', [])}")
    print(f"Views: {info.get('views', [])}")
    print(f"Row counts: {info.get('row_counts', {})}")
