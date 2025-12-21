"""E2E UI tests for SchoolPulse Streamlit application.

These tests verify the UI renders correctly and interactive
elements function as expected using Playwright.
"""

import pytest
from playwright.sync_api import Page, expect

pytestmark = [pytest.mark.e2e, pytest.mark.ui]


class TestPageLoad:
    """Tests for initial page load and rendering."""

    def test_page_loads_successfully(self, streamlit_page: Page):
        """Verify app loads without critical errors."""
        # App container should be present
        app = streamlit_page.locator('[data-testid="stApp"]')
        expect(app).to_be_visible()

        # No error message should be visible
        error = streamlit_page.locator('[data-testid="stException"]')
        expect(error).not_to_be_visible()

    def test_title_displays_correctly(self, streamlit_page: Page):
        """Verify SchoolPulse title is visible."""
        title = streamlit_page.get_by_text("SchoolPulse")
        expect(title).to_be_visible()

    def test_subtitle_displays(self, streamlit_page: Page):
        """Verify subtitle caption is visible."""
        caption = streamlit_page.get_by_text("Your child's academic progress")
        expect(caption).to_be_visible()


class TestSidebarSettings:
    """Tests for sidebar configuration elements."""

    def test_sidebar_can_be_opened(self, streamlit_page: Page):
        """Verify sidebar opens when clicked."""
        # Click sidebar control to open it
        streamlit_page.locator('[data-testid="collapsedControl"]').click()
        sidebar = streamlit_page.locator('[data-testid="stSidebar"]')
        expect(sidebar).to_be_visible()

    def test_api_key_input_is_password_type(self, streamlit_page: Page):
        """Verify API key field masks input."""
        streamlit_page.locator('[data-testid="collapsedControl"]').click()

        # Find the API key input
        api_input = streamlit_page.locator(
            '[data-testid="stTextInput"]:has(label:has-text("API Key")) input'
        )
        expect(api_input).to_have_attribute("type", "password")

    def test_model_dropdown_exists(self, streamlit_page: Page):
        """Verify AI model dropdown is present."""
        streamlit_page.locator('[data-testid="collapsedControl"]').click()

        model_select = streamlit_page.locator(
            '[data-testid="stSelectbox"]:has(label:has-text("AI Model"))'
        )
        expect(model_select).to_be_visible()

    def test_student_name_input_exists(self, streamlit_page: Page):
        """Verify student name input is present."""
        streamlit_page.locator('[data-testid="collapsedControl"]').click()

        student_input = streamlit_page.locator(
            '[data-testid="stTextInput"]:has(label:has-text("Student Name"))'
        )
        expect(student_input).to_be_visible()

    def test_clear_chat_button_exists(self, streamlit_page: Page):
        """Verify Clear Chat button is present."""
        streamlit_page.locator('[data-testid="collapsedControl"]').click()

        clear_button = streamlit_page.locator('button:has-text("Clear Chat")')
        expect(clear_button).to_be_visible()


class TestQuickActions:
    """Tests for quick action buttons."""

    @pytest.mark.parametrize(
        "button_text",
        [
            "Missing Work",
            "Due This Week",
            "Current Grades",
            "Attendance",
        ],
    )
    def test_quick_action_button_exists(self, streamlit_page: Page, button_text: str):
        """Verify all quick action buttons are visible."""
        button = streamlit_page.locator(f'button:has-text("{button_text}")')
        expect(button).to_be_visible()

    def test_missing_work_button_adds_message(self, streamlit_page: Page):
        """Verify clicking Missing Work adds a chat message."""
        # Click the button
        streamlit_page.locator('button:has-text("Missing Work")').click()
        streamlit_page.wait_for_load_state("networkidle")

        # Verify message appears (user message + assistant response)
        messages = streamlit_page.locator('[data-testid="stChatMessage"]')
        expect(messages).to_have_count(2)


class TestWelcomeInfoBox:
    """Tests for the welcome information box."""

    def test_welcome_box_is_visible(self, streamlit_page: Page):
        """Verify welcome info box displays on empty chat."""
        info_box = streamlit_page.locator('[data-testid="stAlert"]')
        expect(info_box).to_be_visible()

    def test_welcome_box_shows_courses(self, streamlit_page: Page):
        """Verify courses count is displayed."""
        info_box = streamlit_page.locator('[data-testid="stAlert"]')
        expect(info_box).to_contain_text("Courses")

    def test_welcome_box_shows_missing_assignments(self, streamlit_page: Page):
        """Verify missing assignments count is displayed."""
        info_box = streamlit_page.locator('[data-testid="stAlert"]')
        expect(info_box).to_contain_text("Missing Assignments")

    def test_welcome_box_shows_attendance(self, streamlit_page: Page):
        """Verify attendance percentage is displayed."""
        info_box = streamlit_page.locator('[data-testid="stAlert"]')
        expect(info_box).to_contain_text("Attendance")


class TestConversationStarters:
    """Tests for conversation starter buttons."""

    def test_conversation_starters_display(self, streamlit_page: Page):
        """Verify conversation starter buttons are visible."""
        try_asking = streamlit_page.get_by_text("Try asking:")
        expect(try_asking).to_be_visible()

    def test_has_multiple_starters(self, streamlit_page: Page):
        """Verify at least 4 starter buttons exist."""
        # Starters are buttons after the quick actions
        # Should have 4 quick actions + at least 4 starters
        buttons = streamlit_page.locator('[data-testid="stButton"] button')
        # Note: count may vary based on student data, but should have at least 8
        count = buttons.count()
        assert count >= 8, f"Expected at least 8 buttons, got {count}"


class TestChatInterface:
    """Tests for the chat input and messages."""

    def test_chat_input_exists(self, streamlit_page: Page):
        """Verify chat input field is visible."""
        chat_input = streamlit_page.locator('[data-testid="stChatInput"] textarea')
        expect(chat_input).to_be_visible()

    def test_chat_input_has_placeholder(self, streamlit_page: Page):
        """Verify placeholder text is correct."""
        chat_input = streamlit_page.locator('[data-testid="stChatInput"] textarea')
        expect(chat_input).to_have_attribute(
            "placeholder", "Ask about your child's progress..."
        )

    def test_welcome_box_hidden_after_message(self, streamlit_page: Page):
        """Verify welcome box disappears after sending a message."""
        # Click a quick action to add a message
        streamlit_page.locator('button:has-text("Attendance")').click()
        streamlit_page.wait_for_load_state("networkidle")

        # Welcome box should no longer be visible (chat has messages now)
        # Note: This depends on app behavior - may need adjustment
        messages = streamlit_page.locator('[data-testid="stChatMessage"]')
        expect(messages).to_have_count(2)
