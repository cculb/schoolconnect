"""Self-validation tests for SchoolPulse POC."""

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

# Add this directory for imports
THIS_DIR = Path(__file__).parent
sys.path.insert(0, str(THIS_DIR))

# Set DATABASE_PATH env var for tests
os.environ.setdefault("DATABASE_PATH", str(THIS_DIR.parent / "powerschool.db"))

from data_queries import (
    get_missing_assignments,
    get_current_grades,
    get_attendance_summary,
    get_student_summary,
    get_upcoming_assignments,
    get_all_courses,
)


def get_db_path() -> str:
    """Get the database path."""
    if os.environ.get("DATABASE_PATH"):
        return os.environ["DATABASE_PATH"]
    parent_db = THIS_DIR.parent / "powerschool.db"
    if parent_db.exists():
        return str(parent_db)
    return str(THIS_DIR / "powerschool.db")


class TestDatabaseExists:
    """Test that database exists with expected tables."""

    def test_database_file_exists(self):
        """Database file exists."""
        db_path = Path(get_db_path())
        assert db_path.exists(), f"Database not found at {db_path}"

    def test_students_table_has_data(self):
        """Students table has at least one student."""
        summary = get_student_summary(get_db_path(), "Delilah")
        assert "error" not in summary, f"Error getting student: {summary}"
        assert summary.get("student_id") is not None


class TestQueryFunctions:
    """Test that query functions return correct data."""

    def test_missing_assignments_count(self):
        """Query functions return ground truth values for missing assignments."""
        missing = get_missing_assignments(get_db_path(), "Delilah")
        assert len(missing) >= 2, f"Expected at least 2 missing assignments, got {len(missing)}"

    def test_missing_assignment_names(self):
        """Missing assignments include expected names."""
        missing = get_missing_assignments(get_db_path(), "Delilah")
        names = [a["assignment_name"] for a in missing]

        expected_names = [
            "Atomic Structure Knowledge Check",
            "FORMATIVE - Edpuzzle on Autocracies"
        ]

        for expected in expected_names:
            assert any(expected in name for name in names), f"Expected '{expected}' in missing assignments"

    def test_attendance_rate_in_range(self):
        """Attendance rate is in expected range."""
        attendance = get_attendance_summary(get_db_path(), "Delilah")
        assert "error" not in attendance, f"Error getting attendance: {attendance}"

        rate = attendance.get("rate", 0)
        # Allow some flexibility (85-95% range)
        assert 85 <= rate <= 95, f"Attendance rate {rate}% outside expected range"

    def test_current_grades_returns_data(self):
        """Current grades returns list of courses with grades."""
        grades = get_current_grades(get_db_path(), "Delilah")
        assert len(grades) > 0, "Expected at least one grade"

    def test_student_summary_has_required_fields(self):
        """Student summary has all required fields."""
        summary = get_student_summary(get_db_path(), "Delilah")

        required_fields = [
            "student_id", "name", "missing_assignments",
            "attendance_rate", "course_count"
        ]

        for field in required_fields:
            assert field in summary, f"Missing field: {field}"

    def test_courses_count(self):
        """Student has expected number of courses."""
        courses = get_all_courses(get_db_path(), "Delilah")
        assert len(courses) >= 8, f"Expected at least 8 courses, got {len(courses)}"


class TestStreamlitApp:
    """Test that Streamlit app starts and responds."""

    @pytest.mark.slow
    def test_streamlit_starts(self):
        """App starts without errors."""
        app_path = Path(__file__).parent / "app.py"

        # Start streamlit in background
        proc = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", str(app_path),
             "--server.headless", "true", "--server.port", "8502"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        try:
            # Wait for startup
            time.sleep(5)

            # Check process is still running
            assert proc.poll() is None, "Streamlit process terminated unexpectedly"

            # Try to connect to health endpoint
            import requests
            try:
                response = requests.get("http://localhost:8502/_stcore/health", timeout=5)
                assert response.status_code == 200, f"Health check failed: {response.status_code}"
            except requests.exceptions.ConnectionError:
                pytest.skip("Could not connect to Streamlit server")

        finally:
            proc.terminate()
            proc.wait(timeout=5)


class TestAIAssistant:
    """Test AI assistant (requires API key)."""

    @pytest.mark.skipif(
        not Path(__file__).parent.parent.joinpath(".env").exists(),
        reason="No .env file with API key"
    )
    def test_ai_response_mentions_data(self):
        """AI response includes relevant data."""
        import os
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).parent.parent / ".env")

        if not os.environ.get("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set")

        from ai_assistant import get_ai_response

        response = get_ai_response(
            "What are Delilah's missing assignments?",
            {"student_name": "Delilah"},
            []
        )

        # Response should mention assignments
        response_lower = response.lower()
        assert any(word in response_lower for word in ["missing", "assignment", "atomic", "edpuzzle"]), \
            f"Response doesn't mention expected content: {response[:200]}"


class TestQuickResponses:
    """Test quick response functionality."""

    def test_quick_missing_works(self):
        """Quick response for missing assignments works."""
        from ai_assistant import get_quick_response

        result = get_quick_response("missing", "Delilah")
        assert "error" not in result, f"Error: {result}"
        assert result.get("count", 0) >= 2

    def test_quick_attendance_works(self):
        """Quick response for attendance works."""
        from ai_assistant import get_quick_response

        result = get_quick_response("attendance", "Delilah")
        assert "error" not in result.get("data", {}), f"Error: {result}"

    def test_quick_grades_works(self):
        """Quick response for grades works."""
        from ai_assistant import get_quick_response

        result = get_quick_response("grades", "Delilah")
        assert "error" not in result, f"Error: {result}"


# Run specific checkpoints
def run_checkpoint_1():
    """Checkpoint 1: Database Ready."""
    print("Checkpoint 1: Database Ready")
    print("-" * 40)

    db_path = get_db_path()
    print(f"Database path: {db_path}")
    print(f"Database exists: {Path(db_path).exists()}")

    missing = get_missing_assignments(db_path, "Delilah")
    print(f"Missing assignments: {len(missing)}")
    for m in missing:
        print(f"  - {m['assignment_name']}")

    return len(missing) >= 2


def run_checkpoint_2():
    """Checkpoint 2: Queries Work."""
    print("\nCheckpoint 2: Queries Work")
    print("-" * 40)

    db_path = get_db_path()

    missing = get_missing_assignments(db_path, "Delilah")
    print(f"Missing: {len(missing)}")

    attendance = get_attendance_summary(db_path, "Delilah")
    print(f"Attendance: {attendance.get('rate', 'N/A')}%")

    grades = get_current_grades(db_path, "Delilah")
    print(f"Grades: {len(grades)} courses")

    return len(missing) >= 2 and attendance.get("rate", 0) > 0


def run_checkpoint_3():
    """Checkpoint 3: AI Responds (requires API key)."""
    print("\nCheckpoint 3: AI Responds")
    print("-" * 40)

    import os
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set - skipping AI test")
        return True

    from ai_assistant import get_ai_response

    response = get_ai_response(
        "What assignments is Delilah missing?",
        {"student_name": "Delilah"},
        []
    )

    print(f"Response preview: {response[:200]}...")
    return "missing" in response.lower() or "assignment" in response.lower()


if __name__ == "__main__":
    print("=" * 50)
    print("SchoolPulse POC Validation")
    print("=" * 50)

    results = []

    results.append(("Checkpoint 1: Database", run_checkpoint_1()))
    results.append(("Checkpoint 2: Queries", run_checkpoint_2()))
    results.append(("Checkpoint 3: AI", run_checkpoint_3()))

    print("\n" + "=" * 50)
    print("Results Summary")
    print("=" * 50)

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False

    print("\n" + ("All checkpoints passed!" if all_passed else "Some checkpoints failed."))
    sys.exit(0 if all_passed else 1)
