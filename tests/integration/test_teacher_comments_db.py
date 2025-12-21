"""Integration tests for teacher comments database operations.

These tests verify the repository methods and database views work
correctly with actual SQLite operations.
"""

import sqlite3
from pathlib import Path
from typing import Generator

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture(scope="function")
def test_db(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary database with schema and test data."""
    db_path = tmp_path / "test_teacher_comments.db"

    # Read schema from project
    schema_path = Path(__file__).parent.parent.parent / "src" / "database" / "schema.sql"
    views_path = Path(__file__).parent.parent.parent / "src" / "database" / "views.sql"

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Create schema
    if schema_path.exists():
        with open(schema_path) as f:
            conn.executescript(f.read())

    # Create views
    if views_path.exists():
        with open(views_path) as f:
            conn.executescript(f.read())

    # Insert test student
    conn.execute(
        """
        INSERT INTO students (id, powerschool_id, first_name, last_name, grade_level, school_name)
        VALUES (1, '12345', 'Test', 'Student', '6', 'Test Middle School')
        """
    )

    # Insert test courses
    conn.execute(
        """
        INSERT INTO courses (id, student_id, course_name, expression, teacher_name, teacher_email)
        VALUES (1, 1, 'Mathematics (grade 6)', '1/6(A-B)', 'Smith, John', 'john.smith@school.net')
        """
    )
    conn.execute(
        """
        INSERT INTO courses (id, student_id, course_name, expression, teacher_name, teacher_email)
        VALUES (2, 1, 'Language Arts (grade 6)', '2/6(A-B)', 'Jones, Mary', 'mary.jones@school.net')
        """
    )
    conn.execute(
        """
        INSERT INTO courses (id, student_id, course_name, expression, teacher_name, teacher_email)
        VALUES (3, 1, 'Science (grade 6)', '3/6(A-B)', 'Miller, Stephen', 'stephen.miller@school.net')
        """
    )

    # Insert test teacher comments
    test_comments = [
        # Q1 comments
        (
            1,
            None,
            "Mathematics (grade 6)",
            "52036",
            "1/6(A-B)",
            "Smith, John",
            "john.smith@school.net",
            "Q1",
            "Excellent progress in algebra this quarter!",
        ),
        (
            1,
            None,
            "Language Arts (grade 6)",
            "51034",
            "2/6(A-B)",
            "Jones, Mary",
            "mary.jones@school.net",
            "Q1",
            "Great participation in class discussions.",
        ),
        (
            1,
            None,
            "Science (grade 6)",
            "53001",
            "3/6(A-B)",
            "Miller, Stephen",
            "stephen.miller@school.net",
            "Q1",
            "Needs to improve lab report writing.",
        ),
        # Q2 comments
        (
            1,
            None,
            "Mathematics (grade 6)",
            "52036",
            "1/6(A-B)",
            "Smith, John",
            "john.smith@school.net",
            "Q2",
            "Continued growth in problem solving skills.",
        ),
        (
            1,
            None,
            "Language Arts (grade 6)",
            "51034",
            "2/6(A-B)",
            "Jones, Mary",
            "mary.jones@school.net",
            "Q2",
            "Reading comprehension has improved significantly.",
        ),
    ]

    for comment in test_comments:
        conn.execute(
            """
            INSERT INTO teacher_comments (
                student_id, course_id, course_name, course_number, expression,
                teacher_name, teacher_email, term, comment
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            comment,
        )

    conn.commit()
    conn.close()

    yield db_path


@pytest.fixture
def repo(test_db: Path):
    """Create repository instance with test database."""
    from src.database.repository import Repository

    return Repository(db_path=test_db)


class TestAddTeacherComment:
    """Tests for add_teacher_comment method."""

    def test_insert_new_comment(self, repo):
        """Inserting a new comment returns its ID."""
        comment_id = repo.add_teacher_comment(
            student_id=1,
            course_name="Social Studies (grade 6)",
            term="Q1",
            comment="Shows excellent understanding of historical concepts.",
            course_number="54436",
            expression="4/6(A-B)",
            teacher_name="Wilson, Bob",
            teacher_email="bob.wilson@school.net",
        )

        assert comment_id is not None
        assert comment_id > 0

    def test_upsert_duplicate_comment(self, repo):
        """Upserting duplicate comment updates existing record."""
        # First insert
        id1 = repo.add_teacher_comment(
            student_id=1,
            course_name="Social Studies",
            term="Q1",
            comment="Initial comment.",
            teacher_name="Teacher One",
        )

        # Same student, course, term, and comment - should update
        id2 = repo.add_teacher_comment(
            student_id=1,
            course_name="Social Studies",
            term="Q1",
            comment="Initial comment.",
            teacher_name="Teacher One Updated",
        )

        # Should return same ID (upsert)
        assert id1 == id2

    def test_different_terms_are_separate(self, repo):
        """Same course with different terms creates separate records."""
        id1 = repo.add_teacher_comment(
            student_id=1,
            course_name="Art",
            term="Q1",
            comment="Great creativity!",
        )
        id2 = repo.add_teacher_comment(
            student_id=1,
            course_name="Art",
            term="Q2",
            comment="Great creativity!",
        )

        assert id1 != id2


class TestGetTeacherComments:
    """Tests for get_teacher_comments method."""

    def test_returns_all_comments(self, repo):
        """Returns all teacher comments for a student."""
        comments = repo.get_teacher_comments(student_id=1)

        assert len(comments) == 5  # 3 Q1 + 2 Q2 comments

    def test_filter_by_term(self, repo):
        """Filtering by term works correctly."""
        comments = repo.get_teacher_comments(student_id=1, term="Q1")

        assert len(comments) == 3
        for c in comments:
            assert c["term"] == "Q1"

    def test_filter_by_course(self, repo):
        """Filtering by course name works correctly."""
        comments = repo.get_teacher_comments(student_id=1, course_name="Math")

        assert len(comments) == 2  # Q1 and Q2 math comments
        for c in comments:
            assert "Math" in c["course_name"]

    def test_filter_by_term_and_course(self, repo):
        """Filtering by both term and course works."""
        comments = repo.get_teacher_comments(student_id=1, course_name="Language", term="Q1")

        assert len(comments) == 1
        assert comments[0]["term"] == "Q1"
        assert "Language" in comments[0]["course_name"]

    def test_includes_all_fields(self, repo):
        """Comments include all required fields."""
        comments = repo.get_teacher_comments(student_id=1)

        required_fields = [
            "id",
            "student_id",
            "student_name",
            "course_name",
            "teacher_name",
            "term",
            "comment",
        ]

        assert len(comments) > 0
        for field in required_fields:
            assert field in comments[0], f"Missing field: {field}"

    def test_ordered_by_term_desc(self, repo):
        """Comments are ordered by term descending."""
        comments = repo.get_teacher_comments(student_id=1)

        terms = [c["term"] for c in comments]
        # Q2 should come before Q1
        q2_indices = [i for i, t in enumerate(terms) if t == "Q2"]
        q1_indices = [i for i, t in enumerate(terms) if t == "Q1"]

        # All Q2 should appear before Q1 (since ordered DESC)
        if q2_indices and q1_indices:
            assert max(q2_indices) < min(q1_indices)


class TestGetTeacherCommentsSummary:
    """Tests for get_teacher_comments_summary method."""

    def test_returns_summary_by_term(self, repo):
        """Returns summary grouped by term."""
        summary = repo.get_teacher_comments_summary(student_id=1)

        assert len(summary) == 2  # Q1 and Q2

    def test_counts_comments_correctly(self, repo):
        """Counts comments per term correctly."""
        summary = repo.get_teacher_comments_summary(student_id=1)

        # Find Q1 summary
        q1 = next((s for s in summary if s["term"] == "Q1"), None)
        assert q1 is not None
        assert q1["comment_count"] == 3

        # Find Q2 summary
        q2 = next((s for s in summary if s["term"] == "Q2"), None)
        assert q2 is not None
        assert q2["comment_count"] == 2


class TestClearTeacherComments:
    """Tests for clear_teacher_comments method."""

    def test_clears_all_comments(self, repo):
        """Clears all comments for a student."""
        # Verify comments exist
        before = repo.get_teacher_comments(student_id=1)
        assert len(before) > 0

        # Clear comments
        deleted = repo.clear_teacher_comments(student_id=1)

        # Verify cleared
        after = repo.get_teacher_comments(student_id=1)
        assert len(after) == 0
        assert deleted == len(before)

    def test_clears_by_term(self, repo):
        """Clears comments for a specific term only."""
        # Clear Q1 comments only
        deleted = repo.clear_teacher_comments(student_id=1, term="Q1")

        assert deleted == 3  # 3 Q1 comments

        # Q2 comments should remain
        remaining = repo.get_teacher_comments(student_id=1)
        assert len(remaining) == 2
        for c in remaining:
            assert c["term"] == "Q2"


class TestViewsExist:
    """Tests that required views exist and work."""

    def test_v_teacher_comments_view(self, test_db):
        """v_teacher_comments view exists and returns data."""
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("SELECT * FROM v_teacher_comments LIMIT 1")
        row = cursor.fetchone()

        assert row is not None
        assert "student_id" in row.keys()
        assert "student_name" in row.keys()
        assert "course_name" in row.keys()
        assert "teacher_name" in row.keys()
        assert "term" in row.keys()
        assert "comment" in row.keys()

        conn.close()

    def test_v_teacher_comments_by_term_view(self, test_db):
        """v_teacher_comments_by_term view exists and returns data."""
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("SELECT * FROM v_teacher_comments_by_term LIMIT 1")
        row = cursor.fetchone()

        assert row is not None
        assert "student_id" in row.keys()
        assert "term" in row.keys()
        assert "comment_count" in row.keys()
        assert "courses_with_comments" in row.keys()

        conn.close()


class TestTeacherCommentsFromParser:
    """Tests for storing parsed comments in the database."""

    def test_store_parsed_comments(self, repo):
        """Parsed comments can be stored in database."""
        from src.scraper.parsers.teacher_comments import parse_teacher_comments

        html = """
        <table class="grid linkDescList">
        <tbody><tr><th>Exp.</th><th>Course #</th><th>Course</th><th>Teacher</th><th>Comment</th></tr>
        <tr>
            <td>5/6(A-B)</td>
            <td>99999</td>
            <td>Test Course</td>
            <td><a href="mailto:test@school.net">Email Teacher, Test</a></td>
            <td><pre>This is a test comment from parsing.</pre></td>
        </tr>
        </tbody></table>
        """

        comments = parse_teacher_comments(html, comments_only=True)
        assert len(comments) == 1

        # Store in database
        for c in comments:
            comment_id = repo.add_teacher_comment(
                student_id=1,
                course_name=c["course_name"],
                term="Q3",  # Simulating Q3 scrape
                comment=c["comment"],
                course_number=c.get("course_number"),
                expression=c.get("expression"),
                teacher_name=c.get("teacher_name"),
                teacher_email=c.get("teacher_email"),
            )
            assert comment_id is not None

        # Verify stored
        stored = repo.get_teacher_comments(student_id=1, term="Q3")
        assert len(stored) == 1
        assert stored[0]["course_name"] == "Test Course"
        assert "test comment" in stored[0]["comment"]
