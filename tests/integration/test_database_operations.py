"""Integration tests for database operations.

These tests verify database operations work correctly with
realistic data volumes and scenarios.
"""

import sqlite3
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


class TestBulkOperations:
    """Tests for bulk database operations."""

    def test_bulk_insert_assignments(self, temp_db: Path):
        """Bulk insert many assignments efficiently."""
        try:
            from src.database.repository import PowerSchoolRepository
        except ImportError:
            pytest.skip("Repository not implemented")

        repo = PowerSchoolRepository(temp_db)

        # Create 100 assignments
        assignments = [
            {
                "assignment_id": f"a{i}",
                "course_id": f"c{i % 8}",
                "assignment_name": f"Assignment {i}",
                "status": "Missing" if i % 10 == 0 else "Graded",
                "due_date": f"2024-12-{(i % 28) + 1:02d}",
            }
            for i in range(100)
        ]

        repo.save_assignments(assignments)

        # Verify all inserted
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM assignments")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 100

    def test_bulk_update_assignments(self, temp_db: Path):
        """Bulk update existing assignments."""
        try:
            from src.database.repository import PowerSchoolRepository
        except ImportError:
            pytest.skip("Repository not implemented")

        repo = PowerSchoolRepository(temp_db)

        # Insert initial assignments
        assignments = [
            {
                "assignment_id": f"a{i}",
                "course_id": "c1",
                "assignment_name": f"Assignment {i}",
                "status": "Missing",
            }
            for i in range(10)
        ]
        repo.save_assignments(assignments)

        # Update to graded
        for a in assignments:
            a["status"] = "Graded"
        repo.save_assignments(assignments)

        # Verify updates
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM assignments WHERE status = 'Graded'")
        graded_count = cursor.fetchone()[0]
        conn.close()

        assert graded_count == 10


class TestQueryPerformance:
    """Tests for query performance with realistic data."""

    def test_missing_assignments_query_performance(self, temp_db: Path):
        """Missing assignments query performs well with many records."""
        import time

        try:
            from src.database.repository import PowerSchoolRepository
        except ImportError:
            pytest.skip("Repository not implemented")

        repo = PowerSchoolRepository(temp_db)

        # Insert 500 assignments, 50 missing
        assignments = [
            {
                "assignment_id": f"a{i}",
                "course_id": f"c{i % 8}",
                "assignment_name": f"Assignment {i}",
                "status": "Missing" if i % 10 == 0 else "Graded",
            }
            for i in range(500)
        ]
        repo.save_assignments(assignments)

        # Time the query
        start = time.time()
        missing = repo.get_missing_assignments()
        elapsed = time.time() - start

        assert len(missing) == 50
        assert elapsed < 0.1, f"Query took too long: {elapsed:.3f}s"

    def test_course_grades_query(self, temp_db: Path):
        """Course grades aggregation query works correctly."""
        try:
            from src.database.repository import PowerSchoolRepository
        except ImportError:
            pytest.skip("Repository not implemented")

        # Setup courses with grades
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        for i in range(8):
            cursor.execute(
                "INSERT INTO courses (course_id, course_name, grade_percent) VALUES (?, ?, ?)",
                (f"c{i}", f"Course {i}", 85.0 + i),
            )
        conn.commit()
        conn.close()

        repo = PowerSchoolRepository(temp_db)
        courses = repo.get_courses_with_grades()

        assert len(courses) == 8
        assert all(c.get("grade_percent") is not None for c in courses)


class TestDataConsistency:
    """Tests for data consistency across operations."""

    def test_course_assignment_relationship(self, temp_db: Path):
        """Assignments maintain relationship with courses."""
        try:
            from src.database.repository import PowerSchoolRepository
        except ImportError:
            pytest.skip("Repository not implemented")

        repo = PowerSchoolRepository(temp_db)

        # Insert course
        course = {
            "course_id": "c1",
            "course_name": "Math 6",
            "teacher_name": "Smith",
        }
        repo.save_course(course)

        # Insert assignments for course
        assignments = [
            {
                "assignment_id": f"a{i}",
                "course_id": "c1",
                "assignment_name": f"Math Assignment {i}",
                "status": "Graded",
            }
            for i in range(5)
        ]
        repo.save_assignments(assignments)

        # Query assignments with course info
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.assignment_name, c.course_name, c.teacher_name
            FROM assignments a
            JOIN courses c ON a.course_id = c.course_id
            WHERE a.course_id = 'c1'
        """)
        results = cursor.fetchall()
        conn.close()

        assert len(results) == 5
        assert all(r[1] == "Math 6" for r in results)

    def test_attendance_student_relationship(self, temp_db: Path):
        """Attendance records maintain relationship with students."""
        try:
            from src.database.repository import PowerSchoolRepository
        except ImportError:
            pytest.skip("Repository not implemented")

        repo = PowerSchoolRepository(temp_db)

        # Insert student
        student = {
            "student_id": "s1",
            "name": "Test Student",
            "grade_level": 6,
        }
        repo.save_student(student)

        # Insert attendance
        attendance = {
            "student_id": "s1",
            "term": "YTD",
            "days_present": 70,
            "days_absent": 9,
            "attendance_rate": 88.6,
        }
        repo.save_attendance_summary(attendance)

        # Query with join
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.name, a.attendance_rate
            FROM students s
            JOIN attendance_summary a ON s.student_id = a.student_id
            WHERE s.student_id = 's1'
        """)
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == "Test Student"
        assert abs(result[1] - 88.6) < 0.1


class TestMCPToolIntegration:
    """Tests for MCP tool integration with database."""

    def test_tools_use_correct_database(self, temp_db: Path):
        """MCP tools query the correct database."""
        try:
            from src.database.repository import PowerSchoolRepository
        except ImportError:
            pytest.skip("Repository not implemented")

        # Populate with known data
        repo = PowerSchoolRepository(temp_db)

        repo.save_assignment(
            {
                "assignment_id": "test1",
                "course_id": "c1",
                "assignment_name": "Unique Test Assignment",
                "status": "Missing",
            }
        )

        # Query through repository
        missing = repo.get_missing_assignments()

        assert len(missing) == 1
        assert missing[0]["assignment_name"] == "Unique Test Assignment"

    def test_concurrent_access(self, temp_db: Path):
        """Database handles concurrent access correctly."""
        import threading
        import time

        try:
            from src.database.repository import PowerSchoolRepository
        except ImportError:
            pytest.skip("Repository not implemented")

        errors = []

        def writer():
            try:
                repo = PowerSchoolRepository(temp_db)
                for i in range(10):
                    repo.save_assignment(
                        {
                            "assignment_id": f"w{threading.current_thread().name}_{i}",
                            "course_id": "c1",
                            "assignment_name": f"Assignment {i}",
                            "status": "Graded",
                        }
                    )
                    time.sleep(0.01)
            except Exception as e:
                errors.append(str(e))

        def reader():
            try:
                repo = PowerSchoolRepository(temp_db)
                for _ in range(10):
                    repo.get_missing_assignments()
                    time.sleep(0.01)
            except Exception as e:
                errors.append(str(e))

        threads = [
            threading.Thread(target=writer, name="w1"),
            threading.Thread(target=writer, name="w2"),
            threading.Thread(target=reader, name="r1"),
            threading.Thread(target=reader, name="r2"),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Concurrent access errors: {errors}"
