"""Repository adapter for Streamlit chat application.

This module provides a thin adapter layer that wraps the existing Repository
pattern from src/database/repository.py for use in the Streamlit chat app.

Addresses:
- CRIT-3: Uses existing Repository pattern instead of duplicating queries
- CRIT-4: Provides input sanitization to prevent SQL injection via LIKE patterns
- CRIT-5: Uses connection pooling via get_db() context manager

Example:
    from repository_adapter import RepositoryAdapter

    adapter = RepositoryAdapter()
    student_id = adapter.get_student_id("Delilah")
    summary = adapter.get_student_summary("Delilah")
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from queue import Empty, Queue
from threading import Lock
from typing import Any, Dict, List, Optional

# Maximum length for student name input (prevents DoS via huge strings)
MAX_NAME_LENGTH = 100

# Connection pool settings
_POOL_SIZE = 5
_POOL_TIMEOUT = 30.0


def escape_like_pattern(value: str) -> str:
    """Escape special characters in LIKE pattern values.

    SQLite LIKE patterns treat % and _ as wildcards. This function escapes
    these characters so they are treated literally, preventing SQL injection
    via LIKE pattern manipulation.

    Args:
        value: The string to escape for use in a LIKE pattern.

    Returns:
        The escaped string safe for LIKE queries.

    Example:
        >>> escape_like_pattern("100%")
        '100\\%'
        >>> escape_like_pattern("test_user")
        'test\\_user'
    """
    if not value:
        return value

    # Escape backslash first (so we don't double-escape later escapes)
    value = value.replace("\\", "\\\\")
    # Escape percent sign (LIKE wildcard for any sequence)
    value = value.replace("%", "\\%")
    # Escape underscore (LIKE wildcard for single character)
    value = value.replace("_", "\\_")

    return value


def sanitize_student_name(name: str) -> str:
    """Sanitize student name input.

    Performs basic input validation and sanitization:
    - Strips leading/trailing whitespace
    - Limits length to prevent DoS attacks
    - Handles empty/null inputs

    Args:
        name: The raw student name input.

    Returns:
        Sanitized student name string.

    Example:
        >>> sanitize_student_name("  John  ")
        'John'
        >>> sanitize_student_name("A" * 500)
        'AAAA...' (truncated to MAX_NAME_LENGTH)
    """
    if not name:
        return ""

    # Strip whitespace
    name = name.strip()

    # Limit length
    if len(name) > MAX_NAME_LENGTH:
        name = name[:MAX_NAME_LENGTH]

    return name


class ConnectionPool:
    """Thread-safe SQLite connection pool for the Streamlit chat app.

    Provides connection pooling to reduce connection overhead and
    enable efficient concurrent access.
    """

    def __init__(self, db_path: Path, pool_size: int = 5, timeout: float = 30.0):
        """Initialize the connection pool.

        Args:
            db_path: Path to the SQLite database file.
            pool_size: Maximum number of connections to maintain.
            timeout: Seconds to wait for an available connection.
        """
        self._db_path = db_path
        self._pool_size = pool_size
        self._timeout = timeout
        self._pool: Queue[sqlite3.Connection] = Queue(maxsize=pool_size)
        self._lock = Lock()

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection with optimal settings.

        Returns:
            Configured SQLite connection with row factory.
        """
        conn = sqlite3.connect(
            str(self._db_path),
            check_same_thread=False,
            timeout=self._timeout,
        )
        conn.row_factory = sqlite3.Row

        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        conn.execute("PRAGMA synchronous = NORMAL")

        return conn

    def get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool.

        Returns:
            SQLite connection from the pool.

        Raises:
            TimeoutError: If no connection available within timeout.
        """
        try:
            conn = self._pool.get(block=True, timeout=self._timeout)
            # Verify connection is still valid
            try:
                conn.execute("SELECT 1")
                return conn
            except sqlite3.Error:
                # Connection is dead, create a new one
                return self._create_connection()
        except Empty:
            # Pool is empty, try to create a new connection
            with self._lock:
                if self._pool.qsize() < self._pool_size:
                    return self._create_connection()
            raise TimeoutError(f"Connection pool exhausted after {self._timeout}s")

    def return_connection(self, conn: sqlite3.Connection) -> None:
        """Return a connection to the pool.

        Args:
            conn: Connection to return.
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
_pools: Dict[Path, ConnectionPool] = {}
_pools_lock = Lock()


def _get_pool(db_path: Path) -> ConnectionPool:
    """Get or create a connection pool for the given path.

    Args:
        db_path: Database path.

    Returns:
        ConnectionPool instance for the path.
    """
    path = db_path.resolve()

    with _pools_lock:
        if path not in _pools:
            _pools[path] = ConnectionPool(path, _POOL_SIZE, _POOL_TIMEOUT)
        return _pools[path]


@contextmanager
def get_db(db_path: Path):
    """Context manager for database connections with automatic pool return.

    Args:
        db_path: Path to database file.

    Yields:
        SQLite connection.

    Example:
        with get_db(Path("test.db")) as conn:
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


class RepositoryAdapter:
    """Adapter for accessing PowerSchool data in the Streamlit chat app.

    This class wraps database operations with proper input sanitization,
    connection pooling, and parameterized queries to prevent SQL injection.

    Attributes:
        db_path: Path to the SQLite database file.

    Example:
        adapter = RepositoryAdapter(Path("powerschool.db"))
        student_id = adapter.get_student_id("Delilah")
        if student_id:
            summary = adapter.get_student_summary("Delilah")
    """

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize the repository adapter.

        Args:
            db_path: Path to SQLite database. Uses default if not provided.
        """
        if db_path is None:
            # Default to parent directory's powerschool.db
            parent_db = Path(__file__).parent.parent / "powerschool.db"
            local_db = Path(__file__).parent / "powerschool.db"
            self.db_path = parent_db if parent_db.exists() else local_db
        else:
            self.db_path = Path(db_path) if isinstance(db_path, str) else db_path

    def get_student_id(self, student_name: str) -> Optional[int]:
        """Get student ID from name (partial match on first name).

        Uses parameterized queries with escaped LIKE patterns to prevent
        SQL injection.

        Args:
            student_name: Student name to search for (partial match).

        Returns:
            Student database ID if found, None otherwise.
        """
        name = sanitize_student_name(student_name)
        if not name:
            return None

        # Escape LIKE pattern special characters
        escaped_name = escape_like_pattern(name)

        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id FROM students
                WHERE LOWER(first_name) LIKE LOWER(?) ESCAPE '\\'
                OR LOWER(first_name || ' ' || COALESCE(last_name, '')) LIKE LOWER(?) ESCAPE '\\'
                LIMIT 1
                """,
                (f"%{escaped_name}%", f"%{escaped_name}%"),
            )
            result = cursor.fetchone()
            return result["id"] if result else None

    def get_student_summary(self, student_name: str) -> Dict[str, Any]:
        """Get overall summary for a student.

        Args:
            student_name: Student name to search for.

        Returns:
            Dictionary with student summary data, or error dict if not found.
        """
        student_id = self.get_student_id(student_name)
        if not student_id:
            return {"error": f"Student '{student_name}' not found"}

        with get_db(self.db_path) as conn:
            # Get student info
            cursor = conn.execute(
                """
                SELECT first_name, last_name, grade_level, school_name
                FROM students WHERE id = ?
                """,
                (student_id,),
            )
            student = cursor.fetchone()

            # Get missing assignment count
            cursor = conn.execute(
                """
                SELECT COUNT(*) as count FROM assignments
                WHERE student_id = ? AND status = 'Missing'
                """,
                (student_id,),
            )
            missing_count = cursor.fetchone()["count"]

            # Get attendance
            cursor = conn.execute(
                """
                SELECT attendance_rate, days_absent, tardies, total_days
                FROM attendance_summary WHERE student_id = ?
                ORDER BY recorded_at DESC LIMIT 1
                """,
                (student_id,),
            )
            attendance = cursor.fetchone()

            # Get course count
            cursor = conn.execute(
                """
                SELECT COUNT(DISTINCT course_name) as count FROM courses WHERE student_id = ?
                """,
                (student_id,),
            )
            course_count = cursor.fetchone()["count"]

            return {
                "student_id": student_id,
                "name": f"{student['first_name']} {student['last_name'] or ''}".strip(),
                "grade_level": student["grade_level"],
                "school_name": student["school_name"],
                "missing_assignments": missing_count,
                "attendance_rate": attendance["attendance_rate"] if attendance else None,
                "days_absent": attendance["days_absent"] if attendance else 0,
                "tardies": attendance["tardies"] if attendance else 0,
                "total_days": attendance["total_days"] if attendance else 0,
                "course_count": course_count,
            }

    def get_missing_assignments(self, student_name: str) -> List[Dict[str, Any]]:
        """Get list of missing assignments for a student.

        Args:
            student_name: Student name to search for.

        Returns:
            List of missing assignment dictionaries.
        """
        student_id = self.get_student_id(student_name)
        if not student_id:
            return []

        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT
                    assignment_name,
                    course_name,
                    teacher_name,
                    category,
                    due_date,
                    term,
                    status
                FROM assignments
                WHERE student_id = ? AND status = 'Missing'
                ORDER BY due_date DESC
                """,
                (student_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_current_grades(self, student_name: str) -> List[Dict[str, Any]]:
        """Get current grades for all courses.

        Args:
            student_name: Student name to search for.

        Returns:
            List of grade dictionaries.
        """
        student_id = self.get_student_id(student_name)
        if not student_id:
            return []

        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT
                    c.course_name,
                    c.teacher_name,
                    c.room,
                    g.term,
                    g.letter_grade,
                    g.percent
                FROM courses c
                LEFT JOIN grades g ON g.course_id = c.id AND g.student_id = c.student_id
                WHERE c.student_id = ?
                ORDER BY c.course_name
                """,
                (student_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_attendance_summary(self, student_name: str) -> Dict[str, Any]:
        """Get attendance summary for a student.

        Args:
            student_name: Student name to search for.

        Returns:
            Attendance summary dictionary, or error dict if not found.
        """
        student_id = self.get_student_id(student_name)
        if not student_id:
            return {"error": f"Student '{student_name}' not found"}

        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT
                    term,
                    attendance_rate as rate,
                    days_present,
                    days_absent,
                    tardies,
                    total_days
                FROM attendance_summary
                WHERE student_id = ?
                ORDER BY recorded_at DESC
                LIMIT 1
                """,
                (student_id,),
            )
            result = cursor.fetchone()

            if result:
                return dict(result)
            return {"error": "No attendance data found"}

    def get_upcoming_assignments(self, student_name: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get assignments due in the next N days.

        Args:
            student_name: Student name to search for.
            days: Number of days to look ahead.

        Returns:
            List of upcoming assignment dictionaries.
        """
        student_id = self.get_student_id(student_name)
        if not student_id:
            return []

        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT
                    assignment_name,
                    course_name,
                    teacher_name,
                    category,
                    due_date,
                    status
                FROM assignments
                WHERE student_id = ?
                  AND due_date >= date('now')
                  AND due_date <= date('now', '+' || ? || ' days')
                  AND status != 'Collected'
                ORDER BY due_date ASC
                """,
                (student_id, days),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_course_details(self, student_name: str, course_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific course.

        Args:
            student_name: Student name to search for.
            course_name: Course name to search for (partial match).

        Returns:
            Course details dictionary, or error dict if not found.
        """
        student_id = self.get_student_id(student_name)
        if not student_id:
            return {"error": f"Student '{student_name}' not found"}

        # Sanitize and escape course name for LIKE query
        course_name = sanitize_student_name(course_name)  # Reuse name sanitization
        escaped_course = escape_like_pattern(course_name)

        with get_db(self.db_path) as conn:
            # Get course info
            cursor = conn.execute(
                """
                SELECT
                    c.course_name,
                    c.teacher_name,
                    c.teacher_email,
                    c.room,
                    c.term
                FROM courses c
                WHERE c.student_id = ? AND LOWER(c.course_name) LIKE LOWER(?) ESCAPE '\\'
                LIMIT 1
                """,
                (student_id, f"%{escaped_course}%"),
            )
            course = cursor.fetchone()

            if not course:
                return {"error": f"Course '{course_name}' not found"}

            course_data = dict(course)

            # Get grade for this course
            cursor = conn.execute(
                """
                SELECT g.letter_grade, g.percent, g.term
                FROM grades g
                JOIN courses c ON c.id = g.course_id
                WHERE c.student_id = ? AND LOWER(c.course_name) LIKE LOWER(?) ESCAPE '\\'
                ORDER BY g.recorded_at DESC
                LIMIT 1
                """,
                (student_id, f"%{escaped_course}%"),
            )
            grade = cursor.fetchone()
            if grade:
                course_data["letter_grade"] = grade["letter_grade"]
                course_data["percent"] = grade["percent"]

            # Get missing assignments for this course
            cursor = conn.execute(
                """
                SELECT assignment_name, due_date, category
                FROM assignments
                WHERE student_id = ?
                  AND LOWER(course_name) LIKE LOWER(?) ESCAPE '\\'
                  AND status = 'Missing'
                ORDER BY due_date DESC
                """,
                (student_id, f"%{escaped_course}%"),
            )
            course_data["missing_assignments"] = [dict(row) for row in cursor.fetchall()]

            # Get recent assignments
            cursor = conn.execute(
                """
                SELECT assignment_name, due_date, score, max_score, status, category
                FROM assignments
                WHERE student_id = ?
                  AND LOWER(course_name) LIKE LOWER(?) ESCAPE '\\'
                ORDER BY due_date DESC
                LIMIT 5
                """,
                (student_id, f"%{escaped_course}%"),
            )
            course_data["recent_assignments"] = [dict(row) for row in cursor.fetchall()]

            return course_data

    def get_all_courses(self, student_name: str) -> List[Dict[str, Any]]:
        """Get list of all courses for a student.

        Args:
            student_name: Student name to search for.

        Returns:
            List of course dictionaries.
        """
        student_id = self.get_student_id(student_name)
        if not student_id:
            return []

        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT DISTINCT
                    course_name,
                    teacher_name,
                    teacher_email,
                    room
                FROM courses
                WHERE student_id = ?
                ORDER BY course_name
                """,
                (student_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_assignment_stats(self, student_name: str) -> Dict[str, Any]:
        """Get assignment completion statistics.

        Args:
            student_name: Student name to search for.

        Returns:
            Assignment statistics dictionary, or error dict if not found.
        """
        student_id = self.get_student_id(student_name)
        if not student_id:
            return {"error": f"Student '{student_name}' not found"}

        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'Collected' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'Missing' THEN 1 ELSE 0 END) as missing,
                    SUM(CASE WHEN status = 'Late' THEN 1 ELSE 0 END) as late
                FROM assignments
                WHERE student_id = ?
                """,
                (student_id,),
            )
            result = cursor.fetchone()

            if result:
                total = result["total"] or 0
                completed = result["completed"] or 0
                return {
                    "total": total,
                    "completed": completed,
                    "missing": result["missing"] or 0,
                    "late": result["late"] or 0,
                    "completion_rate": round(100 * completed / total, 1) if total > 0 else 0,
                }
            return {"total": 0, "completed": 0, "missing": 0, "late": 0, "completion_rate": 0}

    def run_custom_query(self, sql: str) -> List[Dict[str, Any]]:
        """Run a custom read-only SQL query.

        Security: Only SELECT queries are allowed. Dangerous keywords are blocked.

        Args:
            sql: SQL SELECT query to execute.

        Returns:
            List of result dictionaries, or error dict if query is invalid.
        """
        sql_lower = sql.strip().lower()

        # Only allow SELECT
        if not sql_lower.startswith("select"):
            return [{"error": "Only SELECT queries are allowed"}]

        # Block dangerous keywords
        dangerous = [
            "insert",
            "update",
            "delete",
            "drop",
            "alter",
            "create",
            "truncate",
            "attach",
            "detach",
            "pragma",
        ]
        for keyword in dangerous:
            if keyword in sql_lower:
                return [{"error": f"Query contains forbidden keyword: {keyword}"}]

        with get_db(self.db_path) as conn:
            try:
                cursor = conn.execute(sql)
                return [dict(row) for row in cursor.fetchall()]
            except Exception as e:
                return [{"error": str(e)}]


# Singleton adapter instance
_adapter: Optional[RepositoryAdapter] = None


def get_adapter(db_path: Optional[Path] = None) -> RepositoryAdapter:
    """Get or create the singleton RepositoryAdapter instance.

    Args:
        db_path: Optional database path. If provided and different from
                 the current instance, creates a new RepositoryAdapter.

    Returns:
        The RepositoryAdapter singleton instance.
    """
    global _adapter
    if _adapter is None or (db_path and Path(db_path) != _adapter.db_path):
        _adapter = RepositoryAdapter(db_path)
    return _adapter
