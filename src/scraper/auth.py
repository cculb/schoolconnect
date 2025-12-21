"""PowerSchool authentication module.

Provides centralized login functionality for all scraping scripts,
including multi-student support for accounts with multiple children.
"""

import os
import re
from typing import Dict, List, Optional

from dotenv import load_dotenv
from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeout

from src.logutils import get_logger, with_context

load_dotenv()

# Module logger
logger = get_logger(__name__)

# Configuration from environment
BASE_URL = os.getenv("POWERSCHOOL_URL")
USERNAME = os.getenv("POWERSCHOOL_USERNAME")
PASSWORD = os.getenv("POWERSCHOOL_PASSWORD")


class AuthenticationError(Exception):
    """Raised when login fails."""

    pass


def get_base_url() -> str:
    """Get the PowerSchool base URL from environment.

    Returns:
        Base URL for PowerSchool portal

    Raises:
        ValueError: If POWERSCHOOL_URL is not set
    """
    if not BASE_URL:
        raise ValueError("POWERSCHOOL_URL environment variable is required")
    return BASE_URL


def get_credentials() -> tuple[str, str]:
    """Get PowerSchool credentials from environment.

    Returns:
        Tuple of (username, password)

    Raises:
        ValueError: If credentials are not set
    """
    if not USERNAME or not PASSWORD:
        raise ValueError(
            "POWERSCHOOL_USERNAME and POWERSCHOOL_PASSWORD environment variables are required"
        )
    return USERNAME, PASSWORD


def login(
    page: Page,
    base_url: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    timeout: int = 15000,
    verbose: bool = True,
) -> bool:
    """Login to PowerSchool parent portal.

    Args:
        page: Playwright page instance
        base_url: PowerSchool URL (uses env var if not provided)
        username: Login username (uses env var if not provided)
        password: Login password (uses env var if not provided)
        timeout: Timeout in ms for login completion
        verbose: Print status messages

    Returns:
        True if login successful, False otherwise

    Example:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            if login(page):
                # Proceed with scraping
                ...
    """
    url = base_url or get_base_url()
    user = username or USERNAME
    pwd = password or PASSWORD

    if not user or not pwd:
        logger.error("Missing credentials for PowerSchool login")
        return False

    login_url = f"{url}/public/home.html"
    logger.info("Navigating to login page", extra={"extra_data": {"url": login_url}})

    try:
        with with_context(operation="login", component="auth"):
            page.goto(login_url, wait_until="networkidle")
            page.wait_for_selector("#fieldAccount", timeout=10000)

            logger.debug(
                "Login form loaded, entering credentials", extra={"extra_data": {"username": user}}
            )

            page.fill("#fieldAccount", user)
            page.fill("#fieldPassword", pwd)
            page.click("#btn-enter-sign-in")

            page.wait_for_url("**/guardian/**", timeout=timeout)
            logger.info("Login successful", extra={"extra_data": {"username": user}})
            return True

    except Exception as e:
        logger.error("Login failed", extra={"extra_data": {"error": str(e)}}, exc_info=True)
        # Check for error message on page
        error = page.query_selector(".feedback-alert")
        if error:
            logger.warning(
                "Login error message displayed",
                extra={"extra_data": {"message": error.inner_text()}},
            )
        return False


def login_or_raise(
    page: Page,
    base_url: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
    timeout: int = 15000,
    verbose: bool = True,
) -> None:
    """Login to PowerSchool, raising an exception on failure.

    Args:
        page: Playwright page instance
        base_url: PowerSchool URL (uses env var if not provided)
        username: Login username (uses env var if not provided)
        password: Login password (uses env var if not provided)
        timeout: Timeout in ms for login completion
        verbose: Print status messages

    Raises:
        AuthenticationError: If login fails
    """
    if not login(page, base_url, username, password, timeout, verbose):
        raise AuthenticationError("Failed to login to PowerSchool")


# =============================================================================
# Multi-Student Support
# =============================================================================


def _extract_student_id_from_href(href: Optional[str]) -> Optional[str]:
    """Extract student ID from switchStudent JavaScript call.

    Args:
        href: The href attribute value, e.g., "javascript:switchStudent(55260);"

    Returns:
        The student ID string, or None if not found.

    Example:
        >>> _extract_student_id_from_href("javascript:switchStudent(55260);")
        "55260"
    """
    if not href:
        return None

    # Match pattern like: switchStudent(12345) or switchStudent( 12345 )
    match = re.search(r"switchStudent\s*\(\s*(\d+)\s*\)", href)
    if match:
        return match.group(1)
    return None


def get_available_students(page: Page) -> List[Dict[str, any]]:
    """Get list of all students available on the parent account.

    Parses the student selector dropdown from the PowerSchool page
    to retrieve all associated students.

    Args:
        page: Playwright page instance (must be logged in)

    Returns:
        List of student dictionaries with keys:
            - id: PowerSchool student ID
            - name: Student's display name
            - selected: True if this is the currently active student

    Example:
        >>> students = get_available_students(page)
        >>> students
        [
            {"id": "55260", "name": "Delilah", "selected": True},
            {"id": "55259", "name": "Sean", "selected": False}
        ]
    """
    students = []

    # The student list is in <ul id="students-list"> with <li> items
    # Each <li> contains an anchor with href="javascript:switchStudent(ID);"
    # The selected student's <li> has class="selected"
    student_items = page.query_selector_all("#students-list li")

    for item in student_items:
        # Check if this student is selected
        class_attr = item.get_attribute("class") or ""
        is_selected = "selected" in class_attr

        # Get the anchor element inside
        anchor = item.query_selector("a")
        if anchor:
            name = anchor.inner_text().strip()
            href = anchor.get_attribute("href")
            student_id = _extract_student_id_from_href(href)

            if student_id and name:
                students.append(
                    {
                        "id": student_id,
                        "name": name,
                        "selected": is_selected,
                    }
                )

    return students


def get_current_student(page: Page) -> Optional[Dict[str, any]]:
    """Get the currently selected student.

    Args:
        page: Playwright page instance (must be logged in)

    Returns:
        Dictionary with id and name of current student, or None if not found.

    Example:
        >>> student = get_current_student(page)
        >>> student
        {"id": "55260", "name": "Delilah"}
    """
    # Find the selected student's list item
    selected_item = page.query_selector("#students-list li.selected")

    if not selected_item:
        return None

    anchor = selected_item.query_selector("a")
    if not anchor:
        return None

    name = anchor.inner_text().strip()
    href = anchor.get_attribute("href")
    student_id = _extract_student_id_from_href(href)

    if student_id and name:
        return {"id": student_id, "name": name}

    return None


def switch_to_student(
    page: Page, student_id: str, timeout: int = 15000, verbose: bool = False
) -> bool:
    """Switch to a different student on the parent account.

    Uses the PowerSchool student switcher form to change the active student.
    This submits a POST request and waits for the page to reload.

    Args:
        page: Playwright page instance (must be logged in)
        student_id: The PowerSchool ID of the student to switch to
        timeout: Timeout in ms for page reload
        verbose: Print status messages

    Returns:
        True if switch was successful, False otherwise.

    Example:
        >>> switch_to_student(page, "55259")
        True
    """
    try:
        with with_context(operation="switch_student", student_id=student_id, component="auth"):
            # Find the switch student form
            form = page.query_selector("#switch_student_form")
            if not form:
                logger.warning("Student switch form not found on page")
                return False

            # Find the hidden input for student ID
            student_input = page.query_selector(
                '#switch_student_form input[name="selected_student_id"]'
            )
            if not student_input:
                logger.warning("Student ID input not found in form")
                return False

            logger.info("Switching to student", extra={"extra_data": {"student_id": student_id}})

            # Fill the student ID value using JavaScript to avoid focus issues
            page.evaluate(
                """(studentId) => {
                    var form = document.getElementById('switch_student_form');
                    form.selected_student_id.value = studentId;
                    form.submit();
                }""",
                student_id,
            )

            # Wait for navigation to complete
            page.wait_for_load_state("networkidle", timeout=timeout)

            # Verify the switch worked by checking current student
            # Give a short delay for the page to fully update
            page.wait_for_timeout(500)

            logger.debug(
                "Student switch navigation completed",
                extra={"extra_data": {"student_id": student_id}},
            )

            return True

    except PlaywrightTimeout:
        logger.error(
            "Timeout waiting for student switch",
            extra={"extra_data": {"student_id": student_id, "timeout_ms": timeout}},
        )
        return False
    except Exception as e:
        logger.error(
            "Error switching student",
            extra={"extra_data": {"student_id": student_id, "error": str(e)}},
            exc_info=True,
        )
        return False
