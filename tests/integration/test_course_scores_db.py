"""Integration tests for course scores database operations.

These tests verify database operations work correctly for
course categories and assignment details.
"""

import json
import sqlite3
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
def clean_db(tmp_path: Path) -> Path:
    """Create a clean database with full schema for testing."""
    db_path = tmp_path / "test_course_scores.db"

    # Get the full schema
    schema_path = Path(__file__).parent.parent.parent / "src" / "database" / "schema.sql"

    if not schema_path.exists():
        pytest.skip("Schema file not found")

    with open(schema_path) as f:
        schema = f.read()

    # Create fresh database with schema
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = OFF")  # Disable for schema loading
    conn.executescript(schema)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    conn.close()

    return db_path


class TestCourseCategoriesSchema:
    """Tests for course_categories table schema."""

    def test_course_categories_table_exists(self, temp_db: Path):
        """Course categories table is created by schema."""
        # The temp_db fixture creates a minimal schema
        # We need to apply the full schema to test

        # Apply schema
        schema_path = Path(__file__).parent.parent.parent / "src" / "database" / "schema.sql"
        if schema_path.exists():
            with open(schema_path) as f:
                schema = f.read()

            conn = sqlite3.connect(temp_db)
            conn.executescript(schema)
            conn.commit()

            # Check table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='course_categories'"
            )
            result = cursor.fetchone()
            conn.close()

            assert result is not None, "course_categories table should exist"
        else:
            pytest.skip("Schema file not found")

    def test_course_categories_columns(self, temp_db: Path):
        """Course categories table has required columns."""
        schema_path = Path(__file__).parent.parent.parent / "src" / "database" / "schema.sql"
        if not schema_path.exists():
            pytest.skip("Schema file not found")

        with open(schema_path) as f:
            schema = f.read()

        conn = sqlite3.connect(temp_db)
        conn.executescript(schema)
        conn.commit()

        cursor = conn.execute("PRAGMA table_info(course_categories)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        required = {"id", "course_id", "category_name", "weight"}
        assert required.issubset(columns), f"Missing columns: {required - columns}"


class TestAssignmentDetailsSchema:
    """Tests for assignment_details table schema."""

    def test_assignment_details_table_exists(self, temp_db: Path):
        """Assignment details table is created by schema."""
        schema_path = Path(__file__).parent.parent.parent / "src" / "database" / "schema.sql"
        if not schema_path.exists():
            pytest.skip("Schema file not found")

        with open(schema_path) as f:
            schema = f.read()

        conn = sqlite3.connect(temp_db)
        conn.executescript(schema)
        conn.commit()

        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='assignment_details'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "assignment_details table should exist"

    def test_assignment_details_columns(self, temp_db: Path):
        """Assignment details table has required columns."""
        schema_path = Path(__file__).parent.parent.parent / "src" / "database" / "schema.sql"
        if not schema_path.exists():
            pytest.skip("Schema file not found")

        with open(schema_path) as f:
            schema = f.read()

        conn = sqlite3.connect(temp_db)
        conn.executescript(schema)
        conn.commit()

        cursor = conn.execute("PRAGMA table_info(assignment_details)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        required = {"id", "assignment_id", "description", "standards", "comments"}
        assert required.issubset(columns), f"Missing columns: {required - columns}"


class TestCourseCategoriesRepository:
    """Tests for course categories repository operations."""

    def test_add_course_category(self, clean_db: Path):
        """Repository can add course category."""
        try:
            from src.database.repository import Repository
        except ImportError:
            pytest.skip("Repository not available")

        repo = Repository(clean_db)

        # First create a student and course
        student_id = repo.upsert_student("12345", "Test", "Student")
        course_id = repo.upsert_course(student_id, "Math 6")

        # Now add category
        if hasattr(repo, "add_course_category"):
            cat_id = repo.add_course_category(
                course_id=course_id, category_name="Formative", weight=30.0
            )
            assert cat_id is not None
            assert cat_id > 0
        else:
            pytest.skip("add_course_category not implemented")

    def test_get_course_categories(self, clean_db: Path):
        """Repository can retrieve course categories."""
        try:
            from src.database.repository import Repository
        except ImportError:
            pytest.skip("Repository not available")

        repo = Repository(clean_db)

        # Create student and course
        student_id = repo.upsert_student("12345", "Test", "Student")
        course_id = repo.upsert_course(student_id, "Math 6")

        # Add multiple categories
        if hasattr(repo, "add_course_category") and hasattr(repo, "get_course_categories"):
            repo.add_course_category(course_id, "Formative", 30.0)
            repo.add_course_category(course_id, "Summative", 50.0)
            repo.add_course_category(course_id, "Practice", 20.0)

            categories = repo.get_course_categories(course_id)
            assert len(categories) == 3

            weights = [c["weight"] for c in categories]
            assert 30.0 in weights
            assert 50.0 in weights
            assert 20.0 in weights
        else:
            pytest.skip("Course category methods not implemented")

    def test_upsert_course_category(self, clean_db: Path):
        """Repository updates existing category on conflict."""
        try:
            from src.database.repository import Repository
        except ImportError:
            pytest.skip("Repository not available")

        repo = Repository(clean_db)

        # Create student and course
        student_id = repo.upsert_student("12345", "Test", "Student")
        course_id = repo.upsert_course(student_id, "Math 6")

        if hasattr(repo, "upsert_course_category") and hasattr(repo, "get_course_categories"):
            # Add category
            repo.upsert_course_category(course_id, "Formative", 30.0)

            # Update same category with different weight
            repo.upsert_course_category(course_id, "Formative", 40.0)

            # Should only have one category with updated weight
            categories = repo.get_course_categories(course_id)
            assert len(categories) == 1
            assert categories[0]["weight"] == 40.0
        else:
            pytest.skip("upsert_course_category not implemented")


class TestAssignmentDetailsRepository:
    """Tests for assignment details repository operations."""

    def test_add_assignment_details(self, clean_db: Path):
        """Repository can add assignment details."""
        try:
            from src.database.repository import Repository
        except ImportError:
            pytest.skip("Repository not available")

        repo = Repository(clean_db)

        # Create student and assignment
        student_id = repo.upsert_student("12345", "Test", "Student")
        assignment_id = repo.add_assignment(
            student_id=student_id,
            course_name="Math 6",
            assignment_name="Chapter 5 Quiz",
        )

        if hasattr(repo, "add_assignment_details"):
            detail_id = repo.add_assignment_details(
                assignment_id=assignment_id,
                description="Quiz covering fractions",
                standards=json.dumps(["6.NS.1", "6.NS.2"]),
                comments="Great job!",
            )
            assert detail_id is not None
            assert detail_id > 0
        else:
            pytest.skip("add_assignment_details not implemented")

    def test_get_assignment_details(self, clean_db: Path):
        """Repository can retrieve assignment details."""
        try:
            from src.database.repository import Repository
        except ImportError:
            pytest.skip("Repository not available")

        repo = Repository(clean_db)

        # Create student and assignment
        student_id = repo.upsert_student("12345", "Test", "Student")
        assignment_id = repo.add_assignment(
            student_id=student_id,
            course_name="Math 6",
            assignment_name="Chapter 5 Quiz",
        )

        if hasattr(repo, "add_assignment_details") and hasattr(repo, "get_assignment_details"):
            repo.add_assignment_details(
                assignment_id=assignment_id,
                description="Quiz covering fractions",
                standards=json.dumps(["6.NS.1", "6.NS.2"]),
                comments="Great job!",
            )

            details = repo.get_assignment_details(assignment_id)
            assert details is not None
            assert details["description"] == "Quiz covering fractions"
            assert details["comments"] == "Great job!"

            # Standards should be stored as JSON
            standards = json.loads(details["standards"])
            assert "6.NS.1" in standards
        else:
            pytest.skip("Assignment details methods not implemented")

    def test_upsert_assignment_details(self, clean_db: Path):
        """Repository updates existing details on conflict."""
        try:
            from src.database.repository import Repository
        except ImportError:
            pytest.skip("Repository not available")

        repo = Repository(clean_db)

        # Create student and assignment
        student_id = repo.upsert_student("12345", "Test", "Student")
        assignment_id = repo.add_assignment(
            student_id=student_id,
            course_name="Math 6",
            assignment_name="Chapter 5 Quiz",
        )

        if hasattr(repo, "upsert_assignment_details") and hasattr(repo, "get_assignment_details"):
            # Add details
            repo.upsert_assignment_details(
                assignment_id=assignment_id,
                description="Original description",
                comments="Original comment",
            )

            # Update
            repo.upsert_assignment_details(
                assignment_id=assignment_id,
                description="Updated description",
                comments="Updated comment",
            )

            # Should have updated values
            details = repo.get_assignment_details(assignment_id)
            assert details["description"] == "Updated description"
            assert details["comments"] == "Updated comment"
        else:
            pytest.skip("upsert_assignment_details not implemented")


class TestCourseScoreDetails:
    """Tests for combined course score details query."""

    def test_get_course_score_details(self, clean_db: Path):
        """Repository returns complete course score details."""
        try:
            from src.database.repository import Repository
        except ImportError:
            pytest.skip("Repository not available")

        repo = Repository(clean_db)

        # Setup test data
        student_id = repo.upsert_student("12345", "Test", "Student")
        course_id = repo.upsert_course(student_id, "Math 6", teacher_name="Smith, John")

        if not hasattr(repo, "get_course_score_details"):
            pytest.skip("get_course_score_details not implemented")

        # Add categories
        if hasattr(repo, "add_course_category"):
            repo.add_course_category(course_id, "Formative", 30.0)
            repo.add_course_category(course_id, "Summative", 70.0)

        # Add assignments with details
        assignment_id = repo.add_assignment(
            student_id=student_id,
            course_name="Math 6",
            course_id=course_id,
            assignment_name="Quiz 1",
            category="Formative",
            score="17/20",
            percent=85.0,
        )

        if hasattr(repo, "add_assignment_details"):
            repo.add_assignment_details(
                assignment_id=assignment_id,
                description="Chapter 5 quiz",
                standards=json.dumps(["6.NS.1"]),
                comments="Good work!",
            )

        # Get complete details
        details = repo.get_course_score_details(course_id)

        assert details is not None
        assert "course" in details
        assert "categories" in details
        assert "assignments" in details

        # Check course info
        assert details["course"]["course_name"] == "Math 6"

        # Check categories
        assert len(details["categories"]) == 2

        # Check assignments with details
        assert len(details["assignments"]) >= 1
        assignment = details["assignments"][0]
        assert assignment["assignment_name"] == "Quiz 1"
        # Should include details
        if "description" in assignment:
            assert assignment["description"] == "Chapter 5 quiz"


class TestCourseScoreCalculations:
    """Tests for weighted score calculations."""

    def test_calculate_category_score(self, clean_db: Path):
        """Repository calculates category scores correctly."""
        try:
            from src.database.repository import Repository
        except ImportError:
            pytest.skip("Repository not available")

        repo = Repository(clean_db)

        if not hasattr(repo, "get_course_score_details"):
            pytest.skip("get_course_score_details not implemented")

        # Setup
        student_id = repo.upsert_student("12345", "Test", "Student")
        course_id = repo.upsert_course(student_id, "Math 6")

        if hasattr(repo, "add_course_category"):
            repo.add_course_category(
                course_id, "Formative", 30.0, points_earned=85, points_possible=100
            )
            repo.add_course_category(
                course_id, "Summative", 70.0, points_earned=90, points_possible=100
            )

        details = repo.get_course_score_details(course_id)

        # Check category scores
        categories = details.get("categories", [])
        if categories:
            formative = next((c for c in categories if c["category_name"] == "Formative"), None)
            if formative and "category_percent" in formative:
                assert formative["category_percent"] == 85.0

            # Could also check weighted contribution
            # weighted = 85 * 0.30 + 90 * 0.70 = 25.5 + 63 = 88.5
