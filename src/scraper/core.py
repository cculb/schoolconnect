"""Core PowerSchool scraper using Playwright."""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from playwright.async_api import Browser, Page, async_playwright

from .config import ScraperConfig
from .parsers.assignments import parse_assignments_page
from .parsers.attendance import parse_attendance_dashboard, parse_attendance_page
from .parsers.grades import parse_grades_page


class PowerSchoolScraper:
    """Playwright-based scraper for PowerSchool parent portal."""

    def __init__(self, config: ScraperConfig):
        self.config = config
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._students: list[dict] = []

    async def __aenter__(self) -> "PowerSchoolScraper":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def start(self) -> None:
        """Start the browser."""
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(
            headless=self.config.headless
        )
        context = await self.browser.new_context(
            viewport={"width": 1280, "height": 720}
        )
        self.page = await context.new_page()
        self.page.set_default_timeout(self.config.timeout)

    async def close(self) -> None:
        """Close the browser."""
        if self.browser:
            await self.browser.close()
        if hasattr(self, "_playwright"):
            await self._playwright.stop()

    async def login(self) -> bool:
        """Authenticate to PowerSchool parent portal.

        Returns:
            True if login successful, False otherwise
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        try:
            # Navigate to login page
            await self.page.goto(self.config.guardian_url)

            # Wait for login form
            await self.page.wait_for_selector(
                self.config.login_username_selector, timeout=self.config.timeout
            )

            # Fill credentials
            await self.page.fill(
                self.config.login_username_selector, self.config.username
            )
            await self.page.fill(
                self.config.login_password_selector, self.config.password
            )

            # Submit form
            await self.page.click(self.config.login_submit_selector)

            # Wait for navigation to complete
            await self.page.wait_for_load_state("networkidle")

            # Check if we're logged in by looking for common post-login elements
            # PowerSchool typically shows student info or course list after login
            try:
                await self.page.wait_for_selector(
                    'a[href*="home.html"], .student-info, #container',
                    timeout=10000
                )
                return True
            except Exception:
                # Check for error message
                error = await self.page.query_selector(".error-message, .alert-danger")
                if error:
                    error_text = await error.text_content()
                    if self.config.debug:
                        print(f"Login error: {error_text}")
                return False

        except Exception as e:
            if self.config.debug:
                print(f"Login failed: {e}")
            if self.config.screenshot_on_error and self.page:
                await self.page.screenshot(path="login_error.png")
            return False

    async def get_student_list(self) -> list[dict]:
        """Get list of students (for multi-child households).

        Returns:
            List of dictionaries with student info
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        students = []

        # Look for student tabs/selector
        student_elements = await self.page.query_selector_all(
            self.config.student_tabs_selector
        )

        if not student_elements:
            # Try alternative selectors
            student_elements = await self.page.query_selector_all(
                'a[href*="sw="], .studentpicker, [data-student-id]'
            )

        for elem in student_elements:
            try:
                name = await elem.text_content()
                href = await elem.get_attribute("href") or ""
                student_id = self._extract_student_id(href)

                if name:
                    students.append({
                        "student_id": student_id or str(uuid.uuid4())[:8],
                        "name": name.strip(),
                        "href": href,
                    })
            except Exception:
                continue

        # If no student tabs found, try to get current student info
        if not students:
            student_info = await self.page.query_selector('.student-name, #student-name')
            if student_info:
                name = await student_info.text_content()
                if name:
                    students.append({
                        "student_id": "current",
                        "name": name.strip(),
                        "href": "",
                    })

        self._students = students
        return students

    async def switch_student(self, student_href: str) -> bool:
        """Switch to viewing a specific student.

        Args:
            student_href: The href from the student selector

        Returns:
            True if switch successful
        """
        if not self.page or not student_href:
            return False

        try:
            await self.page.goto(f"{self.config.guardian_url}/{student_href}")
            await self.page.wait_for_load_state("networkidle")
            return True
        except Exception:
            return False

    async def scrape_grades_attendance(self) -> dict[str, Any]:
        """Scrape the home page for grades and attendance overview.

        Returns:
            Dictionary with grades and attendance data
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        url = self.config.get_page_url(self.config.home_page)
        await self.page.goto(url)
        await self.page.wait_for_load_state("networkidle")

        html = await self.page.content()
        return parse_grades_page(html)

    async def scrape_assignments(self, term: str = "S1") -> list[dict[str, Any]]:
        """Scrape the assignments page.

        Args:
            term: The term to filter by (S1, S2, Q1, etc.)

        Returns:
            List of assignment dictionaries
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        url = self.config.get_page_url(self.config.assignments_page)
        await self.page.goto(url)
        await self.page.wait_for_load_state("networkidle")

        # Try to select the term if there's a term selector
        term_selector = await self.page.query_selector(
            'select[name="term"], #term-select, [data-term]'
        )
        if term_selector:
            try:
                await term_selector.select_option(value=term)
                await self.page.wait_for_load_state("networkidle")
            except Exception:
                pass

        html = await self.page.content()
        return parse_assignments_page(html)

    async def scrape_schedule(self) -> list[dict[str, Any]]:
        """Scrape the schedule page.

        Returns:
            List of course schedule entries
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        url = self.config.get_page_url(self.config.schedule_page)
        await self.page.goto(url)
        await self.page.wait_for_load_state("networkidle")

        # Parse schedule table
        html = await self.page.content()
        return self._parse_schedule(html)

    async def scrape_attendance_dashboard(self) -> dict[str, Any]:
        """Scrape the attendance dashboard.

        Returns:
            Dictionary with attendance summary
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        url = self.config.get_page_url(self.config.attendance_page)
        await self.page.goto(url)
        await self.page.wait_for_load_state("networkidle")

        html = await self.page.content()
        return parse_attendance_dashboard(html)

    async def scrape_teacher_comments(self, term: str = "Q2") -> list[dict[str, Any]]:
        """Scrape teacher comments.

        Args:
            term: The grading term

        Returns:
            List of teacher comments
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        url = f"{self.config.get_page_url(self.config.comments_page)}?fg={term}"
        await self.page.goto(url)
        await self.page.wait_for_load_state("networkidle")

        html = await self.page.content()
        return self._parse_comments(html)

    async def full_sync(self, student_id: str | None = None) -> dict[str, Any]:
        """Perform a full data sync for a student.

        Args:
            student_id: Optional student ID to sync. If not provided, syncs current student.

        Returns:
            Dictionary with all scraped data
        """
        results = {
            "student_id": student_id or "current",
            "scraped_at": datetime.now().isoformat(),
            "grades": {},
            "assignments": [],
            "schedule": [],
            "attendance": {},
            "comments": [],
            "errors": [],
        }

        try:
            results["grades"] = await self.scrape_grades_attendance()
        except Exception as e:
            results["errors"].append(f"Failed to scrape grades: {e}")

        try:
            results["assignments"] = await self.scrape_assignments()
        except Exception as e:
            results["errors"].append(f"Failed to scrape assignments: {e}")

        try:
            results["schedule"] = await self.scrape_schedule()
        except Exception as e:
            results["errors"].append(f"Failed to scrape schedule: {e}")

        try:
            results["attendance"] = await self.scrape_attendance_dashboard()
        except Exception as e:
            results["errors"].append(f"Failed to scrape attendance: {e}")

        try:
            results["comments"] = await self.scrape_teacher_comments()
        except Exception as e:
            results["errors"].append(f"Failed to scrape comments: {e}")

        return results

    def _extract_student_id(self, href: str) -> str | None:
        """Extract student ID from a URL."""
        if not href:
            return None

        # Look for sw= parameter or student ID in URL
        import re
        match = re.search(r"sw=(\d+)", href)
        if match:
            return match.group(1)

        match = re.search(r"student[_-]?id=(\d+)", href, re.IGNORECASE)
        if match:
            return match.group(1)

        return None

    def _parse_schedule(self, html: str) -> list[dict[str, Any]]:
        """Parse the schedule page HTML."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        schedule = []

        # Find schedule table
        table = soup.find("table", class_=lambda c: c and "schedule" in c.lower())
        if not table:
            tables = soup.find_all("table")
            for t in tables:
                headers = t.find_all("th")
                header_text = " ".join(h.get_text() for h in headers).lower()
                if "course" in header_text and ("room" in header_text or "teacher" in header_text):
                    table = t
                    break

        if not table:
            return schedule

        rows = table.find_all("tr")
        for row in rows[1:]:
            cols = row.find_all("td")
            if len(cols) >= 3:
                try:
                    entry = {
                        "course_name": cols[0].get_text(strip=True),
                        "expression": cols[1].get_text(strip=True) if len(cols) > 1 else None,
                        "room": cols[2].get_text(strip=True) if len(cols) > 2 else None,
                        "teacher_name": cols[3].get_text(strip=True) if len(cols) > 3 else None,
                        "term": cols[4].get_text(strip=True) if len(cols) > 4 else None,
                    }
                    schedule.append(entry)
                except (IndexError, ValueError):
                    continue

        return schedule

    def _parse_comments(self, html: str) -> list[dict[str, Any]]:
        """Parse teacher comments HTML."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        comments = []

        # Find comment sections
        comment_sections = soup.find_all(
            class_=lambda c: c and ("comment" in c.lower() or "note" in c.lower())
        )

        for section in comment_sections:
            try:
                course = section.find(class_=lambda c: c and "course" in c.lower())
                teacher = section.find(class_=lambda c: c and "teacher" in c.lower())
                text = section.find(class_=lambda c: c and "text" in c.lower())

                if text:
                    comment = {
                        "course_name": course.get_text(strip=True) if course else None,
                        "teacher_name": teacher.get_text(strip=True) if teacher else None,
                        "comment_text": text.get_text(strip=True),
                    }
                    comments.append(comment)
            except Exception:
                continue

        # Alternative: look for comment table
        if not comments:
            table = soup.find("table")
            if table:
                rows = table.find_all("tr")
                for row in rows[1:]:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        comments.append({
                            "course_name": cols[0].get_text(strip=True) if cols else None,
                            "teacher_name": cols[1].get_text(strip=True) if len(cols) > 1 else None,
                            "comment_text": cols[2].get_text(strip=True) if len(cols) > 2 else None,
                        })

        return comments
