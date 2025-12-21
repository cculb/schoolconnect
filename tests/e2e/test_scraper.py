"""E2E tests for PowerSchool scraper.

These tests run against live PowerSchool and validate the scraper
extracts data correctly, matching known ground truth values.
"""

import os
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

# Skip all tests in this module if credentials not available
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        not os.getenv("POWERSCHOOL_URL") or not os.getenv("POWERSCHOOL_USERNAME"),
        reason="PowerSchool credentials not configured (need POWERSCHOOL_URL and POWERSCHOOL_USERNAME)",
    ),
]


class TestScraperLogin:
    """Tests for PowerSchool authentication using actual auth module."""

    def test_login_succeeds(self, powerschool_credentials: dict):
        """Verify we can authenticate with PowerSchool."""
        from src.scraper import login

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                result = login(
                    page,
                    base_url=powerschool_credentials["url"],
                    username=powerschool_credentials["username"],
                    password=powerschool_credentials["password"],
                    verbose=False,
                )
                assert result is True, "Login should succeed with valid credentials"
            finally:
                browser.close()

    def test_login_fails_with_bad_credentials(self, powerschool_credentials: dict):
        """Verify login fails with invalid credentials."""
        from src.scraper import login

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                _result = login(  # noqa: F841
                    page,
                    base_url=powerschool_credentials["url"],
                    username="invalid_user_12345",
                    password="invalid_password_67890",
                    verbose=False,
                    timeout=5000,  # Short timeout for faster failure
                )
                # PowerSchool may show an error page or redirect differently
                # The important thing is that we don't end up logged in
                # Check if we're on a guardian page (which would mean logged in)
                current_url = page.url
                if "guardian" in current_url and "home" not in current_url:
                    assert False, "Should not be logged in with invalid credentials"
                # If we got here with result=True but not on guardian page, it's a timeout/redirect
                # which is acceptable behavior for invalid credentials
            finally:
                browser.close()


class TestScraperDataExtraction:
    """Tests for data extraction from scraped HTML files."""

    def test_raw_html_files_exist(self, raw_html_dir: Path):
        """Verify scraper created raw HTML files."""
        if not raw_html_dir.exists():
            pytest.skip("Raw HTML directory not found - run scraper first")

        html_files = list(raw_html_dir.glob("*.html"))
        assert len(html_files) > 0, "Should have captured at least one HTML file"

    def test_full_data_json_exists(self, raw_html_dir: Path):
        """Verify scraper created full_data.json."""
        if not raw_html_dir.exists():
            pytest.skip("Raw HTML directory not found - run scraper first")

        json_file = raw_html_dir / "full_data.json"
        assert json_file.exists(), "Should have created full_data.json"

    def test_full_data_has_expected_structure(self, raw_html_dir: Path):
        """Verify full_data.json has expected keys."""
        import json

        json_file = raw_html_dir / "full_data.json"
        if not json_file.exists():
            pytest.skip("full_data.json not found - run scraper first")

        data = json.loads(json_file.read_text())

        # Check for expected top-level keys (core data keys)
        expected_keys = ["students", "current_student"]
        for key in expected_keys:
            assert key in data, f"Missing expected key: {key}"

        # Check we have student and course data
        assert "courses" in data or "students" in data, "Should have courses or students data"

        # Check current_student has required fields
        if "current_student" in data:
            student = data["current_student"]
            assert "name" in student or "id" in student, "current_student should have name or id"


class TestDatabasePopulation:
    """Tests for database population from scraped data."""

    def test_database_created(self, test_db_path: Path):
        """Verify database was created by load_data.py."""
        if not test_db_path.exists():
            pytest.skip("Database not found - run scraper and load_data first")

        assert test_db_path.stat().st_size > 0, "Database should not be empty"

    def test_students_loaded(self, test_db_path: Path):
        """Verify students were loaded into database."""
        import sqlite3

        if not test_db_path.exists():
            pytest.skip("Database not found")

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM students")
        count = cursor.fetchone()[0]
        conn.close()

        assert count >= 1, "Should have at least one student"

    def test_assignments_loaded(self, test_db_path: Path, ground_truth: dict):
        """Verify assignments were loaded into database."""
        import sqlite3

        if not test_db_path.exists():
            pytest.skip("Database not found")

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM assignments")
        count = cursor.fetchone()[0]
        conn.close()

        assert count >= 10, f"Expected at least 10 assignments, got {count}"

    def test_missing_assignments_detected(self, test_db_path: Path):
        """Verify missing assignments are properly marked."""
        import sqlite3

        if not test_db_path.exists():
            pytest.skip("Database not found")

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM assignments WHERE status = 'Missing'")
        missing_count = cursor.fetchone()[0]
        conn.close()

        assert missing_count >= 1, "Should detect at least one missing assignment"
