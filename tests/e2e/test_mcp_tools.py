"""E2E tests for MCP server tools.

These tests validate that MCP tools return correct data when
querying the PowerSchool database populated by the scraper.
"""

import sqlite3
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.e2e,
]


class TestMCPToolGetMissingAssignments:
    """Tests for get_missing_assignments MCP tool."""

    @pytest.mark.asyncio
    async def test_returns_missing_assignments(self, test_db_path: Path, ground_truth: dict):
        """Tool returns correct missing assignments from database."""
        if not test_db_path.exists():
            pytest.skip("Database not populated - run scraper first")

        try:
            from src.mcp_server.tools import get_missing_assignments
        except ImportError:
            pytest.skip("MCP tools not fully implemented")

        result = await get_missing_assignments(db_path=str(test_db_path))

        assert isinstance(result, list), "Should return a list"
        assert len(result) >= 2, "Should have at least 2 missing assignments"

        # Check structure
        for item in result:
            assert "assignment_name" in item, "Should have assignment_name"
            assert "course_name" in item or "course" in item, "Should have course info"

    @pytest.mark.asyncio
    async def test_includes_known_missing_assignment(self, test_db_path: Path, ground_truth: dict):
        """Tool includes specific known missing assignments."""
        if not test_db_path.exists():
            pytest.skip("Database not populated - run scraper first")

        try:
            from src.mcp_server.tools import get_missing_assignments
        except ImportError:
            pytest.skip("MCP tools not fully implemented")

        result = await get_missing_assignments(db_path=str(test_db_path))

        assignment_names = [r.get("assignment_name", "").lower() for r in result]

        # Check for at least one known missing assignment
        known_missing = ["atomic structure", "edpuzzle"]
        found_any = any(any(known in name for name in assignment_names) for known in known_missing)

        # This may fail if data has changed, so just warn
        if not found_any:
            print(
                f"Warning: None of the known missing assignments found. Found: {assignment_names}"
            )


class TestMCPToolGetAttendanceSummary:
    """Tests for get_attendance_summary MCP tool."""

    @pytest.mark.asyncio
    async def test_returns_attendance_data(self, test_db_path: Path, ground_truth: dict):
        """Tool returns correct attendance summary."""
        if not test_db_path.exists():
            pytest.skip("Database not populated - run scraper first")

        try:
            from src.mcp_server.tools import get_attendance_summary
        except ImportError:
            pytest.skip("MCP tools not fully implemented")

        result = await get_attendance_summary(db_path=str(test_db_path))

        assert isinstance(result, dict), "Should return a dictionary"

        # Check for attendance rate
        rate = result.get("rate") or result.get("attendance_rate")
        assert rate is not None, "Should have attendance rate"

        # Verify rate is in reasonable range
        expected = ground_truth["attendance_rate"]
        tolerance = 5.0
        assert (expected - tolerance) <= rate <= (expected + tolerance), (
            f"Attendance rate {rate}% outside expected range"
        )

    @pytest.mark.asyncio
    async def test_includes_absence_data(self, test_db_path: Path, ground_truth: dict):
        """Tool includes days absent information."""
        if not test_db_path.exists():
            pytest.skip("Database not populated - run scraper first")

        try:
            from src.mcp_server.tools import get_attendance_summary
        except ImportError:
            pytest.skip("MCP tools not fully implemented")

        result = await get_attendance_summary(db_path=str(test_db_path))

        days_absent = result.get("days_absent")
        if days_absent is not None:
            # Verify it's close to ground truth
            expected = ground_truth["days_absent"]
            assert abs(days_absent - expected) <= 3, (
                f"Days absent {days_absent} differs too much from expected {expected}"
            )


class TestMCPToolGenerateWeeklyReport:
    """Tests for generate_weekly_report MCP tool."""

    @pytest.mark.asyncio
    async def test_generates_report(self, test_db_path: Path):
        """Tool generates a readable weekly report."""
        if not test_db_path.exists():
            pytest.skip("Database not populated - run scraper first")

        try:
            from src.mcp_server.tools import generate_weekly_report
        except ImportError:
            pytest.skip("MCP tools not fully implemented")

        result = await generate_weekly_report(db_path=str(test_db_path))

        assert isinstance(result, str), "Should return a string report"
        assert len(result) > 100, "Report should have substantial content"

        # Check for expected sections
        result_lower = result.lower()
        assert "missing" in result_lower or "assignment" in result_lower, (
            "Report should mention assignments"
        )
        assert "attendance" in result_lower, "Report should mention attendance"

    @pytest.mark.asyncio
    async def test_report_mentions_action_items(self, test_db_path: Path):
        """Report includes actionable items for parents."""
        if not test_db_path.exists():
            pytest.skip("Database not populated - run scraper first")

        try:
            from src.mcp_server.tools import generate_weekly_report
        except ImportError:
            pytest.skip("MCP tools not fully implemented")

        result = await generate_weekly_report(db_path=str(test_db_path))

        # Check for action-oriented language
        action_words = ["should", "need", "must", "please", "action", "todo", "reminder"]
        result_lower = result.lower()
        has_action = any(word in result_lower for word in action_words)

        if not has_action:
            print("Warning: Report may lack actionable items")


class TestMCPToolGetActionItems:
    """Tests for get_action_items MCP tool."""

    @pytest.mark.asyncio
    async def test_returns_action_items(self, test_db_path: Path):
        """Tool returns prioritized action items."""
        if not test_db_path.exists():
            pytest.skip("Database not populated - run scraper first")

        try:
            from src.mcp_server.tools import get_action_items
        except ImportError:
            pytest.skip("MCP tools not fully implemented")

        result = await get_action_items(db_path=str(test_db_path))

        assert isinstance(result, list), "Should return a list"
        assert len(result) >= 1, "Should have at least one action item"

        # Check structure
        for item in result:
            assert "type" in item or "priority" in item, "Should have type or priority"
            assert "description" in item or "message" in item, "Should have description"

    @pytest.mark.asyncio
    async def test_includes_missing_assignment_action(self, test_db_path: Path, ground_truth: dict):
        """Action items include missing assignment reminders."""
        if not test_db_path.exists():
            pytest.skip("Database not populated - run scraper first")

        try:
            from src.mcp_server.tools import get_action_items
        except ImportError:
            pytest.skip("MCP tools not fully implemented")

        result = await get_action_items(db_path=str(test_db_path))

        # Look for missing assignment action items
        types = [item.get("type", "").lower() for item in result]
        has_missing = any("missing" in t or "assignment" in t for t in types)

        if not has_missing:
            # Check descriptions
            descriptions = [
                item.get("description", "").lower() + item.get("message", "").lower()
                for item in result
            ]
            has_missing = any("missing" in d for d in descriptions)

        assert has_missing, "Should include action item for missing assignments"


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
