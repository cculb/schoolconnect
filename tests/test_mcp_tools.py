"""Tests for MCP tools."""

import pytest

from src.database.connection import Database
from src.database.repository import Repository


class TestStudentTools:
    """Tests for student-related MCP tools."""

    @pytest.mark.asyncio
    async def test_list_students(self, populated_db):
        """Test listing students."""
        async with Database(populated_db) as db:
            repo = Repository(db)
            students = await repo.list_students()

            assert len(students) == 1
            assert students[0]["first_name"] == "Delilah"

    @pytest.mark.asyncio
    async def test_get_student_summary(self, populated_db):
        """Test getting student summary."""
        async with Database(populated_db) as db:
            repo = Repository(db)

            summary = await repo.get_student_summary("STU001")
            assert summary is not None
            assert summary["student_name"] == "Delilah Culbreth"
            assert summary["course_count"] == 3
            assert summary["missing_assignments"] == 2


class TestGradeTools:
    """Tests for grade-related MCP tools."""

    @pytest.mark.asyncio
    async def test_get_current_grades(self, populated_db):
        """Test getting current grades."""
        async with Database(populated_db) as db:
            repo = Repository(db)

            grades = await repo.get_current_grades("STU001")
            assert len(grades) == 3

            # Check that grades have expected fields
            for grade in grades:
                assert "course_name" in grade
                assert "letter_grade" in grade

    @pytest.mark.asyncio
    async def test_get_grade_history(self, populated_db):
        """Test getting grade history."""
        async with Database(populated_db) as db:
            repo = Repository(db)

            history = await repo.get_grade_history("STU001")
            assert len(history) == 3

    @pytest.mark.asyncio
    async def test_get_grade_history_by_course(self, populated_db):
        """Test getting grade history filtered by course."""
        async with Database(populated_db) as db:
            repo = Repository(db)

            history = await repo.get_grade_history("STU001", "CRS001")
            assert len(history) == 1
            assert "Social Studies" in history[0]["course_name"]

    @pytest.mark.asyncio
    async def test_calculate_gpa(self, populated_db):
        """Test GPA calculation."""
        async with Database(populated_db) as db:
            repo = Repository(db)

            gpa = await repo.calculate_gpa("STU001")
            assert gpa is not None
            assert gpa["gpa"] is not None
            # (2 + 3 + 3) / 3 = 2.67
            assert round(gpa["gpa"], 2) == 2.67

    @pytest.mark.asyncio
    async def test_calculate_gpa_by_term(self, populated_db):
        """Test GPA calculation for specific term."""
        async with Database(populated_db) as db:
            repo = Repository(db)

            gpa = await repo.calculate_gpa("STU001", "Q1")
            assert gpa is not None
            assert gpa["term"] == "Q1"

    @pytest.mark.asyncio
    async def test_get_grade_trends(self, populated_db):
        """Test getting grade trends."""
        async with Database(populated_db) as db:
            repo = Repository(db)

            trends = await repo.get_grade_trends("STU001")
            assert len(trends) == 3


class TestAssignmentTools:
    """Tests for assignment-related MCP tools."""

    @pytest.mark.asyncio
    async def test_get_missing_assignments_for_student(self, populated_db):
        """Test getting missing assignments for a specific student."""
        async with Database(populated_db) as db:
            repo = Repository(db)

            missing = await repo.get_missing_assignments("STU001")
            assert len(missing) == 2

            names = [a["assignment_name"] for a in missing]
            assert "Atomic Structure Knowledge Check" in names

    @pytest.mark.asyncio
    async def test_get_missing_assignments_all(self, populated_db):
        """Test getting all missing assignments."""
        async with Database(populated_db) as db:
            repo = Repository(db)

            missing = await repo.get_missing_assignments()
            assert len(missing) == 2

    @pytest.mark.asyncio
    async def test_get_assignment_completion_rates(self, populated_db):
        """Test getting completion rates."""
        async with Database(populated_db) as db:
            repo = Repository(db)

            rates = await repo.get_assignment_completion_rates("STU001")

            # We have 3 assignments across 3 courses
            assert len(rates) >= 2  # At least courses with assignments

            # Find Science course (has 1 missing assignment)
            science_rate = next(
                (r for r in rates if "Science" in r["course_name"]), None
            )
            if science_rate:
                assert science_rate["missing"] == 1


class TestAttendanceTools:
    """Tests for attendance-related MCP tools."""

    @pytest.mark.asyncio
    async def test_get_attendance_summary(self, populated_db):
        """Test getting attendance summary."""
        async with Database(populated_db) as db:
            repo = Repository(db)

            summary = await repo.get_attendance_summary("STU001")
            assert summary is not None
            assert summary["attendance_rate"] == 88.60
            assert summary["days_absent"] == 9
            assert summary["days_absent_excused"] == 9
            assert summary["days_absent_unexcused"] == 0
            assert summary["tardies"] == 2

    @pytest.mark.asyncio
    async def test_get_attendance_alerts(self, populated_db):
        """Test getting attendance alerts."""
        async with Database(populated_db) as db:
            repo = Repository(db)

            alerts = await repo.get_attendance_alerts()
            assert len(alerts) == 1

            alert = alerts[0]
            assert alert["student_name"] == "Delilah Culbreth"
            assert alert["alert_level"] == "Critical"  # 88.6% < 90%


class TestInsightTools:
    """Tests for insight generation tools."""

    @pytest.mark.asyncio
    async def test_query_for_weekly_report_data(self, populated_db):
        """Test that we can gather data needed for weekly report."""
        async with Database(populated_db) as db:
            repo = Repository(db)

            # Get all the data a weekly report would need
            student = await repo.get_student_by_name("Delilah")
            assert student is not None

            grades = await repo.get_current_grades(student["student_id"])
            assert len(grades) == 3

            missing = await repo.get_missing_assignments(student["student_id"])
            assert len(missing) == 2

            attendance = await repo.get_attendance_summary(student["student_id"])
            assert attendance is not None

            gpa = await repo.calculate_gpa(student["student_id"])
            assert gpa is not None

    @pytest.mark.asyncio
    async def test_custom_query_functionality(self, populated_db):
        """Test custom query execution."""
        async with Database(populated_db) as db:
            repo = Repository(db)

            # Test a valid query
            result = await repo.run_custom_query(
                "SELECT student_name, missing_assignments FROM v_student_summary"
            )
            assert len(result) == 1
            assert result[0]["missing_assignments"] == 2
