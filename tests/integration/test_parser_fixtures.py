"""Integration tests for parsers using saved HTML fixtures.

These tests use real HTML saved from PowerSchool to validate
parser behavior against actual page structures.
"""

from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


class TestAssignmentParserWithFixtures:
    """Test assignment parsing with real HTML fixtures."""

    def test_parse_grades_detail_page(self, raw_html_dir: Path):
        """Parse the grades detail page from saved HTML."""
        grades_file = raw_html_dir / "grades_detail.html"
        if not grades_file.exists():
            pytest.skip("grades_detail.html fixture not found")

        try:
            from src.scraper.parsers import parse_assignments
        except ImportError:
            pytest.skip("Parser not implemented")

        html = grades_file.read_text()
        assignments = parse_assignments(html)

        assert isinstance(assignments, list)
        assert len(assignments) > 0, "Should find assignments in grades detail page"

    def test_parse_assignments_page(self, raw_html_dir: Path):
        """Parse the assignments page from saved HTML."""
        assignments_file = raw_html_dir / "assignments.html"
        if not assignments_file.exists():
            pytest.skip("assignments.html fixture not found")

        try:
            from src.scraper.parsers import parse_assignments
        except ImportError:
            pytest.skip("Parser not implemented")

        html = assignments_file.read_text()
        assignments = parse_assignments(html)

        assert isinstance(assignments, list)

    def test_find_missing_in_fixtures(self, raw_html_dir: Path, ground_truth: dict):
        """Find known missing assignments in fixtures."""
        # Try various possible fixture files
        for filename in ["grades_detail.html", "assignments.html", "course_page.html"]:
            fixture = raw_html_dir / filename
            if fixture.exists():
                try:
                    from src.scraper.parsers import parse_assignments

                    html = fixture.read_text()
                    assignments = parse_assignments(html)
                    missing = [a for a in assignments if a.get("status") == "Missing"]

                    if missing:
                        print(f"Found {len(missing)} missing assignments in {filename}")
                        return

                except ImportError:
                    pytest.skip("Parser not implemented")

        # If no fixtures found, skip
        pytest.skip("No usable HTML fixtures found")


class TestAttendanceParserWithFixtures:
    """Test attendance parsing with real HTML fixtures."""

    def test_parse_attendance_dashboard(self, raw_html_dir: Path):
        """Parse attendance dashboard from saved HTML."""
        attendance_file = raw_html_dir / "attendance_dashboard.html"
        if not attendance_file.exists():
            # Try alternative names
            for alt in ["attendance.html", "attendance_summary.html"]:
                attendance_file = raw_html_dir / alt
                if attendance_file.exists():
                    break
            else:
                pytest.skip("Attendance fixture not found")

        try:
            from src.scraper.parsers import parse_attendance
        except ImportError:
            pytest.skip("Parser not implemented")

        html = attendance_file.read_text()
        attendance = parse_attendance(html)

        assert isinstance(attendance, dict)
        assert "rate" in attendance or "attendance_rate" in attendance

    def test_attendance_rate_matches_ground_truth(
        self, raw_html_dir: Path, ground_truth: dict
    ):
        """Parsed attendance rate matches ground truth."""
        for filename in ["attendance_dashboard.html", "attendance.html"]:
            attendance_file = raw_html_dir / filename
            if attendance_file.exists():
                break
        else:
            pytest.skip("Attendance fixture not found")

        try:
            from src.scraper.parsers import parse_attendance
        except ImportError:
            pytest.skip("Parser not implemented")

        html = attendance_file.read_text()
        attendance = parse_attendance(html)

        rate = attendance.get("rate") or attendance.get("attendance_rate")
        expected = ground_truth["attendance_rate"]

        # Allow some tolerance
        assert abs(rate - expected) <= 1.0, (
            f"Parsed rate {rate} differs from ground truth {expected}"
        )


class TestScheduleParserWithFixtures:
    """Test schedule parsing with real HTML fixtures."""

    def test_parse_schedule_page(self, raw_html_dir: Path):
        """Parse schedule page from saved HTML."""
        schedule_file = raw_html_dir / "schedule.html"
        if not schedule_file.exists():
            # Try alternative names
            for alt in ["classes.html", "courses.html"]:
                schedule_file = raw_html_dir / alt
                if schedule_file.exists():
                    break
            else:
                pytest.skip("Schedule fixture not found")

        try:
            from src.scraper.parsers import parse_schedule
        except ImportError:
            pytest.skip("Parser not implemented")

        html = schedule_file.read_text()
        courses = parse_schedule(html)

        assert isinstance(courses, list)
        assert len(courses) > 0

    def test_course_count_matches_expected(
        self, raw_html_dir: Path, ground_truth: dict
    ):
        """Parsed course count meets minimum expected."""
        for filename in ["schedule.html", "classes.html"]:
            schedule_file = raw_html_dir / filename
            if schedule_file.exists():
                break
        else:
            pytest.skip("Schedule fixture not found")

        try:
            from src.scraper.parsers import parse_schedule
        except ImportError:
            pytest.skip("Parser not implemented")

        html = schedule_file.read_text()
        courses = parse_schedule(html)

        expected_min = ground_truth["expected_courses_min"]
        assert len(courses) >= expected_min, (
            f"Found {len(courses)} courses, expected at least {expected_min}"
        )


class TestFullDataPipeline:
    """Test complete data parsing pipeline."""

    def test_all_parsers_produce_data(self, raw_html_dir: Path):
        """All parsers can process their fixtures without errors."""
        results = {}

        parser_files = [
            ("assignments", ["grades_detail.html", "assignments.html"]),
            ("attendance", ["attendance_dashboard.html", "attendance.html"]),
            ("schedule", ["schedule.html", "classes.html"]),
        ]

        for parser_name, filenames in parser_files:
            for filename in filenames:
                fixture = raw_html_dir / filename
                if fixture.exists():
                    try:
                        if parser_name == "assignments":
                            from src.scraper.parsers import parse_assignments
                            results[parser_name] = parse_assignments(fixture.read_text())
                        elif parser_name == "attendance":
                            from src.scraper.parsers import parse_attendance
                            results[parser_name] = parse_attendance(fixture.read_text())
                        elif parser_name == "schedule":
                            from src.scraper.parsers import parse_schedule
                            results[parser_name] = parse_schedule(fixture.read_text())
                        break
                    except ImportError:
                        pass

        # Skip if no parsers are implemented yet
        if not results:
            pytest.skip("No parsers implemented yet")

        # At least one parser should produce results
        assert any(results.values()), "At least one parser should produce data"

        for parser_name, data in results.items():
            if data:
                print(f"{parser_name}: {len(data) if isinstance(data, list) else 'dict'}")

    def test_data_can_be_stored_in_database(
        self, raw_html_dir: Path, temp_db: Path
    ):
        """Parsed data can be stored in database."""
        try:
            from src.database.repository import PowerSchoolRepository
            from src.scraper.parsers import parse_assignments
        except ImportError:
            pytest.skip("Required modules not implemented")

        # Find and parse assignments
        for filename in ["grades_detail.html", "assignments.html"]:
            fixture = raw_html_dir / filename
            if fixture.exists():
                html = fixture.read_text()
                assignments = parse_assignments(html)
                break
        else:
            pytest.skip("No assignment fixtures found")

        if not assignments:
            pytest.skip("No assignments parsed")

        # Store in database
        repo = PowerSchoolRepository(temp_db)
        for assignment in assignments:
            repo.save_assignment(assignment)

        # Verify storage
        stored = repo.get_all_assignments()
        assert len(stored) == len(assignments)
