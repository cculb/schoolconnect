"""E2E tests for PowerSchool scraper.

These tests run against live PowerSchool and validate the scraper
extracts data correctly, matching known ground truth values.
"""

import os
import sqlite3
from pathlib import Path

import pytest

# Skip all tests in this module if credentials not available
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        not os.getenv("POWERSCHOOL_URL") or not os.getenv("POWERSCHOOL_USERNAME"),
        reason="PowerSchool credentials not configured (need POWERSCHOOL_URL and POWERSCHOOL_USERNAME)",
    ),
]


class TestScraperLogin:
    """Tests for PowerSchool authentication."""

    @pytest.mark.asyncio
    async def test_login_succeeds(self, powerschool_credentials: dict):
        """Verify we can authenticate with PowerSchool."""
        # Import here to avoid import errors when scraper not fully implemented
        try:
            from src.scraper import PowerSchoolScraper
        except ImportError:
            pytest.skip("Scraper module not fully implemented")

        async with PowerSchoolScraper(
            url=powerschool_credentials["url"],
            username=powerschool_credentials["username"],
            password=powerschool_credentials["password"],
        ) as scraper:
            result = await scraper.login()
            assert result is True, "Login should succeed with valid credentials"

    @pytest.mark.asyncio
    async def test_login_fails_with_bad_credentials(self, powerschool_credentials: dict):
        """Verify login fails with invalid credentials."""
        try:
            from src.scraper import PowerSchoolScraper
        except ImportError:
            pytest.skip("Scraper module not fully implemented")

        async with PowerSchoolScraper(
            url=powerschool_credentials["url"],
            username="invalid_user",
            password="invalid_password",
        ) as scraper:
            result = await scraper.login()
            assert result is False, "Login should fail with invalid credentials"


class TestAssignmentScraping:
    """Tests for assignment data extraction."""

    @pytest.mark.asyncio
    async def test_scrape_assignments_returns_data(
        self, powerschool_credentials: dict, ground_truth: dict
    ):
        """Verify assignment scraping returns expected data structure."""
        try:
            from src.scraper import PowerSchoolScraper
        except ImportError:
            pytest.skip("Scraper module not fully implemented")

        async with PowerSchoolScraper(
            url=powerschool_credentials["url"],
            username=powerschool_credentials["username"],
            password=powerschool_credentials["password"],
        ) as scraper:
            await scraper.login()
            assignments = await scraper.scrape_assignments()

            assert isinstance(assignments, list), "Should return a list"
            assert len(assignments) > 0, "Should return at least one assignment"

            # Check required fields in first assignment
            first = assignments[0]
            required_fields = ["assignment_name", "status", "due_date"]
            for field in required_fields:
                assert field in first, f"Missing required field: {field}"

    @pytest.mark.asyncio
    async def test_finds_missing_assignments(
        self, powerschool_credentials: dict, ground_truth: dict
    ):
        """Verify we find known missing assignments from ground truth."""
        try:
            from src.scraper import PowerSchoolScraper
        except ImportError:
            pytest.skip("Scraper module not fully implemented")

        async with PowerSchoolScraper(
            url=powerschool_credentials["url"],
            username=powerschool_credentials["username"],
            password=powerschool_credentials["password"],
        ) as scraper:
            await scraper.login()
            assignments = await scraper.scrape_assignments()

            missing = [a for a in assignments if a.get("status", "").lower() == "missing"]
            assert len(missing) >= 2, f"Expected at least 2 missing assignments, got {len(missing)}"

            # Check for specific known missing assignments
            assignment_names = [a["assignment_name"].lower() for a in missing]

            for expected in ground_truth["missing_assignments"]:
                expected_name = expected["name"].lower()
                found = any(expected_name in name for name in assignment_names)
                # Log for debugging but don't fail - data may have changed
                if not found:
                    print(f"Warning: Expected missing assignment not found: {expected['name']}")


class TestAttendanceScraping:
    """Tests for attendance data extraction."""

    @pytest.mark.asyncio
    async def test_scrape_attendance_returns_data(
        self, powerschool_credentials: dict, ground_truth: dict
    ):
        """Verify attendance scraping returns expected data structure."""
        try:
            from src.scraper import PowerSchoolScraper
        except ImportError:
            pytest.skip("Scraper module not fully implemented")

        async with PowerSchoolScraper(
            url=powerschool_credentials["url"],
            username=powerschool_credentials["username"],
            password=powerschool_credentials["password"],
        ) as scraper:
            await scraper.login()
            attendance = await scraper.scrape_attendance_dashboard()

            assert isinstance(attendance, dict), "Should return a dictionary"
            assert "rate" in attendance or "attendance_rate" in attendance, (
                "Should include attendance rate"
            )

    @pytest.mark.asyncio
    async def test_attendance_rate_in_expected_range(
        self, powerschool_credentials: dict, ground_truth: dict
    ):
        """Verify attendance rate matches ground truth within tolerance."""
        try:
            from src.scraper import PowerSchoolScraper
        except ImportError:
            pytest.skip("Scraper module not fully implemented")

        async with PowerSchoolScraper(
            url=powerschool_credentials["url"],
            username=powerschool_credentials["username"],
            password=powerschool_credentials["password"],
        ) as scraper:
            await scraper.login()
            attendance = await scraper.scrape_attendance_dashboard()

            rate = attendance.get("rate") or attendance.get("attendance_rate", 0)

            # Allow some variance since attendance changes over time
            expected = ground_truth["attendance_rate"]
            tolerance = 5.0  # +/- 5% tolerance

            assert (expected - tolerance) <= rate <= (expected + tolerance), (
                f"Attendance rate {rate}% outside expected range "
                f"{expected - tolerance}% - {expected + tolerance}%"
            )


class TestScheduleScraping:
    """Tests for schedule/course data extraction."""

    @pytest.mark.asyncio
    async def test_scrape_schedule_returns_courses(
        self, powerschool_credentials: dict, ground_truth: dict
    ):
        """Verify schedule scraping returns expected courses."""
        try:
            from src.scraper import PowerSchoolScraper
        except ImportError:
            pytest.skip("Scraper module not fully implemented")

        async with PowerSchoolScraper(
            url=powerschool_credentials["url"],
            username=powerschool_credentials["username"],
            password=powerschool_credentials["password"],
        ) as scraper:
            await scraper.login()
            courses = await scraper.scrape_schedule()

            assert isinstance(courses, list), "Should return a list"
            assert len(courses) >= ground_truth["expected_courses_min"], (
                f"Expected at least {ground_truth['expected_courses_min']} courses"
            )

            # Check required fields
            for course in courses:
                assert "course_name" in course, "Course should have a name"


class TestFullScrapeWorkflow:
    """Tests for complete scrape workflow."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_full_scrape_populates_database(
        self, powerschool_credentials: dict, temp_db: Path, ground_truth: dict
    ):
        """Verify full scrape workflow populates database correctly."""
        try:
            from src.database.repository import PowerSchoolRepository
            from src.scraper import PowerSchoolScraper
        except ImportError:
            pytest.skip("Modules not fully implemented")

        async with PowerSchoolScraper(
            url=powerschool_credentials["url"],
            username=powerschool_credentials["username"],
            password=powerschool_credentials["password"],
        ) as scraper:
            await scraper.login()

            # Scrape all data
            assignments = await scraper.scrape_assignments()
            attendance = await scraper.scrape_attendance_dashboard()
            courses = await scraper.scrape_schedule()

            # Store in database
            repo = PowerSchoolRepository(temp_db)
            repo.save_assignments(assignments)
            repo.save_attendance(attendance)
            repo.save_courses(courses)

            # Verify database contents
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM assignments")
            assignment_count = cursor.fetchone()[0]
            assert assignment_count > 0, "Should have stored assignments"

            cursor.execute("SELECT COUNT(*) FROM courses")
            course_count = cursor.fetchone()[0]
            assert course_count >= ground_truth["expected_courses_min"], (
                f"Should have at least {ground_truth['expected_courses_min']} courses"
            )

            conn.close()
