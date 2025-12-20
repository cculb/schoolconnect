"""Unit tests for HTML parsers.

These tests use static HTML fixtures and don't require
external dependencies or network access.
"""

import pytest

pytestmark = pytest.mark.unit


class TestAssignmentParser:
    """Tests for assignment HTML parsing."""

    def test_parse_assignment_table(self, sample_assignment_html: str):
        """Parser extracts assignments from HTML table."""
        try:
            from src.scraper.parsers import parse_assignments
        except ImportError:
            pytest.skip("Parser not implemented")

        assignments = parse_assignments(sample_assignment_html)

        assert isinstance(assignments, list)
        assert len(assignments) >= 2

    def test_parse_missing_status(self, sample_assignment_html: str):
        """Parser correctly identifies missing assignments."""
        try:
            from src.scraper.parsers import parse_assignments
        except ImportError:
            pytest.skip("Parser not implemented")

        assignments = parse_assignments(sample_assignment_html)

        missing = [a for a in assignments if a.get("status") == "Missing"]
        assert len(missing) >= 1

    def test_parse_score_format(self, sample_assignment_html: str):
        """Parser handles various score formats."""
        try:
            from src.scraper.parsers import parse_assignments
        except ImportError:
            pytest.skip("Parser not implemented")

        assignments = parse_assignments(sample_assignment_html)

        # Find graded assignment
        graded = [a for a in assignments if a.get("status") == "Graded"]
        if graded:
            score = graded[0].get("score")
            assert score is not None

    def test_parse_empty_html(self):
        """Parser handles empty or minimal HTML gracefully."""
        try:
            from src.scraper.parsers import parse_assignments
        except ImportError:
            pytest.skip("Parser not implemented")

        result = parse_assignments("")
        assert result == [] or result is None

        result = parse_assignments("<html></html>")
        assert result == [] or result is None


class TestAttendanceParser:
    """Tests for attendance HTML parsing."""

    def test_parse_attendance_summary(self, sample_attendance_html: str):
        """Parser extracts attendance summary data."""
        try:
            from src.scraper.parsers import parse_attendance
        except ImportError:
            pytest.skip("Parser not implemented")

        attendance = parse_attendance(sample_attendance_html)

        assert isinstance(attendance, dict)
        assert "rate" in attendance or "attendance_rate" in attendance

    def test_parse_attendance_rate_value(self, sample_attendance_html: str):
        """Parser extracts correct attendance rate."""
        try:
            from src.scraper.parsers import parse_attendance
        except ImportError:
            pytest.skip("Parser not implemented")

        attendance = parse_attendance(sample_attendance_html)

        rate = attendance.get("rate") or attendance.get("attendance_rate")
        # Should be approximately 88.6 from the sample
        assert 88 <= rate <= 89

    def test_parse_days_values(self, sample_attendance_html: str):
        """Parser extracts days present/absent values."""
        try:
            from src.scraper.parsers import parse_attendance
        except ImportError:
            pytest.skip("Parser not implemented")

        attendance = parse_attendance(sample_attendance_html)

        days_present = attendance.get("days_present")
        days_absent = attendance.get("days_absent")

        if days_present is not None:
            assert days_present == 70
        if days_absent is not None:
            assert days_absent == 9


class TestScheduleParser:
    """Tests for schedule/course HTML parsing."""

    def test_parse_course_list(self):
        """Parser extracts course information."""
        sample_html = """
        <table class="schedule">
            <tr>
                <td class="period">1</td>
                <td class="course">Math 6</td>
                <td class="teacher">Smith, John</td>
                <td class="room">101</td>
            </tr>
            <tr>
                <td class="period">2</td>
                <td class="course">English 6</td>
                <td class="teacher">Jones, Mary</td>
                <td class="room">102</td>
            </tr>
        </table>
        """

        try:
            from src.scraper.parsers import parse_schedule
        except ImportError:
            pytest.skip("Parser not implemented")

        courses = parse_schedule(sample_html)

        assert isinstance(courses, list)
        assert len(courses) >= 2

    def test_parse_teacher_name_format(self):
        """Parser handles different teacher name formats."""
        sample_html = """
        <table class="schedule">
            <tr>
                <td class="course">Science</td>
                <td class="teacher">Miller, Stephen J</td>
            </tr>
        </table>
        """

        try:
            from src.scraper.parsers import parse_schedule
        except ImportError:
            pytest.skip("Parser not implemented")

        courses = parse_schedule(sample_html)

        if courses:
            teacher = courses[0].get("teacher_name", "")
            # Should preserve the name format
            assert "Miller" in teacher


class TestDataValidation:
    """Tests for data validation utilities."""

    def test_validate_date_format(self):
        """Date validation accepts various formats."""
        try:
            from src.scraper.parsers import validate_date
        except ImportError:
            pytest.skip("Validation not implemented")

        # Should accept these formats
        assert validate_date("2024-12-15")
        assert validate_date("12/15/2024")
        assert validate_date("12/15/24")

        # Should reject invalid dates
        assert not validate_date("not-a-date")
        assert not validate_date("")

    def test_validate_percentage(self):
        """Percentage validation checks range."""
        try:
            from src.scraper.parsers import validate_percentage
        except ImportError:
            pytest.skip("Validation not implemented")

        assert validate_percentage(88.6)
        assert validate_percentage(100.0)
        assert validate_percentage(0.0)

        assert not validate_percentage(-5.0)
        assert not validate_percentage(150.0)

    def test_sanitize_html_text(self):
        """HTML text sanitization removes unwanted characters."""
        try:
            from src.scraper.parsers import sanitize_text
        except ImportError:
            pytest.skip("Sanitization not implemented")

        # Should strip whitespace
        assert sanitize_text("  test  ") == "test"

        # Should handle newlines
        assert sanitize_text("test\nvalue") == "test value"

        # Should handle empty
        assert sanitize_text("") == ""
        assert sanitize_text(None) == ""
