"""Integration tests for daily attendance database operations.

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
    db_path = tmp_path / "test_attendance.db"

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
        INSERT INTO students (powerschool_id, first_name, last_name, grade_level, school_name)
        VALUES ('12345', 'Test', 'Student', '6', 'Test Middle School')
        """
    )

    # Insert test attendance records (2 weeks of data)
    # Use empty string for period to match repository behavior
    test_records = [
        # Week 1: Dec 2-6, 2024
        (1, "2024-12-02", "Present", ".", ""),  # Monday
        (1, "2024-12-03", "Present", ".", ""),  # Tuesday
        (1, "2024-12-04", "Absent", "A", ""),   # Wednesday
        (1, "2024-12-05", "Present", ".", ""),  # Thursday
        (1, "2024-12-06", "Tardy", "T", ""),    # Friday
        # Week 2: Dec 9-13, 2024
        (1, "2024-12-09", "Present", ".", ""),  # Monday
        (1, "2024-12-10", "Excused", "E", ""),  # Tuesday
        (1, "2024-12-11", "Absent", "A", ""),   # Wednesday
        (1, "2024-12-12", "Present", ".", ""),  # Thursday
        (1, "2024-12-13", "Present", ".", ""),  # Friday
    ]

    for record in test_records:
        conn.execute(
            """
            INSERT INTO attendance_records (student_id, date, status, code, period)
            VALUES (?, ?, ?, ?, ?)
            """,
            record,
        )

    conn.commit()
    conn.close()

    yield db_path


@pytest.fixture
def repo(test_db: Path):
    """Create repository instance with test database."""
    from src.database.repository import Repository

    return Repository(db_path=test_db)


class TestUpsertAttendanceRecord:
    """Tests for upsert_attendance_record method."""

    def test_insert_new_record(self, repo):
        """Inserting a new record returns its ID."""
        record_id = repo.upsert_attendance_record(
            student_id=1,
            date="2024-12-16",
            status="Present",
            code=".",
        )

        assert record_id is not None
        assert record_id > 0

    def test_update_existing_record(self, repo):
        """Updating an existing record updates status."""
        # First insert
        record_id1 = repo.upsert_attendance_record(
            student_id=1,
            date="2024-12-16",
            status="Present",
            code=".",
        )

        # Update same date
        record_id2 = repo.upsert_attendance_record(
            student_id=1,
            date="2024-12-16",
            status="Absent",
            code="A",
        )

        # Should return same ID (upsert)
        assert record_id1 == record_id2

        # Verify status was updated
        records = repo.get_daily_attendance(student_id=1, start_date="2024-12-16")
        assert len(records) == 1
        assert records[0]["status"] == "Absent"

    def test_different_periods_are_separate_records(self, repo):
        """Different periods for same date are separate records."""
        id1 = repo.upsert_attendance_record(
            student_id=1, date="2024-12-16", status="Present", period="1"
        )
        id2 = repo.upsert_attendance_record(
            student_id=1, date="2024-12-16", status="Tardy", period="2"
        )

        assert id1 != id2


class TestBulkUpsertAttendanceRecords:
    """Tests for bulk_upsert_attendance_records method."""

    def test_bulk_insert_multiple_records(self, repo):
        """Bulk insert processes all records."""
        records = [
            {"date": "2024-12-16", "status": "Present", "code": "."},
            {"date": "2024-12-17", "status": "Absent", "code": "A"},
            {"date": "2024-12-18", "status": "Tardy", "code": "T"},
        ]

        count = repo.bulk_upsert_attendance_records(student_id=1, records=records)

        assert count == 3

        # Verify all records exist
        attendance = repo.get_daily_attendance(
            student_id=1, start_date="2024-12-16", end_date="2024-12-18"
        )
        assert len(attendance) == 3

    def test_bulk_insert_empty_list(self, repo):
        """Bulk insert handles empty list."""
        count = repo.bulk_upsert_attendance_records(student_id=1, records=[])
        assert count == 0


class TestGetDailyAttendance:
    """Tests for get_daily_attendance method."""

    def test_returns_all_records(self, repo):
        """Returns all attendance records for student."""
        records = repo.get_daily_attendance(student_id=1)

        assert len(records) == 10  # 2 weeks of test data

    def test_date_filtering(self, repo):
        """Date range filtering works correctly."""
        records = repo.get_daily_attendance(
            student_id=1, start_date="2024-12-09", end_date="2024-12-13"
        )

        assert len(records) == 5  # Week 2 only

        for r in records:
            assert r["date"] >= "2024-12-09"
            assert r["date"] <= "2024-12-13"

    def test_limit_parameter(self, repo):
        """Limit parameter restricts results."""
        records = repo.get_daily_attendance(student_id=1, limit=3)

        assert len(records) == 3

    def test_ordered_by_date_desc(self, repo):
        """Results are ordered by date descending."""
        records = repo.get_daily_attendance(student_id=1)

        dates = [r["date"] for r in records]
        assert dates == sorted(dates, reverse=True)

    def test_includes_student_info(self, repo):
        """Records include student name info."""
        records = repo.get_daily_attendance(student_id=1)

        assert len(records) > 0
        assert records[0]["first_name"] == "Test"


class TestGetAttendancePatterns:
    """Tests for get_attendance_patterns method."""

    def test_returns_day_of_week_patterns(self, repo):
        """Returns patterns grouped by day of week."""
        patterns = repo.get_attendance_patterns(student_id=1)

        # Should have records for 5 days (M-F)
        assert len(patterns) == 5

        # Check day names
        day_names = [p["day_name"] for p in patterns]
        assert "Monday" in day_names
        assert "Wednesday" in day_names

    def test_counts_absences_correctly(self, repo):
        """Correctly counts absences by day."""
        patterns = repo.get_attendance_patterns(student_id=1)

        # Wednesday has 2 absences (Dec 4 and Dec 11)
        wednesday = next((p for p in patterns if p["day_name"] == "Wednesday"), None)
        assert wednesday is not None
        assert wednesday["absence_count"] == 2
        assert wednesday["total_records"] == 2

    def test_calculates_attendance_rate(self, repo):
        """Calculates attendance rate per day."""
        patterns = repo.get_attendance_patterns(student_id=1)

        # Monday: 2 present / 2 total = 100%
        monday = next((p for p in patterns if p["day_name"] == "Monday"), None)
        assert monday is not None
        assert monday["attendance_rate"] == 100.0

        # Wednesday: 0 present / 2 total = 0%
        wednesday = next((p for p in patterns if p["day_name"] == "Wednesday"), None)
        assert wednesday is not None
        assert wednesday["attendance_rate"] == 0.0


class TestGetWeeklyAttendance:
    """Tests for get_weekly_attendance method."""

    def test_returns_weekly_summaries(self, repo):
        """Returns weekly attendance summaries."""
        weekly = repo.get_weekly_attendance(student_id=1)

        assert len(weekly) == 2  # 2 weeks of data

    def test_weekly_counts(self, repo):
        """Weekly counts are accurate."""
        weekly = repo.get_weekly_attendance(student_id=1)

        # Find week 1 (Dec 2-6)
        week1 = next((w for w in weekly if "2024-12-02" in str(w.get("week_start", ""))), None)
        if week1:
            assert week1["days_present"] == 3  # M, T, Th
            assert week1["days_absent"] == 1   # W
            assert week1["tardies"] == 1       # F


class TestGetAttendanceStreak:
    """Tests for get_attendance_streak method."""

    def test_calculates_longest_streaks(self, repo):
        """Calculates longest present and absent streaks."""
        streaks = repo.get_attendance_streak(student_id=1)

        assert "longest_present_streak" in streaks
        assert "longest_absent_streak" in streaks

        # Longest present streak: M, T (2) or later combinations
        assert streaks["longest_present_streak"] >= 2

    def test_current_streak(self, repo):
        """Determines current streak type and length."""
        streaks = repo.get_attendance_streak(student_id=1)

        assert "current_streak_type" in streaks
        assert "current_streak_days" in streaks

        # Last 2 days (Dec 12, 13) are present
        assert streaks["current_streak_type"] == "present"
        assert streaks["current_streak_days"] >= 2

    def test_handles_no_records(self, repo):
        """Handles student with no attendance records."""
        # Insert a new student with no records
        with sqlite3.connect(repo.db_path) as conn:
            conn.execute(
                "INSERT INTO students (id, powerschool_id, first_name) VALUES (99, '99', 'Empty')"
            )

        streaks = repo.get_attendance_streak(student_id=99)

        assert streaks["current_streak_type"] == "none"
        assert streaks["current_streak_days"] == 0


class TestClearAttendanceRecords:
    """Tests for clear_attendance_records method."""

    def test_clears_all_records(self, repo):
        """Clears all attendance records for student."""
        # Verify records exist
        before = repo.get_daily_attendance(student_id=1)
        assert len(before) > 0

        # Clear records
        repo.clear_attendance_records(student_id=1)

        # Verify cleared
        after = repo.get_daily_attendance(student_id=1)
        assert len(after) == 0


class TestViewsExist:
    """Tests that required views exist and work."""

    def test_v_daily_attendance_view(self, test_db):
        """v_daily_attendance view exists and returns data."""
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("SELECT * FROM v_daily_attendance LIMIT 1")
        row = cursor.fetchone()

        assert row is not None
        assert "student_id" in row.keys()
        assert "date" in row.keys()
        assert "status" in row.keys()

        conn.close()

    def test_v_attendance_patterns_view(self, test_db):
        """v_attendance_patterns view exists and returns data."""
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("SELECT * FROM v_attendance_patterns LIMIT 1")
        row = cursor.fetchone()

        assert row is not None
        assert "day_name" in row.keys()
        assert "absence_count" in row.keys()
        assert "attendance_rate" in row.keys()

        conn.close()

    def test_v_weekly_attendance_view(self, test_db):
        """v_weekly_attendance view exists and returns data."""
        conn = sqlite3.connect(test_db)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("SELECT * FROM v_weekly_attendance LIMIT 1")
        row = cursor.fetchone()

        assert row is not None
        assert "week_start" in row.keys()
        assert "days_present" in row.keys()
        assert "days_absent" in row.keys()

        conn.close()
