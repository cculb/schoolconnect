"""Database connection management for PowerSchool Portal.

This module provides connection pooling, WAL mode, and secure path handling
for SQLite database operations.
"""

import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from queue import Empty, Queue
from typing import Optional

from dotenv import load_dotenv

from src.logutils import get_logger

load_dotenv()

# Module logger
logger = get_logger(__name__)

# Default database path
DEFAULT_DB_PATH = Path(__file__).parent.parent.parent / "powerschool.db"
DB_PATH = Path(os.getenv("DATABASE_PATH", str(DEFAULT_DB_PATH)))

# Connection pool settings
_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
_POOL_TIMEOUT = float(os.getenv("DB_POOL_TIMEOUT", "30.0"))


class ConnectionPool:
    """Thread-safe SQLite connection pool with WAL mode support.

    Manages a pool of database connections to reduce connection overhead
    and enable concurrent read access with WAL mode.
    """

    def __init__(self, db_path: Path, pool_size: int = 5, timeout: float = 30.0):
        """Initialize the connection pool.

        Args:
            db_path: Path to the SQLite database file
            pool_size: Maximum number of connections to maintain
            timeout: Seconds to wait for an available connection
        """
        self._db_path = self._validate_path(db_path)
        self._pool_size = pool_size
        self._timeout = timeout
        self._pool: Queue[sqlite3.Connection] = Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        self._initialized = False

    @staticmethod
    def _validate_path(db_path: Path) -> Path:
        """Validate database path to prevent path traversal attacks.

        Args:
            db_path: Path to validate

        Returns:
            Resolved absolute path

        Raises:
            ValueError: If path contains traversal attempts or is invalid
        """
        resolved = db_path.resolve()

        # Check for path traversal attempts
        try:
            # Ensure the path doesn't escape expected directories
            str_path = str(resolved)
            if ".." in str(db_path) or str_path.startswith("/etc") or str_path.startswith("/var"):
                raise ValueError(f"Invalid database path: {db_path}")
        except (ValueError, RuntimeError) as e:
            raise ValueError(f"Invalid database path: {db_path}") from e

        return resolved

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection with optimal settings.

        Returns:
            Configured SQLite connection
        """
        conn = sqlite3.connect(
            str(self._db_path),
            check_same_thread=False,  # Allow cross-thread usage with pool
            timeout=self._timeout,
        )
        conn.row_factory = sqlite3.Row

        # Enable WAL mode for better concurrency (readers don't block writers)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")  # 5 second busy timeout
        conn.execute("PRAGMA synchronous = NORMAL")  # Balance safety/performance

        return conn

    def get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool.

        Returns:
            SQLite connection from the pool

        Raises:
            TimeoutError: If no connection available within timeout
        """
        try:
            conn = self._pool.get(block=True, timeout=self._timeout)
            # Verify connection is still valid
            try:
                conn.execute("SELECT 1")
                logger.debug("Reusing connection from pool", extra={"extra_data": {"pool_size": self._pool.qsize()}})
                return conn
            except sqlite3.Error:
                # Connection is dead, create a new one
                logger.debug("Dead connection detected, creating new one")
                return self._create_connection()
        except Empty:
            # Pool is empty, try to create a new connection
            with self._lock:
                if self._pool.qsize() < self._pool_size:
                    logger.debug("Pool empty, creating new connection")
                    return self._create_connection()
            logger.error("Connection pool exhausted", extra={"extra_data": {"timeout": self._timeout, "pool_size": self._pool_size}})
            raise TimeoutError(f"Connection pool exhausted after {self._timeout}s")

    def return_connection(self, conn: sqlite3.Connection) -> None:
        """Return a connection to the pool.

        Args:
            conn: Connection to return
        """
        try:
            self._pool.put_nowait(conn)
        except Exception:
            # Pool is full, close the connection
            try:
                conn.close()
            except sqlite3.Error:
                pass

    def close_all(self) -> None:
        """Close all connections in the pool."""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except (Empty, sqlite3.Error):
                pass


# Global connection pools (one per database path)
_pools: dict[Path, ConnectionPool] = {}
_pools_lock = threading.Lock()


def _get_pool(db_path: Optional[Path] = None) -> ConnectionPool:
    """Get or create a connection pool for the given path.

    Args:
        db_path: Database path (uses default if not provided)

    Returns:
        ConnectionPool instance for the path
    """
    path = (db_path or DB_PATH).resolve()

    with _pools_lock:
        if path not in _pools:
            _pools[path] = ConnectionPool(path, _POOL_SIZE, _POOL_TIMEOUT)
        return _pools[path]


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Get a database connection from the pool.

    Args:
        db_path: Path to database file (uses default if not provided)

    Returns:
        SQLite connection with row factory enabled
    """
    return _get_pool(db_path).get_connection()


@contextmanager
def get_db(db_path: Optional[Path] = None):
    """Context manager for database connections with automatic pool return.

    Args:
        db_path: Path to database file (uses default if not provided)

    Yields:
        SQLite connection

    Example:
        with get_db() as conn:
            cursor = conn.execute("SELECT * FROM students")
            results = cursor.fetchall()
    """
    pool = _get_pool(db_path)
    conn = pool.get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.return_connection(conn)


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
        logger.info("Removing existing database", extra={"extra_data": {"path": str(path)}})
        path.unlink()

    # Read schema and views
    schema_path = Path(__file__).parent / "schema.sql"
    views_path = Path(__file__).parent / "views.sql"

    with get_db(path) as conn:
        # Execute schema
        if schema_path.exists():
            schema_sql = schema_path.read_text()
            conn.executescript(schema_sql)
            logger.info("Schema created", extra={"extra_data": {"source": str(schema_path)}})

        # Execute views
        if views_path.exists():
            views_sql = views_path.read_text()
            conn.executescript(views_sql)
            logger.info("Views created", extra={"extra_data": {"source": str(views_path)}})

    logger.info("Database initialized", extra={"extra_data": {"path": str(path)}})
    return path


def verify_database(db_path: Optional[Path] = None) -> dict:
    """Verify database tables exist and return table info."""
    path = db_path or DB_PATH

    if not path.exists():
        return {"exists": False, "tables": [], "error": "Database file not found"}

    try:
        with get_db(path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row["name"] for row in cursor.fetchall()]

            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name")
            views = [row["name"] for row in cursor.fetchall()]

            # Get row counts (validate table names to prevent injection)
            counts = {}
            # Only count tables that exist in sqlite_master (already validated)
            for table in tables:
                # Extra validation: ensure table name is alphanumeric/underscore only
                if table.replace("_", "").isalnum():
                    cursor = conn.execute(
                        "SELECT COUNT(*) as cnt FROM sqlite_master WHERE type='table' AND name=?",
                        (table,),
                    )
                    if cursor.fetchone()["cnt"] > 0:
                        # Safe to query - table exists and name is validated
                        cursor = conn.execute(
                            f"SELECT COUNT(*) as cnt FROM [{table}]"  # Bracket quoting
                        )
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
    from src.logutils import configure_root_logger
    configure_root_logger()

    logger.info("Initializing database...")
    init_database(force=True)
    logger.info("Verifying database...")
    info = verify_database()
    logger.info("Database verification complete", extra={"extra_data": {
        "tables": info.get("tables", []),
        "views": info.get("views", []),
        "row_counts": info.get("row_counts", {}),
    }})
