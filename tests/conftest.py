"""Pytest configuration and fixtures for PowerSchool Portal tests."""

import asyncio
import base64
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Generator

import pytest
import requests
from dotenv import load_dotenv
from playwright.sync_api import Browser, Page, sync_playwright

# Load environment variables
load_dotenv()


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests (no external dependencies)")
    config.addinivalue_line("markers", "integration: Integration tests (database, parsers)")
    config.addinivalue_line("markers", "e2e: End-to-end tests (requires PowerSchool access)")
    config.addinivalue_line("markers", "slow: Slow running tests")


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def powerschool_credentials() -> dict:
    """Get PowerSchool credentials from environment."""
    password = os.getenv("POWERSCHOOL_PASSWORD", "")

    # Handle base64 encoded password
    if password:
        try:
            decoded = base64.b64decode(password).decode("utf-8")
            password = decoded
        except Exception:
            # Password is not base64 encoded, use as-is
            pass

    url = os.getenv("POWERSCHOOL_URL", "")
    if not url:
        pytest.skip("POWERSCHOOL_URL environment variable not set")

    return {
        "url": url,
        "username": os.getenv("POWERSCHOOL_USERNAME", ""),
        "password": password,
    }


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def raw_html_dir(project_root: Path) -> Path:
    """Get the raw HTML directory."""
    return project_root / "raw_html"


@pytest.fixture(scope="session")
def test_db_path(project_root: Path) -> Path:
    """Get path to the test database."""
    return project_root / "powerschool.db"


@pytest.fixture(scope="function")
def temp_db(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary database for testing."""
    db_path = tmp_path / "test_powerschool.db"

    # Create schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            grade_level INTEGER,
            school_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS courses (
            course_id TEXT PRIMARY KEY,
            student_id TEXT,
            course_name TEXT NOT NULL,
            period TEXT,
            teacher_name TEXT,
            room TEXT,
            current_grade TEXT,
            grade_percent REAL,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        );

        CREATE TABLE IF NOT EXISTS assignments (
            assignment_id TEXT PRIMARY KEY,
            course_id TEXT,
            assignment_name TEXT NOT NULL,
            category TEXT,
            due_date TEXT,
            score TEXT,
            points_possible REAL,
            status TEXT,
            FOREIGN KEY (course_id) REFERENCES courses(course_id)
        );

        CREATE TABLE IF NOT EXISTS attendance_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            term TEXT,
            days_present INTEGER,
            days_absent INTEGER,
            tardies INTEGER,
            attendance_rate REAL,
            as_of_date TEXT,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        );

        CREATE TABLE IF NOT EXISTS attendance_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            date TEXT,
            period TEXT,
            status TEXT,
            code TEXT,
            course_name TEXT,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        );
    """)

    conn.commit()
    conn.close()

    yield db_path


@pytest.fixture(scope="session")
def sample_assignment_html() -> str:
    """Sample HTML for assignment parsing tests."""
    return """
    <table class="grid assignments">
        <tr>
            <td class="assignmentName">Atomic Structure Knowledge Check</td>
            <td class="category">Assessment</td>
            <td class="dueDate">12/15/2024</td>
            <td class="score">--</td>
            <td class="status missing">Missing</td>
        </tr>
        <tr>
            <td class="assignmentName">Chapter 5 Quiz</td>
            <td class="category">Quiz</td>
            <td class="dueDate">12/10/2024</td>
            <td class="score">85/100</td>
            <td class="status">Graded</td>
        </tr>
    </table>
    """


@pytest.fixture(scope="session")
def sample_attendance_html() -> str:
    """Sample HTML for attendance parsing tests."""
    return """
    <div class="attendance-summary">
        <div class="stat">
            <span class="label">Attendance Rate</span>
            <span class="value">88.60%</span>
        </div>
        <div class="stat">
            <span class="label">Days Present</span>
            <span class="value">70</span>
        </div>
        <div class="stat">
            <span class="label">Days Absent</span>
            <span class="value">9</span>
        </div>
        <div class="stat">
            <span class="label">Tardies</span>
            <span class="value">2</span>
        </div>
    </div>
    """


# Ground truth data for validation - configure via environment variables
# Real values should be set in .env file (not committed to git)
GROUND_TRUTH = {
    "student_name": os.getenv("GROUND_TRUTH_STUDENT_NAME", "Test Student"),
    "grade_level": int(os.getenv("GROUND_TRUTH_GRADE_LEVEL", "6")),
    "missing_assignments": [
        # Example placeholder assignments
        {"course": "Science", "name": "Knowledge Check"},
        {"course": "Social Studies", "name": "Assignment"},
    ],
    "attendance_rate": float(os.getenv("GROUND_TRUTH_ATTENDANCE_RATE", "90.0")),
    "days_present": int(os.getenv("GROUND_TRUTH_DAYS_PRESENT", "70")),
    "days_absent": int(os.getenv("GROUND_TRUTH_DAYS_ABSENT", "5")),
    "tardies": int(os.getenv("GROUND_TRUTH_TARDIES", "2")),
    "expected_courses_min": int(os.getenv("GROUND_TRUTH_COURSES_MIN", "8")),
}


@pytest.fixture(scope="session")
def ground_truth() -> dict:
    """Provide ground truth data for validation."""
    return GROUND_TRUTH


# =============================================================================
# Streamlit UI Test Fixtures
# =============================================================================

STREAMLIT_PORT = 8503  # Avoid conflict with dev server on 8501/8502


@pytest.fixture(scope="session")
def streamlit_server(project_root: Path) -> Generator[str, None, None]:
    """Start Streamlit server for UI tests.

    Yields the base URL of the running server.
    """
    app_path = project_root / "streamlit-chat" / "app.py"
    db_path = project_root / "powerschool.db"

    # Set environment for the subprocess
    env = os.environ.copy()
    env["DATABASE_PATH"] = str(db_path)

    # Start Streamlit server
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(app_path),
            "--server.port",
            str(STREAMLIT_PORT),
            "--server.headless",
            "true",
            "--server.runOnSave",
            "false",
            "--browser.gatherUsageStats",
            "false",
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    base_url = f"http://localhost:{STREAMLIT_PORT}"

    # Wait for server to start (15s timeout)
    for _ in range(30):
        try:
            response = requests.get(f"{base_url}/_stcore/health", timeout=1)
            if response.status_code == 200:
                break
        except Exception:
            time.sleep(0.5)
    else:
        proc.terminate()
        proc.wait()
        pytest.fail("Streamlit server failed to start")

    yield base_url

    # Cleanup
    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture(scope="session")
def browser() -> Generator[Browser, None, None]:
    """Launch browser for UI tests."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def streamlit_page(browser: Browser, streamlit_server: str) -> Generator[Page, None, None]:
    """Provide a page navigated to the Streamlit app.

    This is the main fixture tests should use.
    """
    context = browser.new_context(viewport={"width": 1280, "height": 720})
    page = context.new_page()

    # Navigate to app
    page.goto(streamlit_server)

    # Wait for Streamlit to finish loading
    page.wait_for_selector('[data-testid="stApp"]', timeout=10000)
    page.wait_for_load_state("networkidle")

    yield page

    context.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Store test result for screenshot fixture."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(autouse=True)
def screenshot_on_failure(request, streamlit_page: Page = None):
    """Capture screenshot on test failure for UI tests."""
    yield

    # Only capture for UI tests that use streamlit_page
    if streamlit_page is None:
        return

    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        screenshots_dir = Path("reports/screenshots")
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        test_name = request.node.name.replace("/", "_").replace("::", "_")
        streamlit_page.screenshot(path=str(screenshots_dir / f"{test_name}.png"), full_page=True)
