"""Database query functions for SchoolPulse.

This module provides the public API for querying student data.
It delegates to RepositoryAdapter which handles connection pooling,
input sanitization, and parameterized queries.

Addresses:
- CRIT-3: Uses RepositoryAdapter (Repository pattern) instead of direct SQL
- CRIT-4: Input sanitization via RepositoryAdapter (LIKE pattern escaping)
- CRIT-5: Connection pooling via RepositoryAdapter's get_db() context manager
"""

from pathlib import Path
from typing import Optional

from repository_adapter import RepositoryAdapter


def _get_adapter(db_path: str) -> RepositoryAdapter:
    """Get a RepositoryAdapter instance for the given database path.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        RepositoryAdapter instance.
    """
    return RepositoryAdapter(Path(db_path))


def get_student_id(db_path: str, student_name: str) -> Optional[int]:
    """Get student ID from name (partial match on first name).

    Args:
        db_path: Path to the database file.
        student_name: Student name to search for (partial match).

    Returns:
        Student database ID if found, None otherwise.
    """
    adapter = _get_adapter(db_path)
    return adapter.get_student_id(student_name)


def get_student_summary(db_path: str, student_name: str) -> dict:
    """Get overall summary for a student.

    Args:
        db_path: Path to the database file.
        student_name: Student name to search for.

    Returns:
        Dictionary with student summary data including:
        - student_id: Database ID
        - name: Full name
        - grade_level: Grade level
        - school_name: School name
        - missing_assignments: Count of missing assignments
        - attendance_rate: Attendance percentage
        - days_absent: Number of absences
        - tardies: Number of tardies
        - course_count: Number of enrolled courses
    """
    adapter = _get_adapter(db_path)
    return adapter.get_student_summary(student_name)


def get_missing_assignments(db_path: str, student_name: str) -> list[dict]:
    """Get list of missing assignments for a student.

    Args:
        db_path: Path to the database file.
        student_name: Student name to search for.

    Returns:
        List of missing assignment dictionaries with keys:
        - assignment_name
        - course_name
        - teacher_name
        - category
        - due_date
        - term
    """
    adapter = _get_adapter(db_path)
    return adapter.get_missing_assignments(student_name)


def get_current_grades(db_path: str, student_name: str) -> list[dict]:
    """Get current grades for all courses.

    Args:
        db_path: Path to the database file.
        student_name: Student name to search for.

    Returns:
        List of grade dictionaries with keys:
        - course_name
        - teacher_name
        - room
        - term
        - letter_grade
        - percent
    """
    adapter = _get_adapter(db_path)
    return adapter.get_current_grades(student_name)


def get_attendance_summary(db_path: str, student_name: str) -> dict:
    """Get attendance summary for a student.

    Args:
        db_path: Path to the database file.
        student_name: Student name to search for.

    Returns:
        Attendance summary dictionary with keys:
        - term
        - rate (attendance_rate)
        - days_present
        - days_absent
        - tardies
        - total_days
    """
    adapter = _get_adapter(db_path)
    return adapter.get_attendance_summary(student_name)


def get_upcoming_assignments(
    db_path: str, student_name: str, days: int = 7
) -> list[dict]:
    """Get assignments due in the next N days.

    Args:
        db_path: Path to the database file.
        student_name: Student name to search for.
        days: Number of days to look ahead (default 7).

    Returns:
        List of upcoming assignment dictionaries with keys:
        - assignment_name
        - course_name
        - teacher_name
        - category
        - due_date
        - status
    """
    adapter = _get_adapter(db_path)
    return adapter.get_upcoming_assignments(student_name, days)


def get_course_details(db_path: str, student_name: str, course_name: str) -> dict:
    """Get detailed information about a specific course.

    Args:
        db_path: Path to the database file.
        student_name: Student name to search for.
        course_name: Course name to search for (partial match).

    Returns:
        Course details dictionary with keys:
        - course_name
        - teacher_name
        - teacher_email
        - room
        - term
        - letter_grade (if available)
        - percent (if available)
        - missing_assignments: List of missing assignment dicts
        - recent_assignments: List of recent assignment dicts
    """
    adapter = _get_adapter(db_path)
    return adapter.get_course_details(student_name, course_name)


def run_custom_query(db_path: str, sql: str) -> list[dict]:
    """Run a custom read-only SQL query.

    Security: Only SELECT queries are allowed. Dangerous keywords are blocked.

    Args:
        db_path: Path to the database file.
        sql: SQL SELECT query to execute.

    Returns:
        List of result dictionaries, or error dict if query is invalid.
    """
    adapter = _get_adapter(db_path)
    return adapter.run_custom_query(sql)


def get_all_courses(db_path: str, student_name: str) -> list[dict]:
    """Get list of all courses for a student.

    Args:
        db_path: Path to the database file.
        student_name: Student name to search for.

    Returns:
        List of course dictionaries with keys:
        - course_name
        - teacher_name
        - teacher_email
        - room
    """
    adapter = _get_adapter(db_path)
    return adapter.get_all_courses(student_name)


def get_assignment_stats(db_path: str, student_name: str) -> dict:
    """Get assignment completion statistics.

    Args:
        db_path: Path to the database file.
        student_name: Student name to search for.

    Returns:
        Assignment statistics dictionary with keys:
        - total: Total number of assignments
        - completed: Number of completed assignments
        - missing: Number of missing assignments
        - late: Number of late assignments
        - completion_rate: Percentage of assignments completed
    """
    adapter = _get_adapter(db_path)
    return adapter.get_assignment_stats(student_name)
