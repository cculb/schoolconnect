"""Configuration for the PowerSchool scraper."""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ScraperConfig:
    """Configuration for the PowerSchool scraper."""

    base_url: str
    username: str
    password: str
    headless: bool = True
    timeout: int = 30000  # 30 seconds
    screenshot_on_error: bool = True
    debug: bool = False

    # Selectors (can be customized per district)
    login_username_selector: str = "#fieldAccount"
    login_password_selector: str = "#fieldPassword"
    login_submit_selector: str = "#btn-enter-sign-in"
    student_tabs_selector: str = ".student-tab"

    # Page URLs (relative to base_url/guardian/)
    home_page: str = "home.html"
    assignments_page: str = "classassignments.html"
    schedule_page: str = "myschedule.html"
    comments_page: str = "teachercomments.html"
    attendance_page: str = "mba_attendance_monitor/guardian_dashboard.html"

    @classmethod
    def from_env(cls) -> "ScraperConfig":
        """Create configuration from environment variables."""
        base_url = os.environ.get("POWERSCHOOL_URL")
        username = os.environ.get("POWERSCHOOL_USERNAME")
        password = os.environ.get("POWERSCHOOL_PASSWORD")

        if not base_url:
            raise ValueError("POWERSCHOOL_URL environment variable is required")
        if not username:
            raise ValueError("POWERSCHOOL_USERNAME environment variable is required")
        if not password:
            raise ValueError("POWERSCHOOL_PASSWORD environment variable is required")

        return cls(
            base_url=base_url.rstrip("/"),
            username=username,
            password=password,
            headless=os.environ.get("SCRAPER_HEADLESS", "true").lower() == "true",
            debug=os.environ.get("SCRAPER_DEBUG", "false").lower() == "true",
        )

    @property
    def guardian_url(self) -> str:
        """Get the base URL for the guardian portal."""
        return f"{self.base_url}/guardian"

    def get_page_url(self, page: str) -> str:
        """Get full URL for a guardian page."""
        return f"{self.guardian_url}/{page}"
