"""E2E tests for multi-student scraper functionality.

Tests for student switching capability in the PowerSchool scraper,
allowing data extraction for all students associated with a parent account.
"""

import os
from unittest.mock import MagicMock

import pytest

# Skip module if credentials not available
pytestmark = [
    pytest.mark.e2e,
]


class TestGetAvailableStudents:
    """Tests for get_available_students function."""

    def test_parses_student_list_from_page(self):
        """Verify student list is correctly parsed from page HTML."""
        from src.scraper.auth import get_available_students

        # Create mock page with student list HTML
        mock_page = MagicMock()
        mock_page.query_selector_all.return_value = [
            self._create_mock_student_element("55260", "Delilah", selected=True),
            self._create_mock_student_element("55259", "Sean", selected=False),
        ]

        students = get_available_students(mock_page)

        assert len(students) == 2
        assert students[0] == {"id": "55260", "name": "Delilah", "selected": True}
        assert students[1] == {"id": "55259", "name": "Sean", "selected": False}

    def test_returns_empty_list_when_no_students(self):
        """Return empty list when no student elements found."""
        from src.scraper.auth import get_available_students

        mock_page = MagicMock()
        mock_page.query_selector_all.return_value = []

        students = get_available_students(mock_page)

        assert students == []

    def test_handles_single_student(self):
        """Handle accounts with only one student."""
        from src.scraper.auth import get_available_students

        mock_page = MagicMock()
        mock_page.query_selector_all.return_value = [
            self._create_mock_student_element("55260", "Delilah", selected=True),
        ]

        students = get_available_students(mock_page)

        assert len(students) == 1
        assert students[0]["id"] == "55260"
        assert students[0]["selected"] is True

    def test_identifies_selected_student(self):
        """Correctly identify which student is currently selected."""
        from src.scraper.auth import get_available_students

        mock_page = MagicMock()
        mock_page.query_selector_all.return_value = [
            self._create_mock_student_element("55260", "Delilah", selected=False),
            self._create_mock_student_element("55259", "Sean", selected=True),
        ]

        students = get_available_students(mock_page)

        # Sean should be selected
        selected = [s for s in students if s["selected"]]
        assert len(selected) == 1
        assert selected[0]["name"] == "Sean"

    def _create_mock_student_element(
        self, student_id: str, name: str, selected: bool = False
    ) -> MagicMock:
        """Create a mock element matching PowerSchool student list structure.

        The structure is:
        <li class="selected">  (class="selected" only if currently active)
            <a href="javascript:switchStudent(55260);">Delilah</a>
        </li>
        """
        mock_li = MagicMock()

        # Mock the class attribute for selection detection
        mock_li.get_attribute.side_effect = lambda attr: (
            "selected" if attr == "class" and selected else ""
        )

        # Mock the anchor element inside
        mock_anchor = MagicMock()
        mock_anchor.inner_text.return_value = name
        mock_anchor.get_attribute.return_value = f"javascript:switchStudent({student_id});"

        mock_li.query_selector.return_value = mock_anchor

        return mock_li


class TestSwitchToStudent:
    """Tests for switch_to_student function."""

    def test_switches_to_different_student(self):
        """Verify switching to a different student works."""
        from src.scraper.auth import switch_to_student

        mock_page = MagicMock()

        # Mock form and input elements
        mock_form = MagicMock()
        mock_input = MagicMock()
        mock_page.query_selector.side_effect = lambda sel: (
            mock_form if sel == "#switch_student_form" else mock_input
        )

        # Mock successful navigation
        mock_page.wait_for_load_state.return_value = None
        mock_page.wait_for_timeout.return_value = None
        mock_page.evaluate.return_value = None

        result = switch_to_student(mock_page, "55259")

        assert result is True
        # Verify evaluate was called with the student ID
        mock_page.evaluate.assert_called_once()
        call_args = mock_page.evaluate.call_args
        assert "55259" in str(call_args)

    def test_returns_false_when_form_not_found(self):
        """Return False if switch form is not found on page."""
        from src.scraper.auth import switch_to_student

        mock_page = MagicMock()
        mock_page.query_selector.return_value = None

        result = switch_to_student(mock_page, "55259")

        assert result is False

    def test_handles_navigation_timeout(self):
        """Handle timeout waiting for page load after switch."""
        from src.scraper.auth import switch_to_student

        mock_page = MagicMock()
        mock_form = MagicMock()
        mock_input = MagicMock()
        mock_page.query_selector.side_effect = lambda sel: (
            mock_form if sel == "#switch_student_form" else mock_input
        )
        mock_page.evaluate.return_value = None

        # Simulate timeout on wait
        from playwright.sync_api import TimeoutError as PlaywrightTimeout

        mock_page.wait_for_load_state.side_effect = PlaywrightTimeout("Timeout")

        result = switch_to_student(mock_page, "55259")

        assert result is False

    def test_returns_false_for_invalid_student_id(self):
        """Return False when trying to switch to non-existent student."""
        from src.scraper.auth import switch_to_student

        mock_page = MagicMock()
        mock_page.query_selector.return_value = None

        result = switch_to_student(mock_page, "invalid_id")

        assert result is False

    def test_uses_correct_form_selectors(self):
        """Verify correct CSS selectors are used for form interaction."""
        from src.scraper.auth import switch_to_student

        mock_page = MagicMock()
        mock_form = MagicMock()
        mock_input = MagicMock()

        # Track selector calls
        selector_calls = []

        def track_selector(sel):
            selector_calls.append(sel)
            if sel == "#switch_student_form":
                return mock_form
            elif 'name="selected_student_id"' in sel:
                return mock_input
            return None

        mock_page.query_selector.side_effect = track_selector
        mock_page.wait_for_load_state.return_value = None
        mock_page.wait_for_timeout.return_value = None
        mock_page.evaluate.return_value = None

        switch_to_student(mock_page, "55260")

        # Should query for form and input
        assert "#switch_student_form" in selector_calls


class TestGetCurrentStudent:
    """Tests for get_current_student function."""

    def test_returns_current_student(self):
        """Return the currently selected student."""
        from src.scraper.auth import get_current_student

        mock_page = MagicMock()

        # Mock selected student element
        mock_selected_li = MagicMock()
        mock_anchor = MagicMock()
        mock_anchor.inner_text.return_value = "Delilah"
        mock_anchor.get_attribute.return_value = "javascript:switchStudent(55260);"
        mock_selected_li.query_selector.return_value = mock_anchor

        mock_page.query_selector.return_value = mock_selected_li

        student = get_current_student(mock_page)

        assert student is not None
        assert student["id"] == "55260"
        assert student["name"] == "Delilah"

    def test_returns_none_when_no_student_selected(self):
        """Return None if no student is selected."""
        from src.scraper.auth import get_current_student

        mock_page = MagicMock()
        mock_page.query_selector.return_value = None

        student = get_current_student(mock_page)

        assert student is None


class TestMultiStudentIntegration:
    """Integration tests for multi-student workflow."""

    @pytest.mark.skipif(
        not os.getenv("POWERSCHOOL_URL") or not os.getenv("POWERSCHOOL_USERNAME"),
        reason="PowerSchool credentials not configured",
    )
    def test_list_students_after_login(self, powerschool_credentials: dict):
        """List available students after successful login."""
        from playwright.sync_api import sync_playwright

        from src.scraper import login
        from src.scraper.auth import get_available_students

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
                assert result is True, "Login should succeed"

                # Get student list
                students = get_available_students(page)

                # Should have at least one student
                assert len(students) >= 1, "Should have at least one student"

                # Each student should have required fields
                for student in students:
                    assert "id" in student, "Student should have id"
                    assert "name" in student, "Student should have name"
                    assert "selected" in student, "Student should have selected flag"

                # Exactly one student should be selected
                selected = [s for s in students if s["selected"]]
                assert len(selected) == 1, "Exactly one student should be selected"

            finally:
                browser.close()

    @pytest.mark.skipif(
        not os.getenv("POWERSCHOOL_URL") or not os.getenv("POWERSCHOOL_USERNAME"),
        reason="PowerSchool credentials not configured",
    )
    def test_switch_between_students(self, powerschool_credentials: dict):
        """Switch between multiple students on the account."""
        from playwright.sync_api import sync_playwright

        from src.scraper import login
        from src.scraper.auth import (
            get_available_students,
            get_current_student,
            switch_to_student,
        )

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
                assert result is True, "Login should succeed"

                students = get_available_students(page)

                if len(students) < 2:
                    pytest.skip("Need at least 2 students to test switching")

                # Get initial student
                initial_student = get_current_student(page)
                assert initial_student is not None, (
                    f"Should have current student. Students found: {students}"
                )

                # Find a different student to switch to
                other_student = next(
                    (s for s in students if s["id"] != initial_student["id"]), None
                )
                assert other_student is not None

                # Switch to other student with verbose output for debugging
                switch_result = switch_to_student(page, other_student["id"], verbose=True)
                assert switch_result is True, (
                    f"Switch should succeed. Tried to switch to {other_student}"
                )

                # Verify switch worked
                current = get_current_student(page)
                assert current is not None
                assert current["id"] == other_student["id"], (
                    f"Expected {other_student['id']}, got {current['id']}"
                )

                # Switch back to original
                switch_back = switch_to_student(page, initial_student["id"], verbose=True)
                assert switch_back is True

                final = get_current_student(page)
                assert final["id"] == initial_student["id"]

            finally:
                browser.close()


class TestStudentIDExtraction:
    """Tests for extracting student ID from anchor href."""

    def test_extracts_id_from_valid_href(self):
        """Extract student ID from switchStudent JavaScript call."""
        from src.scraper.auth import _extract_student_id_from_href

        href = "javascript:switchStudent(55260);"
        student_id = _extract_student_id_from_href(href)

        assert student_id == "55260"

    def test_extracts_id_with_different_format(self):
        """Handle variations in href format."""
        from src.scraper.auth import _extract_student_id_from_href

        # No semicolon
        assert _extract_student_id_from_href("javascript:switchStudent(12345)") == "12345"

        # Extra spaces
        assert _extract_student_id_from_href("javascript:switchStudent( 99999 );") == "99999"

    def test_returns_none_for_invalid_href(self):
        """Return None for malformed href."""
        from src.scraper.auth import _extract_student_id_from_href

        assert _extract_student_id_from_href("") is None
        assert _extract_student_id_from_href("javascript:void(0)") is None
        assert _extract_student_id_from_href("http://example.com") is None
        assert _extract_student_id_from_href(None) is None
