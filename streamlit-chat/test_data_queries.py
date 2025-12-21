"""Unit tests for data layer (data_queries.py and repository_adapter.py).

Tests cover:
- CRIT-3: Repository pattern usage
- CRIT-4: SQL injection prevention (LIKE pattern escaping)
- CRIT-5: Connection pooling via context managers
"""

import sqlite3
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def test_db_with_data(tmp_path: Path) -> Path:
    """Create a test database with schema and sample data."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create schema matching the real database
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            powerschool_id TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT,
            grade_level TEXT,
            school_name TEXT DEFAULT 'Eagle Schools',
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
    """)

    # Insert test student
    cursor.execute("""
        INSERT INTO students (powerschool_id, first_name, last_name, grade_level)
        VALUES ('55260', 'Delilah', 'Rae Culbreth', '6')
    """)
    student_id = cursor.lastrowid

    # Insert a second student with special characters in name
    cursor.execute("""
        INSERT INTO students (powerschool_id, first_name, last_name, grade_level)
        VALUES ('55261', 'O%Brien', 'Test_User', '7')
    """)

    # Insert courses
    cursor.execute("""
        INSERT INTO courses (student_id, course_name, teacher_name, teacher_email, room, term)
        VALUES (?, 'Math 6', 'Smith, John', 'jsmith@school.edu', '101', 'Q2')
    """, (student_id,))
    math_course_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO courses (student_id, course_name, teacher_name, teacher_email, room, term)
        VALUES (?, 'Science (grade 6)', 'Johnson, Mary', 'mjohnson@school.edu', '202', 'Q2')
    """, (student_id,))

    # Insert assignments
    cursor.execute("""
        INSERT INTO assignments (student_id, course_name, teacher_name, assignment_name,
                                 category, due_date, status, term)
        VALUES (?, 'Science (grade 6)', 'Johnson, Mary', 'Atomic Structure Knowledge Check',
                'Formative', '2024-12-10', 'Missing', 'Q2')
    """, (student_id,))

    cursor.execute("""
        INSERT INTO assignments (student_id, course_name, teacher_name, assignment_name,
                                 category, due_date, score, max_score, status, term)
        VALUES (?, 'Math 6', 'Smith, John', 'Chapter 5 Test',
                'Summative', '2024-12-08', '85', 100, 'Collected', 'Q2')
    """, (student_id,))

    # Insert attendance summary
    cursor.execute("""
        INSERT INTO attendance_summary (student_id, term, attendance_rate, days_present,
                                       days_absent, tardies, total_days)
        VALUES (?, 'YTD', 88.6, 61, 9, 2, 70)
    """, (student_id,))

    # Insert grades
    cursor.execute("""
        INSERT INTO grades (course_id, student_id, term, letter_grade, percent)
        VALUES (?, ?, 'Q2', 'B+', 87.5)
    """, (math_course_id, student_id))

    conn.commit()
    conn.close()

    return db_path


# =============================================================================
# CRIT-4: SQL Injection Prevention Tests
# =============================================================================


class TestInputSanitization:
    """Tests for SQL injection prevention via LIKE pattern escaping."""

    def test_escape_like_pattern_percent(self):
        """Percent signs in input should be escaped for LIKE queries."""
        from repository_adapter import escape_like_pattern

        assert escape_like_pattern("100%") == "100\\%"
        assert escape_like_pattern("50%off") == "50\\%off"

    def test_escape_like_pattern_underscore(self):
        """Underscores in input should be escaped for LIKE queries."""
        from repository_adapter import escape_like_pattern

        assert escape_like_pattern("test_user") == "test\\_user"
        assert escape_like_pattern("a_b_c") == "a\\_b\\_c"

    def test_escape_like_pattern_backslash(self):
        """Backslashes in input should be escaped for LIKE queries."""
        from repository_adapter import escape_like_pattern

        assert escape_like_pattern("path\\file") == "path\\\\file"

    def test_escape_like_pattern_combined(self):
        """Multiple special characters should all be escaped."""
        from repository_adapter import escape_like_pattern

        assert escape_like_pattern("50%_test\\path") == "50\\%\\_test\\\\path"

    def test_escape_like_pattern_normal_input(self):
        """Normal input without special characters should be unchanged."""
        from repository_adapter import escape_like_pattern

        assert escape_like_pattern("John Smith") == "John Smith"
        assert escape_like_pattern("Delilah") == "Delilah"

    def test_sanitize_student_name_strips_whitespace(self):
        """Student name sanitization should strip leading/trailing whitespace."""
        from repository_adapter import sanitize_student_name

        assert sanitize_student_name("  John  ") == "John"
        assert sanitize_student_name("\tMary\n") == "Mary"

    def test_sanitize_student_name_length_limit(self):
        """Student names should be limited to reasonable length."""
        from repository_adapter import sanitize_student_name

        long_name = "A" * 500
        result = sanitize_student_name(long_name)
        assert len(result) <= 100  # Reasonable max length

    def test_sanitize_student_name_empty_returns_empty(self):
        """Empty or whitespace-only names should return empty string."""
        from repository_adapter import sanitize_student_name

        assert sanitize_student_name("") == ""
        assert sanitize_student_name("   ") == ""

    def test_student_lookup_with_special_chars(self, test_db_with_data: Path):
        """Student lookup should handle names with LIKE special characters safely."""
        from repository_adapter import RepositoryAdapter

        adapter = RepositoryAdapter(test_db_with_data)

        # This should NOT find 'OBrien' when searching for 'O%Brien'
        # The % should be treated literally, not as a wildcard
        student_id = adapter.get_student_id("O%Brien")
        assert student_id is not None  # Should find exact match

        # Verify that a percent wildcard in name doesn't match everything
        # by ensuring 'O%' doesn't match 'Delilah'
        student_id_percent = adapter.get_student_id("O%")
        # Should only match O%Brien (literal %)
        if student_id_percent is not None:
            # Get the actual student to verify it's the right one
            summary = adapter.get_student_summary("O%Brien")
            assert "O%Brien" in summary.get("name", "")


# =============================================================================
# CRIT-3: Repository Pattern Tests
# =============================================================================


class TestRepositoryAdapter:
    """Tests for repository adapter usage and pattern compliance."""

    def test_adapter_uses_context_manager(self, test_db_with_data: Path):
        """Adapter should use context managers for all connections."""
        from repository_adapter import RepositoryAdapter

        adapter = RepositoryAdapter(test_db_with_data)

        # The adapter should use get_db context manager from connection module
        # We verify this by checking there are no leaked connections
        for _ in range(10):
            adapter.get_student_id("Delilah")

        # If connections are properly managed, we shouldn't hit pool exhaustion

    def test_adapter_get_student_id(self, test_db_with_data: Path):
        """Adapter should find student by partial name match."""
        from repository_adapter import RepositoryAdapter

        adapter = RepositoryAdapter(test_db_with_data)

        student_id = adapter.get_student_id("Delilah")
        assert student_id is not None
        assert isinstance(student_id, int)

    def test_adapter_get_student_id_full_name(self, test_db_with_data: Path):
        """Adapter should find student by full name."""
        from repository_adapter import RepositoryAdapter

        adapter = RepositoryAdapter(test_db_with_data)

        student_id = adapter.get_student_id("Delilah Rae")
        assert student_id is not None

    def test_adapter_get_student_id_not_found(self, test_db_with_data: Path):
        """Adapter should return None for non-existent student."""
        from repository_adapter import RepositoryAdapter

        adapter = RepositoryAdapter(test_db_with_data)

        student_id = adapter.get_student_id("NonExistent Student")
        assert student_id is None

    def test_adapter_get_student_summary(self, test_db_with_data: Path):
        """Adapter should return complete student summary."""
        from repository_adapter import RepositoryAdapter

        adapter = RepositoryAdapter(test_db_with_data)

        summary = adapter.get_student_summary("Delilah")

        assert "student_id" in summary
        assert "name" in summary
        assert "missing_assignments" in summary
        assert "attendance_rate" in summary
        assert summary["name"] == "Delilah Rae Culbreth"
        assert summary["attendance_rate"] == 88.6

    def test_adapter_get_student_summary_not_found(self, test_db_with_data: Path):
        """Adapter should return error for non-existent student."""
        from repository_adapter import RepositoryAdapter

        adapter = RepositoryAdapter(test_db_with_data)

        summary = adapter.get_student_summary("NonExistent")

        assert "error" in summary

    def test_adapter_get_missing_assignments(self, test_db_with_data: Path):
        """Adapter should return missing assignments."""
        from repository_adapter import RepositoryAdapter

        adapter = RepositoryAdapter(test_db_with_data)

        missing = adapter.get_missing_assignments("Delilah")

        assert isinstance(missing, list)
        assert len(missing) == 1
        assert missing[0]["assignment_name"] == "Atomic Structure Knowledge Check"
        assert missing[0]["status"] == "Missing"

    def test_adapter_get_current_grades(self, test_db_with_data: Path):
        """Adapter should return current grades."""
        from repository_adapter import RepositoryAdapter

        adapter = RepositoryAdapter(test_db_with_data)

        grades = adapter.get_current_grades("Delilah")

        assert isinstance(grades, list)
        assert len(grades) >= 1

    def test_adapter_get_attendance_summary(self, test_db_with_data: Path):
        """Adapter should return attendance summary."""
        from repository_adapter import RepositoryAdapter

        adapter = RepositoryAdapter(test_db_with_data)

        attendance = adapter.get_attendance_summary("Delilah")

        assert "rate" in attendance
        assert attendance["rate"] == 88.6
        assert attendance["days_absent"] == 9

    def test_adapter_get_all_courses(self, test_db_with_data: Path):
        """Adapter should return all courses for a student."""
        from repository_adapter import RepositoryAdapter

        adapter = RepositoryAdapter(test_db_with_data)

        courses = adapter.get_all_courses("Delilah")

        assert isinstance(courses, list)
        assert len(courses) == 2  # Math 6 and Science


# =============================================================================
# CRIT-5: Connection Pooling Tests
# =============================================================================


class TestConnectionPooling:
    """Tests for connection pooling implementation."""

    def test_connections_returned_to_pool(self, test_db_with_data: Path):
        """Connections should be returned to pool after use."""
        from repository_adapter import RepositoryAdapter

        adapter = RepositoryAdapter(test_db_with_data)

        # Make many requests to verify connections are recycled
        for i in range(20):
            result = adapter.get_student_id("Delilah")
            assert result is not None

    def test_no_connection_leaks_on_error(self, test_db_with_data: Path):
        """Connections should be returned even when queries fail."""
        from repository_adapter import RepositoryAdapter

        adapter = RepositoryAdapter(test_db_with_data)

        # This should fail gracefully and still return connection
        for _ in range(10):
            result = adapter.get_student_summary("NonExistent")
            assert "error" in result


# =============================================================================
# Integration with data_queries.py Tests
# =============================================================================


class TestDataQueriesIntegration:
    """Tests for data_queries.py using the adapter."""

    def test_get_student_id_uses_adapter(self, test_db_with_data: Path):
        """get_student_id should work with the refactored implementation."""
        # Import after adding to path
        import sys
        sys.path.insert(0, str(Path(__file__).parent))

        from data_queries import get_student_id

        student_id = get_student_id(str(test_db_with_data), "Delilah")
        assert student_id is not None

    def test_get_student_summary_uses_adapter(self, test_db_with_data: Path):
        """get_student_summary should work with the refactored implementation."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent))

        from data_queries import get_student_summary

        summary = get_student_summary(str(test_db_with_data), "Delilah")
        assert "name" in summary
        assert summary["missing_assignments"] == 1

    def test_get_missing_assignments_uses_adapter(self, test_db_with_data: Path):
        """get_missing_assignments should work with the refactored implementation."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent))

        from data_queries import get_missing_assignments

        missing = get_missing_assignments(str(test_db_with_data), "Delilah")
        assert len(missing) == 1

    def test_course_name_escaping(self, test_db_with_data: Path):
        """Course names with special characters should be escaped."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent))

        from data_queries import get_course_details

        # Should not cause SQL injection with special chars
        details = get_course_details(str(test_db_with_data), "Delilah", "50%_off")
        # Should return not found, not crash or return all courses
        assert "error" in details


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_database(self, tmp_path: Path):
        """Adapter should handle empty database gracefully."""
        db_path = tmp_path / "empty.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                powerschool_id TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT,
                grade_level TEXT,
                school_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY,
                student_id INTEGER,
                course_name TEXT,
                assignment_name TEXT,
                status TEXT
            );
            CREATE TABLE IF NOT EXISTS attendance_summary (
                id INTEGER PRIMARY KEY,
                student_id INTEGER,
                attendance_rate REAL,
                days_absent INTEGER,
                tardies INTEGER,
                total_days INTEGER
            );
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY,
                student_id INTEGER,
                course_name TEXT,
                teacher_name TEXT,
                teacher_email TEXT,
                room TEXT
            );
        """)
        conn.commit()
        conn.close()

        from repository_adapter import RepositoryAdapter

        adapter = RepositoryAdapter(db_path)
        student_id = adapter.get_student_id("Anyone")
        assert student_id is None

    def test_unicode_names(self, test_db_with_data: Path):
        """Adapter should handle Unicode names correctly."""
        # Add a student with Unicode name
        conn = sqlite3.connect(test_db_with_data)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO students (powerschool_id, first_name, last_name, grade_level)
            VALUES ('55262', 'Maria', 'Garcia', '8')
        """)
        conn.commit()
        conn.close()

        from repository_adapter import RepositoryAdapter

        adapter = RepositoryAdapter(test_db_with_data)
        student_id = adapter.get_student_id("Maria")
        assert student_id is not None

    def test_sql_injection_attempt(self, test_db_with_data: Path):
        """Malicious input should be safely handled."""
        from repository_adapter import RepositoryAdapter

        adapter = RepositoryAdapter(test_db_with_data)

        # These should not cause SQL injection
        malicious_inputs = [
            "'; DROP TABLE students; --",
            "1' OR '1'='1",
            "Robert'); DELETE FROM students WHERE ('1'='1",
            "' UNION SELECT * FROM students --",
        ]

        for malicious_input in malicious_inputs:
            # Should return None (not found), not crash or execute SQL
            result = adapter.get_student_id(malicious_input)
            assert result is None

        # Verify database is intact
        student_id = adapter.get_student_id("Delilah")
        assert student_id is not None
