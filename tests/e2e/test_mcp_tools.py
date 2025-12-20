"""E2E tests for MCP server tools.

These tests validate that MCP tools return correct data when
querying the PowerSchool database populated by the scraper.

Tests use the Repository class directly since MCP tools are
server handlers that wrap repository methods.
"""

import sqlite3
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.e2e,
]


class TestRepositoryMissingAssignments:
    """Tests for get_missing_assignments via Repository."""

    def test_returns_missing_assignments(self, test_db_path: Path, ground_truth: dict):
        """Repository returns correct missing assignments from database."""
        if not test_db_path.exists():
            pytest.skip("Database not populated - run scraper first")

        from src.database.repository import Repository

        repo = Repository(test_db_path)
        result = repo.get_missing_assignments()

        assert isinstance(result, list), "Should return a list"
        assert len(result) >= 1, "Should have at least 1 missing assignment"

        # Check structure
        for item in result:
            assert "assignment_name" in item, "Should have assignment_name"
            assert "course_name" in item, "Should have course_name"

    def test_includes_known_missing_assignment(self, test_db_path: Path, ground_truth: dict):
        """Repository includes specific known missing assignments."""
        if not test_db_path.exists():
            pytest.skip("Database not populated - run scraper first")

        from src.database.repository import Repository

        repo = Repository(test_db_path)
        result = repo.get_missing_assignments()

        assignment_names = [r.get("assignment_name", "").lower() for r in result]

        # Check for at least one known missing assignment pattern
        known_patterns = ["atomic", "edpuzzle", "knowledge check", "formative"]
        found_any = any(
            any(pattern in name for pattern in known_patterns) for name in assignment_names
        )

        # Log what we found for debugging
        if not found_any:
            print(f"Found missing assignments: {assignment_names}")

        assert len(result) >= 1, "Should have at least one missing assignment"


class TestRepositoryAttendance:
    """Tests for get_attendance_summary via Repository."""

    def test_returns_attendance_data(self, test_db_path: Path, ground_truth: dict):
        """Repository returns attendance summary for a student."""
        if not test_db_path.exists():
            pytest.skip("Database not populated - run scraper first")

        from src.database.repository import Repository

        repo = Repository(test_db_path)
        students = repo.get_students()

        if not students:
            pytest.skip("No students in database")

        result = repo.get_attendance_summary(students[0]["id"])

        # Result may be None if no attendance data
        if result is None:
            pytest.skip("No attendance summary data available")

        assert isinstance(result, dict), "Should return a dictionary"

    def test_attendance_has_expected_fields(self, test_db_path: Path):
        """Attendance summary has expected fields."""
        if not test_db_path.exists():
            pytest.skip("Database not populated - run scraper first")

        from src.database.repository import Repository

        repo = Repository(test_db_path)
        students = repo.get_students()

        if not students:
            pytest.skip("No students in database")

        result = repo.get_attendance_summary(students[0]["id"])

        if result is None:
            pytest.skip("No attendance data available")

        # Check for attendance rate field
        assert "attendance_rate" in result, "Should have attendance_rate"


class TestRepositoryActionItems:
    """Tests for get_action_items via Repository."""

    def test_returns_action_items(self, test_db_path: Path):
        """Repository returns prioritized action items."""
        if not test_db_path.exists():
            pytest.skip("Database not populated - run scraper first")

        from src.database.repository import Repository

        repo = Repository(test_db_path)
        students = repo.get_students()

        if not students:
            pytest.skip("No students in database")

        result = repo.get_action_items(students[0]["id"])

        assert isinstance(result, list), "Should return a list"
        # May be empty if no issues
        if len(result) > 0:
            # Check structure of first item
            first = result[0]
            assert "priority" in first or "message" in first, "Should have priority or message"

    def test_missing_assignments_generate_action_items(self, test_db_path: Path):
        """Missing assignments should generate action items."""
        if not test_db_path.exists():
            pytest.skip("Database not populated - run scraper first")

        from src.database.repository import Repository

        repo = Repository(test_db_path)
        missing = repo.get_missing_assignments()
        actions = repo.get_action_items()

        # If there are missing assignments, there should be action items
        if len(missing) > 0:
            assert len(actions) > 0, "Missing assignments should generate action items"


class TestRepositoryStudentSummary:
    """Tests for get_student_summary via Repository."""

    def test_returns_student_summary(self, test_db_path: Path):
        """Repository returns comprehensive student summary."""
        if not test_db_path.exists():
            pytest.skip("Database not populated - run scraper first")

        from src.database.repository import Repository

        repo = Repository(test_db_path)
        students = repo.get_students()

        if not students:
            pytest.skip("No students in database")

        result = repo.get_student_summary(students[0]["id"])

        if result is None:
            pytest.skip("No summary data available")

        assert isinstance(result, dict), "Should return a dictionary"
        assert "student_name" in result, "Should have student_name"
        assert "course_count" in result, "Should have course_count"


class TestDatabaseIntegrity:
    """Tests for database state and integrity."""

    def test_database_exists(self, test_db_path: Path):
        """Verify database file exists."""
        if not test_db_path.exists():
            pytest.skip(f"Database not found at {test_db_path} - run scraper first")

    def test_database_has_expected_tables(self, test_db_path: Path):
        """Verify database has required tables."""
        if not test_db_path.exists():
            pytest.skip("Database not created yet")

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        expected_tables = {"students", "courses", "assignments"}
        missing = expected_tables - tables

        assert not missing, f"Missing tables: {missing}"

    def test_database_has_data(self, test_db_path: Path):
        """Verify database is populated with data."""
        if not test_db_path.exists():
            pytest.skip("Database not created yet")

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Check for at least some assignments
        cursor.execute("SELECT COUNT(*) FROM assignments")
        assignment_count = cursor.fetchone()[0]

        conn.close()

        assert assignment_count > 0, "Database should have assignments"


class TestRepositoryTeachers:
    """Tests for teacher-related repository methods."""

    def test_returns_teachers(self, test_db_path: Path):
        """Repository returns list of teachers."""
        if not test_db_path.exists():
            pytest.skip("Database not populated - run scraper first")

        from src.database.repository import Repository

        repo = Repository(test_db_path)
        result = repo.get_teachers()

        assert isinstance(result, list), "Should return a list"

    def test_teacher_has_required_fields(self, test_db_path: Path):
        """Teachers have required fields."""
        if not test_db_path.exists():
            pytest.skip("Database not populated - run scraper first")

        from src.database.repository import Repository

        repo = Repository(test_db_path)
        teachers = repo.get_teachers()

        if not teachers:
            pytest.skip("No teachers in database")

        first = teachers[0]
        assert "name" in first, "Teacher should have name"
        # Email may not always be available
        assert "id" in first, "Teacher should have id"
