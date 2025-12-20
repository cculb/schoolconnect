"""PowerSchool authentication module.

Provides centralized login functionality for all scraping scripts.
"""

import os
from typing import Optional

from dotenv import load_dotenv
from playwright.sync_api import Page

load_dotenv()

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
        if verbose:
            print("Error: Missing credentials")
        return False

    login_url = f"{url}/public/home.html"
    if verbose:
        print(f"Navigating to {login_url}")

    try:
        page.goto(login_url, wait_until="networkidle")
        page.wait_for_selector("#fieldAccount", timeout=10000)

        if verbose:
            print(f"Logging in as {user}...")

        page.fill("#fieldAccount", user)
        page.fill("#fieldPassword", pwd)
        page.click("#btn-enter-sign-in")

        page.wait_for_url("**/guardian/**", timeout=timeout)
        if verbose:
            print("Login successful!")
        return True

    except Exception as e:
        if verbose:
            print(f"Login failed: {e}")
            # Check for error message on page
            error = page.query_selector(".feedback-alert")
            if error:
                print(f"Error message: {error.inner_text()}")
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
