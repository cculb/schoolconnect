"""Tests for database operations."""

from datetime import date

import pytest

from src.database.connection import Database
from src.database.models import Assignment, Course, Grade, Student
from src.database.repository import Repository, generate_id


class TestDatabaseConnection:
    """Tests for database connection management."""

    @pytest.mark.asyncio
    async def test_database_creates_file(self, tmp_path):
        """Test that database file is created."""
        db_path = tmp_path / "test.db"
        assert not db_path.exists()

        async with Database(db_path) as db:
            await db.init_schema()

        assert db_path.exists()

    @pytest.mark.asyncio
    async def test_schema_creates_tables(self, empty_db):
        """Test that schema creates all expected tables."""
        async with Database(empty_db) as db:
            tables = [
                "students",
                "courses",
                "grades",
                "assignments",
                "attendance_records",
                "attendance_summary",
                "teacher_comments",
                "scrape_history",
            ]
            for table in tables:
                exists = await db.table_exists(table)
                assert exists, f"Table {table} should exist"

    @pytest.mark.asyncio
    async def test_views_created(self, empty_db):
        """Test that views are created."""
        async with Database(empty_db) as db:
            # Views should be queryable
            result = await db.fetch_all("SELECT * FROM v_missing_assignments")
            assert isinstance(result, list)

            result = await db.fetch_all("SELECT * FROM v_current_grades")
            assert isinstance(result, list)


class TestRepository:
    """Tests for repository operations."""

    @pytest.mark.asyncio
    async def test_insert_and_get_student(self, empty_db):
        """Test inserting and retrieving a student."""
        async with Database(empty_db) as db:
            repo = Repository(db)

            student = Student(
                student_id="TEST001",
                first_name="Test",
                last_name="Student",
                grade_level=7,
                school_name="Test School",
            )
            await repo.insert_student(student)

            retrieved = await repo.get_student("TEST001")
            assert retrieved is not None
            assert retrieved["first_name"] == "Test"
            assert retrieved["last_name"] == "Student"

    @pytest.mark.asyncio
    async def test_get_student_by_name(self, populated_db):
        """Test finding student by name."""
        async with Database(populated_db) as db:
            repo = Repository(db)

            # Full name
            student = await repo.get_student_by_name("Delilah Culbreth")
            assert student is not None
            assert student["first_name"] == "Delilah"

            # Partial name
            student = await repo.get_student_by_name("Delilah")
            assert student is not None

            # Last name
            student = await repo.get_student_by_name("Culbreth")
            assert student is not None

    @pytest.mark.asyncio
    async def test_get_missing_assignments(self, populated_db):
        """Test retrieving missing assignments."""
        async with Database(populated_db) as db:
            repo = Repository(db)

            missing = await repo.get_missing_assignments("STU001")
            assert len(missing) == 2

            # Check assignment names
            names = [a["assignment_name"] for a in missing]
            assert "Atomic Structure Knowledge Check" in names
            assert "FORMATIVE - Edpuzzle on Autocracies" in names

    @pytest.mark.asyncio
    async def test_get_current_grades(self, populated_db):
        """Test retrieving current grades."""
        async with Database(populated_db) as db:
            repo = Repository(db)

            grades = await repo.get_current_grades("STU001")
            assert len(grades) == 3

    @pytest.mark.asyncio
    async def test_calculate_gpa(self, populated_db):
        """Test GPA calculation."""
        async with Database(populated_db) as db:
            repo = Repository(db)

            gpa = await repo.calculate_gpa("STU001")
            assert gpa is not None
            assert gpa["course_count"] == 3
            # (2 + 3 + 3) / 3 = 2.67
            assert round(gpa["gpa"], 2) == 2.67

    @pytest.mark.asyncio
    async def test_get_attendance_summary(self, populated_db):
        """Test retrieving attendance summary."""
        async with Database(populated_db) as db:
            repo = Repository(db)

            summary = await repo.get_attendance_summary("STU001")
            assert summary is not None
            assert summary["attendance_rate"] == 88.60
            assert summary["days_absent"] == 9
            assert summary["tardies"] == 2

    @pytest.mark.asyncio
    async def test_custom_query_select_allowed(self, populated_db):
        """Test that SELECT queries work."""
        async with Database(populated_db) as db:
            repo = Repository(db)

            result = await repo.run_custom_query("SELECT COUNT(*) as count FROM students")
            assert result[0]["count"] == 1

    @pytest.mark.asyncio
    async def test_custom_query_insert_blocked(self, populated_db):
        """Test that INSERT queries are blocked."""
        async with Database(populated_db) as db:
            repo = Repository(db)

            with pytest.raises(ValueError, match="SELECT"):
                await repo.run_custom_query(
                    "INSERT INTO students VALUES ('X', 'Test', 'User', 5, 'School', 'X')"
                )

    @pytest.mark.asyncio
    async def test_custom_query_delete_blocked(self, populated_db):
        """Test that DELETE queries are blocked."""
        async with Database(populated_db) as db:
            repo = Repository(db)

            with pytest.raises(ValueError, match="SELECT"):
                await repo.run_custom_query("DELETE FROM students")


class TestViews:
    """Tests for database views."""

    @pytest.mark.asyncio
    async def test_missing_assignments_view(self, populated_db):
        """Test v_missing_assignments view."""
        async with Database(populated_db) as db:
            result = await db.fetch_all("SELECT * FROM v_missing_assignments")

            assert len(result) == 2
            for row in result:
                assert row["student_name"] == "Delilah Culbreth"
                assert row["days_overdue"] is not None
                assert row["assignment_name"] is not None

    @pytest.mark.asyncio
    async def test_student_summary_view(self, populated_db):
        """Test v_student_summary view."""
        async with Database(populated_db) as db:
            result = await db.fetch_all(
                "SELECT * FROM v_student_summary WHERE student_id = 'STU001'"
            )

            assert len(result) == 1
            summary = result[0]
            assert summary["student_name"] == "Delilah Culbreth"
            assert summary["course_count"] == 3
            assert summary["missing_assignments"] == 2

    @pytest.mark.asyncio
    async def test_attendance_alerts_view(self, populated_db):
        """Test v_attendance_alerts view."""
        async with Database(populated_db) as db:
            result = await db.fetch_all("SELECT * FROM v_attendance_alerts")

            assert len(result) == 1
            alert = result[0]
            assert alert["alert_level"] == "Critical"  # 88.6% < 90%
