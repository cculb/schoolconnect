"""E2E UI tests for SchoolPulse Streamlit application.

These tests verify the UI renders correctly and interactive
elements function as expected using Playwright.

Test fixtures:
- streamlit_page: Page at login screen (not logged in)
- logged_in_page: Page after successful login (main app visible)
"""

import pytest
from playwright.sync_api import Page, expect

pytestmark = [pytest.mark.e2e, pytest.mark.ui]


# =============================================================================
# Login Page Tests (use streamlit_page fixture)
# =============================================================================


class TestLoginPage:
    """Tests for the login page."""

    def test_login_page_loads(self, streamlit_page: Page):
        """Verify login page loads without critical errors."""
        app = streamlit_page.locator('[data-testid="stApp"]')
        expect(app).to_be_visible()

        # No error message should be visible
        error = streamlit_page.locator('[data-testid="stException"]')
        expect(error).not_to_be_visible()

    def test_login_title_displays(self, streamlit_page: Page):
        """Verify SchoolPulse title is visible on login page."""
        # Use .first since there are multiple elements containing "SchoolPulse"
        title = streamlit_page.get_by_text("SchoolPulse").first
        expect(title).to_be_visible()

    def test_login_form_exists(self, streamlit_page: Page):
        """Verify login form elements are present."""
        # Username input
        username_input = streamlit_page.locator('input[type="text"]').first
        expect(username_input).to_be_visible()

        # Password input
        password_input = streamlit_page.locator('input[type="password"]').first
        expect(password_input).to_be_visible()

        # Login button
        login_button = streamlit_page.locator('button:has-text("Login")')
        expect(login_button).to_be_visible()

    def test_demo_credentials_hint(self, streamlit_page: Page):
        """Verify demo credentials hint is shown."""
        hint = streamlit_page.get_by_text("demo / demo123")
        expect(hint).to_be_visible()

    def test_successful_login(self, streamlit_page: Page):
        """Verify login with demo credentials works."""
        # Fill in credentials
        username_input = streamlit_page.locator('input[type="text"]').first
        password_input = streamlit_page.locator('input[type="password"]').first

        username_input.fill("demo")
        password_input.fill("demo123")

        # Submit
        login_button = streamlit_page.locator('button:has-text("Login")')
        login_button.click()

        # Wait for navigation
        streamlit_page.wait_for_load_state("networkidle")
        streamlit_page.wait_for_timeout(1000)

        # Should now see main app content - look for Quick Actions header (with emoji)
        quick_actions = streamlit_page.get_by_text("Quick Actions").first
        expect(quick_actions).to_be_visible(timeout=10000)


# =============================================================================
# Main App Tests (use logged_in_page fixture - already logged in)
# =============================================================================


class TestPageLoad:
    """Tests for main page load and rendering after login."""

    def test_page_loads_successfully(self, logged_in_page: Page):
        """Verify app loads without critical errors."""
        app = logged_in_page.locator('[data-testid="stApp"]')
        expect(app).to_be_visible()

        # No error message should be visible
        error = logged_in_page.locator('[data-testid="stException"]')
        expect(error).not_to_be_visible()

    def test_title_displays_correctly(self, logged_in_page: Page):
        """Verify SchoolPulse title is visible."""
        # Use .first since there are multiple elements containing "SchoolPulse"
        title = logged_in_page.get_by_text("SchoolPulse").first
        expect(title).to_be_visible()

    def test_subtitle_displays(self, logged_in_page: Page):
        """Verify subtitle caption is visible."""
        caption = logged_in_page.get_by_text("Your child's academic progress")
        expect(caption).to_be_visible()


class TestSidebarSettings:
    """Tests for sidebar configuration elements."""

    def _open_sidebar(self, page: Page):
        """Helper to open the sidebar reliably."""
        # The sidebar starts collapsed, click to open
        collapsed = page.locator('[data-testid="collapsedControl"]')
        if collapsed.is_visible():
            collapsed.click()
            # Wait for sidebar to be visible
            page.locator('[data-testid="stSidebar"]').wait_for(state="visible", timeout=5000)

    def test_sidebar_can_be_opened(self, logged_in_page: Page):
        """Verify sidebar opens when clicked."""
        self._open_sidebar(logged_in_page)
        sidebar = logged_in_page.locator('[data-testid="stSidebar"]')
        expect(sidebar).to_be_visible()

    def test_model_dropdown_exists(self, logged_in_page: Page):
        """Verify AI model dropdown is present."""
        self._open_sidebar(logged_in_page)

        model_select = logged_in_page.locator(
            '[data-testid="stSelectbox"]:has(label:has-text("AI Model"))'
        )
        expect(model_select).to_be_visible()

    def test_logout_button_exists(self, logged_in_page: Page):
        """Verify Logout button is present."""
        self._open_sidebar(logged_in_page)

        logout_button = logged_in_page.locator('button:has-text("Logout")')
        expect(logout_button).to_be_visible()

    def test_clear_chat_button_exists(self, logged_in_page: Page):
        """Verify Clear Chat button is present."""
        self._open_sidebar(logged_in_page)

        clear_button = logged_in_page.locator('button:has-text("Clear Chat")')
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
    def test_quick_action_button_exists(self, logged_in_page: Page, button_text: str):
        """Verify all quick action buttons are visible."""
        button = logged_in_page.locator(f'button:has-text("{button_text}")')
        expect(button).to_be_visible()

    def test_missing_work_button_adds_message(self, logged_in_page: Page):
        """Verify clicking Missing Work adds a chat message."""
        # Click the button
        logged_in_page.locator('button:has-text("Missing Work")').click()
        logged_in_page.wait_for_load_state("networkidle")
        logged_in_page.wait_for_timeout(500)

        # Verify message appears (user message + assistant response)
        messages = logged_in_page.locator('[data-testid="stChatMessage"]')
        expect(messages).to_have_count(2, timeout=10000)


class TestDashboard:
    """Tests for the dashboard metrics section."""

    def test_dashboard_overview_visible(self, logged_in_page: Page):
        """Verify dashboard overview is displayed."""
        dashboard = logged_in_page.get_by_text("Dashboard Overview")
        expect(dashboard).to_be_visible()

    def test_courses_metric_visible(self, logged_in_page: Page):
        """Verify courses count is displayed."""
        # Look for the Courses label in a metric card
        courses = logged_in_page.locator('text=Courses').first
        expect(courses).to_be_visible()

    def test_missing_work_metric_visible(self, logged_in_page: Page):
        """Verify missing work count is displayed."""
        missing = logged_in_page.locator('text=Missing Work').first
        expect(missing).to_be_visible()

    def test_attendance_metric_visible(self, logged_in_page: Page):
        """Verify attendance percentage is displayed."""
        attendance = logged_in_page.locator('text=Attendance').first
        expect(attendance).to_be_visible()


class TestWelcomeSection:
    """Tests for the welcome section when chat is empty."""

    def test_welcome_message_visible(self, logged_in_page: Page):
        """Verify welcome message displays on empty chat."""
        # Use .first since there may be multiple matches
        welcome = logged_in_page.get_by_text("Welcome to SchoolPulse").first
        expect(welcome).to_be_visible()

    def test_tip_message_visible(self, logged_in_page: Page):
        """Verify tip message is displayed."""
        # Use .first since there may be multiple matches
        tip = logged_in_page.get_by_text("Tip:").first
        expect(tip).to_be_visible()


class TestConversationStarters:
    """Tests for conversation starter buttons."""

    def test_try_asking_label_visible(self, logged_in_page: Page):
        """Verify 'Try asking:' label is visible."""
        # Use .first since there may be multiple matches
        try_asking = logged_in_page.get_by_text("Try asking:").first
        expect(try_asking).to_be_visible()

    def test_has_conversation_starters(self, logged_in_page: Page):
        """Verify conversation starter buttons exist."""
        # Should have at least some starter buttons
        # Starters contain emojis like Target, Chart, Clipboard etc.
        starters = logged_in_page.locator('[data-testid="stButton"] button')
        count = starters.count()
        # 4 quick actions + at least 4 starters = 8 minimum
        assert count >= 8, f"Expected at least 8 buttons, got {count}"


class TestChatInterface:
    """Tests for the chat input and messages."""

    def test_chat_section_header(self, logged_in_page: Page):
        """Verify chat section header is visible."""
        # Use .first since there may be multiple matches
        header = logged_in_page.get_by_text("Chat with SchoolPulse").first
        expect(header).to_be_visible()

    def test_chat_input_exists(self, logged_in_page: Page):
        """Verify chat input field is visible."""
        chat_input = logged_in_page.locator('[data-testid="stChatInput"] textarea')
        expect(chat_input).to_be_visible()

    def test_quick_action_creates_messages(self, logged_in_page: Page):
        """Verify clicking a quick action creates chat messages."""
        # Click Attendance quick action
        logged_in_page.locator('button:has-text("Attendance")').click()
        logged_in_page.wait_for_load_state("networkidle")
        logged_in_page.wait_for_timeout(500)

        # Should have user and assistant messages
        messages = logged_in_page.locator('[data-testid="stChatMessage"]')
        expect(messages).to_have_count(2, timeout=10000)
