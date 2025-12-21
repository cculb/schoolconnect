"""Pytest fixtures for Streamlit chat application tests.

Provides:
- Test database with known data (no dependency on real data)
- Mock AI responses for testing without API keys
- Session state fixtures for Streamlit testing
- Portable test data from JSON fixtures

Addresses:
- HIGH-5: Proper test fixtures and mocking (no dependency on real data)
"""

import json
import sqlite3
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

# Path to portable test data
FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures"
TEST_DATA_PATH = FIXTURES_DIR / "test_student_data.json"

pytestmark = pytest.mark.unit


# =============================================================================
# Test Data Loading
# =============================================================================


def load_test_data() -> dict:
    """Load test data from JSON fixture file."""
    if TEST_DATA_PATH.exists():
        with open(TEST_DATA_PATH) as f:
            return json.load(f)
    # Fallback minimal test data
    return {
        "students": [
            {
                "powerschool_id": "TEST001",
                "first_name": "TestStudent",
                "last_name": "Smith",
                "grade_level": "6",
                "school_name": "Test School",
                "is_primary": True,
                "attendance": {
                    "term": "YTD",
                    "attendance_rate": 88.6,
                    "days_present": 61,
                    "days_absent": 9,
                    "tardies": 2,
                    "total_days": 70,
                },
                "courses": [],
                "assignments": [],
            }
        ],
        "expected_values": {
            "primary_student": {
                "name": "TestStudent Smith",
                "first_name": "TestStudent",
                "missing_count": 0,
                "course_count": 0,
                "attendance_rate": 88.6,
            }
        },
        "mock_ai_responses": {
            "generic": "Test response from AI.",
        },
    }


@pytest.fixture(scope="session")
def test_data() -> dict:
    """Provide test data from JSON fixture."""
    return load_test_data()


@pytest.fixture(scope="session")
def primary_student(test_data: dict) -> dict:
    """Get the primary test student data."""
    for student in test_data["students"]:
        if student.get("is_primary", False):
            return student
    return test_data["students"][0] if test_data["students"] else {}


@pytest.fixture(scope="session")
def expected_values(test_data: dict) -> dict:
    """Get expected test values."""
    return test_data.get("expected_values", {})


@pytest.fixture(scope="session")
def mock_ai_responses(test_data: dict) -> dict:
    """Get mock AI responses for testing."""
    return test_data.get("mock_ai_responses", {})


# =============================================================================
# Test Database Fixtures
# =============================================================================


def create_test_database_from_data(db_path: Path, test_data: dict) -> None:
    """Create a test database with data from test fixture."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create schema matching the real database
    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            powerschool_id TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT,
            grade_level TEXT,
            school_name TEXT DEFAULT 'Test School',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_name TEXT NOT NULL,
            expression TEXT,
            room TEXT,
            teacher_name TEXT,
            teacher_email TEXT,
            course_section TEXT,
            term TEXT,
            powerschool_frn TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        );

        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            term TEXT NOT NULL,
            letter_grade TEXT,
            percent REAL,
            gpa_points REAL,
            absences INTEGER DEFAULT 0,
            tardies INTEGER DEFAULT 0,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses(id),
            FOREIGN KEY (student_id) REFERENCES students(id)
        );

        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            student_id INTEGER NOT NULL,
            course_name TEXT NOT NULL,
            teacher_name TEXT,
            assignment_name TEXT NOT NULL,
            category TEXT,
            due_date DATE,
            score TEXT,
            max_score REAL,
            percent REAL,
            letter_grade TEXT,
            status TEXT DEFAULT 'Unknown',
            codes TEXT,
            term TEXT,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses(id),
            FOREIGN KEY (student_id) REFERENCES students(id)
        );

        CREATE TABLE IF NOT EXISTS attendance_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            term TEXT,
            attendance_rate REAL,
            days_present INTEGER DEFAULT 0,
            days_absent INTEGER DEFAULT 0,
            days_excused INTEGER DEFAULT 0,
            days_unexcused INTEGER DEFAULT 0,
            tardies INTEGER DEFAULT 0,
            total_days INTEGER DEFAULT 0,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id)
        );
    """
    )

    # Insert test data
    for student_data in test_data.get("students", []):
        cursor.execute(
            """
            INSERT INTO students (powerschool_id, first_name, last_name, grade_level, school_name)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                student_data["powerschool_id"],
                student_data["first_name"],
                student_data.get("last_name", ""),
                student_data.get("grade_level", ""),
                student_data.get("school_name", "Test School"),
            ),
        )
        student_id = cursor.lastrowid

        # Insert attendance
        attendance = student_data.get("attendance", {})
        if attendance:
            cursor.execute(
                """
                INSERT INTO attendance_summary
                (student_id, term, attendance_rate, days_present, days_absent, tardies, total_days)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    student_id,
                    attendance.get("term", "YTD"),
                    attendance.get("attendance_rate", 0),
                    attendance.get("days_present", 0),
                    attendance.get("days_absent", 0),
                    attendance.get("tardies", 0),
                    attendance.get("total_days", 0),
                ),
            )

        # Insert courses and grades
        for idx, course_data in enumerate(student_data.get("courses", []), 1):
            cursor.execute(
                """
                INSERT INTO courses
                (student_id, course_name, teacher_name, teacher_email, room, term)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    student_id,
                    course_data["name"],
                    course_data.get("teacher_name", ""),
                    course_data.get("teacher_email", ""),
                    course_data.get("room", ""),
                    course_data.get("term", "Q2"),
                ),
            )
            course_id = cursor.lastrowid

            # Insert grade if present
            grade = course_data.get("grade", {})
            if grade:
                cursor.execute(
                    """
                    INSERT INTO grades (course_id, student_id, term, letter_grade, percent)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        course_id,
                        student_id,
                        course_data.get("term", "Q2"),
                        grade.get("letter", ""),
                        grade.get("percent", 0),
                    ),
                )

        # Insert assignments
        for assignment in student_data.get("assignments", []):
            cursor.execute(
                """
                INSERT INTO assignments
                (student_id, course_name, teacher_name, assignment_name, category,
                 due_date, score, max_score, status, term)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    student_id,
                    assignment.get("course_name", ""),
                    assignment.get("teacher_name", ""),
                    assignment.get("assignment_name", ""),
                    assignment.get("category", ""),
                    assignment.get("due_date", ""),
                    assignment.get("score"),
                    assignment.get("max_score", 100),
                    assignment.get("status", "Unknown"),
                    assignment.get("term", "Q2"),
                ),
            )

    conn.commit()
    conn.close()


@pytest.fixture
def test_db(tmp_path: Path, test_data: dict) -> Generator[Path, None, None]:
    """Create a temporary test database with fixture data."""
    db_path = tmp_path / "test_powerschool.db"
    create_test_database_from_data(db_path, test_data)
    yield db_path


@pytest.fixture
def test_db_path(test_db: Path) -> str:
    """Get the test database path as a string."""
    return str(test_db)


@pytest.fixture
def empty_test_db(tmp_path: Path) -> Generator[Path, None, None]:
    """Create an empty test database (schema only, no data)."""
    db_path = tmp_path / "empty_test.db"
    create_test_database_from_data(db_path, {"students": []})
    yield db_path


# =============================================================================
# Mock Fixtures for AI Assistant
# =============================================================================


@pytest.fixture
def mock_anthropic_client(mock_ai_responses: dict):
    """Mock the Anthropic client for testing without API key.

    Returns a mock that simulates the Claude API response format.
    """
    mock_client = MagicMock()

    # Create a mock response structure
    mock_text_block = MagicMock()
    mock_text_block.type = "text"
    mock_text_block.text = mock_ai_responses.get(
        "generic", "This is a test response from the mock AI."
    )

    mock_response = MagicMock()
    mock_response.stop_reason = "end_turn"
    mock_response.content = [mock_text_block]

    mock_client.messages.create.return_value = mock_response

    return mock_client


@pytest.fixture
def mock_ai_assistant(mock_anthropic_client, mock_ai_responses: dict):
    """Provide a patched AI assistant module for testing.

    Patches the Anthropic client to return mock responses.
    """
    with patch("ai_assistant.Anthropic", return_value=mock_anthropic_client):
        yield mock_anthropic_client


@pytest.fixture
def mock_ai_response_missing(mock_ai_responses: dict) -> str:
    """Get mock AI response for missing assignments query."""
    return mock_ai_responses.get(
        "missing_assignments", "Student has missing assignments."
    )


@pytest.fixture
def mock_ai_response_attendance(mock_ai_responses: dict) -> str:
    """Get mock AI response for attendance query."""
    return mock_ai_responses.get("attendance", "Student attendance information.")


@pytest.fixture
def mock_ai_response_grades(mock_ai_responses: dict) -> str:
    """Get mock AI response for grades query."""
    return mock_ai_responses.get("grades", "Student grades information.")


# =============================================================================
# Streamlit Session State Fixtures
# =============================================================================


@pytest.fixture
def mock_session_state(primary_student: dict) -> dict:
    """Create a mock Streamlit session state for testing."""
    return {
        "authenticated": True,
        "username": "testuser",
        "student_name": primary_student.get("first_name", "TestStudent"),
        "messages": [],
        "api_key": "test-api-key",
        "selected_model": "claude-haiku-3-5-20241022",
    }


@pytest.fixture
def unauthenticated_session_state() -> dict:
    """Create a mock unauthenticated session state."""
    return {
        "authenticated": False,
        "username": None,
        "student_name": None,
        "messages": [],
    }


@pytest.fixture
def session_with_history(mock_session_state: dict) -> dict:
    """Create session state with existing chat history."""
    state = mock_session_state.copy()
    state["messages"] = [
        {"role": "user", "content": "What are the missing assignments?"},
        {"role": "assistant", "content": "Let me check the missing assignments..."},
        {"role": "user", "content": "What about attendance?"},
        {"role": "assistant", "content": "The attendance rate is 88.6%."},
    ]
    return state


# =============================================================================
# Parameterized Test Data
# =============================================================================


@pytest.fixture(
    params=[
        ("missing", "Missing Assignments"),
        ("grades", "Current Grades"),
        ("attendance", "Attendance Summary"),
        ("upcoming", "Due This Week"),
        ("summary", "Student Summary"),
    ]
)
def quick_response_types(request) -> tuple[str, str]:
    """Parameterized fixture for quick response type testing."""
    return request.param


@pytest.fixture(
    params=[
        "",  # Empty name
        "   ",  # Whitespace only
        "NonExistent",  # Student not in database
    ]
)
def invalid_student_names(request) -> str:
    """Parameterized fixture for invalid student name testing."""
    return request.param


@pytest.fixture(
    params=[
        "What are the missing assignments?",
        "How is my child doing in Math?",
        "What's the attendance rate?",
        "Can you show me the grades?",
        "Are there any upcoming assignments?",
    ]
)
def sample_user_queries(request) -> str:
    """Parameterized fixture for sample user queries."""
    return request.param
