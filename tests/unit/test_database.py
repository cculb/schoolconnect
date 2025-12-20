"""Unit tests for database operations.

These tests use temporary in-memory databases and don't
require external dependencies.
"""

import sqlite3
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


class TestDatabaseSchema:
    """Tests for database schema creation."""

    def test_create_schema(self, temp_db: Path):
        """Schema creation creates expected tables."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

        expected = {"students", "courses", "assignments", "attendance_summary"}
        assert expected.issubset(tables), f"Missing tables: {expected - tables}"

    def test_students_table_columns(self, temp_db: Path):
        """Students table has required columns."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(students)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        required = {"student_id", "name"}
        assert required.issubset(columns)

    def test_assignments_foreign_key(self, temp_db: Path):
        """Assignments table references courses."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(assignments)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        assert "course_id" in columns


class TestRepositorySave:
    """Tests for repository save operations."""

    def test_save_student(self, temp_db: Path):
        """Repository can save student data."""
        try:
            from src.database.repository import PowerSchoolRepository
        except ImportError:
            pytest.skip("Repository not implemented")

        repo = PowerSchoolRepository(temp_db)

        student = {
            "student_id": "12345",
            "name": "Test Student",
            "grade_level": 6,
        }
        repo.save_student(student)

        # Verify saved
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM students WHERE student_id = ?", ("12345",))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == "Test Student"

    def test_save_assignment(self, temp_db: Path):
        """Repository can save assignment data."""
        try:
            from src.database.repository import PowerSchoolRepository
        except ImportError:
            pytest.skip("Repository not implemented")

        repo = PowerSchoolRepository(temp_db)

        assignment = {
            "assignment_id": "a1",
            "course_id": "c1",
            "assignment_name": "Test Assignment",
            "status": "Missing",
            "due_date": "2024-12-15",
        }
        repo.save_assignment(assignment)

        # Verify saved
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT assignment_name, status FROM assignments WHERE assignment_id = ?", ("a1",)
        )
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == "Test Assignment"
        assert row[1] == "Missing"

    def test_save_attendance_summary(self, temp_db: Path):
        """Repository can save attendance summary."""
        try:
            from src.database.repository import PowerSchoolRepository
        except ImportError:
            pytest.skip("Repository not implemented")

        repo = PowerSchoolRepository(temp_db)

        attendance = {
            "student_id": "12345",
            "term": "YTD",
            "days_present": 70,
            "days_absent": 9,
            "attendance_rate": 88.6,
        }
        repo.save_attendance_summary(attendance)

        # Verify saved
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT attendance_rate FROM attendance_summary WHERE student_id = ?", ("12345",)
        )
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert abs(row[0] - 88.6) < 0.1


class TestRepositoryQuery:
    """Tests for repository query operations."""

    def test_get_missing_assignments(self, temp_db: Path):
        """Repository can query missing assignments."""
        try:
            from src.database.repository import PowerSchoolRepository
        except ImportError:
            pytest.skip("Repository not implemented")

        # Insert test data
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO assignments (assignment_id, course_id, assignment_name, status) "
            "VALUES (?, ?, ?, ?)",
            ("a1", "c1", "Missing Test", "Missing"),
        )
        cursor.execute(
            "INSERT INTO assignments (assignment_id, course_id, assignment_name, status) "
            "VALUES (?, ?, ?, ?)",
            ("a2", "c1", "Graded Test", "Graded"),
        )
        conn.commit()
        conn.close()

        repo = PowerSchoolRepository(temp_db)
        missing = repo.get_missing_assignments()

        assert len(missing) == 1
        assert missing[0]["assignment_name"] == "Missing Test"

    def test_get_attendance_rate(self, temp_db: Path):
        """Repository can query attendance rate."""
        try:
            from src.database.repository import PowerSchoolRepository
        except ImportError:
            pytest.skip("Repository not implemented")

        # Insert test data
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO attendance_summary "
            "(student_id, term, days_present, days_absent, attendance_rate) "
            "VALUES (?, ?, ?, ?, ?)",
            ("12345", "YTD", 70, 9, 88.6),
        )
        conn.commit()
        conn.close()

        repo = PowerSchoolRepository(temp_db)
        rate = repo.get_attendance_rate()

        assert rate is not None
        assert abs(rate - 88.6) < 0.1

    def test_get_courses(self, temp_db: Path):
        """Repository can query course list."""
        try:
            from src.database.repository import PowerSchoolRepository
        except ImportError:
            pytest.skip("Repository not implemented")

        # Insert test data
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO courses (course_id, course_name, teacher_name) VALUES (?, ?, ?)",
            ("c1", "Math 6", "Smith, John"),
        )
        cursor.execute(
            "INSERT INTO courses (course_id, course_name, teacher_name) VALUES (?, ?, ?)",
            ("c2", "English 6", "Jones, Mary"),
        )
        conn.commit()
        conn.close()

        repo = PowerSchoolRepository(temp_db)
        courses = repo.get_courses()

        assert len(courses) == 2


class TestDataIntegrity:
    """Tests for data integrity constraints."""

    def test_duplicate_assignment_handling(self, temp_db: Path):
        """Repository handles duplicate assignment IDs."""
        try:
            from src.database.repository import PowerSchoolRepository
        except ImportError:
            pytest.skip("Repository not implemented")

        repo = PowerSchoolRepository(temp_db)

        assignment = {
            "assignment_id": "a1",
            "course_id": "c1",
            "assignment_name": "Original",
            "status": "Missing",
        }
        repo.save_assignment(assignment)

        # Save again with updated name - should update or handle gracefully
        assignment["assignment_name"] = "Updated"
        repo.save_assignment(assignment)

        # Should not have duplicates
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM assignments WHERE assignment_id = ?", ("a1",))
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 1

    def test_null_handling(self, temp_db: Path):
        """Repository handles NULL values correctly."""
        try:
            from src.database.repository import PowerSchoolRepository
        except ImportError:
            pytest.skip("Repository not implemented")

        repo = PowerSchoolRepository(temp_db)

        # Assignment with minimal data
        assignment = {
            "assignment_id": "a1",
            "course_id": "c1",
            "assignment_name": "Test",
            # Missing: due_date, score, etc.
        }
        repo.save_assignment(assignment)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT due_date FROM assignments WHERE assignment_id = ?", ("a1",))
        row = cursor.fetchone()
        conn.close()

        # Should handle None gracefully
        assert row is not None
