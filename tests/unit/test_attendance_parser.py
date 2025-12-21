"""Unit tests for daily attendance parser.

These tests use static HTML fixtures and don't require
external dependencies or network access.
"""


import pytest

pytestmark = pytest.mark.unit


# Sample HTML fixtures representing PowerSchool attendance grid
SAMPLE_ATTENDANCE_GRID_HTML = """
<table class="attendance-grid" id="attendance-calendar">
    <thead>
        <tr>
            <th>Week</th>
            <th>M</th>
            <th>T</th>
            <th>W</th>
            <th>H</th>
            <th>F</th>
        </tr>
    </thead>
    <tbody>
        <tr data-week="2024-12-02">
            <td class="week-label">Dec 2</td>
            <td class="att-present" data-date="2024-12-02"><span class="code">.</span></td>
            <td class="att-present" data-date="2024-12-03"><span class="code">.</span></td>
            <td class="att-absent" data-date="2024-12-04"><span class="code">A</span></td>
            <td class="att-present" data-date="2024-12-05"><span class="code">.</span></td>
            <td class="att-tardy" data-date="2024-12-06"><span class="code">T</span></td>
        </tr>
        <tr data-week="2024-12-09">
            <td class="week-label">Dec 9</td>
            <td class="att-present" data-date="2024-12-09"><span class="code">.</span></td>
            <td class="att-excused" data-date="2024-12-10"><span class="code">E</span></td>
            <td class="att-present" data-date="2024-12-11"><span class="code">.</span></td>
            <td class="att-present" data-date="2024-12-12"><span class="code">.</span></td>
            <td class="att-present" data-date="2024-12-13"><span class="code">.</span></td>
        </tr>
    </tbody>
</table>
"""

SAMPLE_EMPTY_GRID_HTML = """
<table class="attendance-grid" id="attendance-calendar">
    <thead>
        <tr>
            <th>Week</th>
            <th>M</th>
            <th>T</th>
            <th>W</th>
            <th>H</th>
            <th>F</th>
        </tr>
    </thead>
    <tbody>
    </tbody>
</table>
"""

# Alternative HTML format sometimes seen in PowerSchool
SAMPLE_DAILY_LIST_HTML = """
<div class="attendance-records">
    <div class="attendance-day" data-date="2024-12-02">
        <span class="date">Mon 12/02</span>
        <span class="status present">Present</span>
    </div>
    <div class="attendance-day" data-date="2024-12-03">
        <span class="date">Tue 12/03</span>
        <span class="status absent">Absent</span>
        <span class="code">Unexcused</span>
    </div>
    <div class="attendance-day" data-date="2024-12-04">
        <span class="date">Wed 12/04</span>
        <span class="status tardy">Tardy</span>
    </div>
</div>
"""


class TestAttendanceParser:
    """Tests for daily attendance HTML parsing."""

    def test_parse_attendance_grid_returns_list(self):
        """Parser returns a list of attendance records."""
        from src.scraper.parsers.attendance import parse_daily_attendance

        records = parse_daily_attendance(SAMPLE_ATTENDANCE_GRID_HTML)

        assert isinstance(records, list)
        assert len(records) > 0

    def test_parse_attendance_grid_count(self):
        """Parser extracts correct number of attendance records."""
        from src.scraper.parsers.attendance import parse_daily_attendance

        records = parse_daily_attendance(SAMPLE_ATTENDANCE_GRID_HTML)

        # 2 weeks * 5 days = 10 records
        assert len(records) == 10

    def test_parse_attendance_record_structure(self):
        """Each record has required fields: date, status, code."""
        from src.scraper.parsers.attendance import parse_daily_attendance

        records = parse_daily_attendance(SAMPLE_ATTENDANCE_GRID_HTML)

        for record in records:
            assert "date" in record, "Record missing 'date' field"
            assert "status" in record, "Record missing 'status' field"
            assert "code" in record, "Record missing 'code' field"

    def test_parse_attendance_present_status(self):
        """Parser correctly identifies present status."""
        from src.scraper.parsers.attendance import parse_daily_attendance

        records = parse_daily_attendance(SAMPLE_ATTENDANCE_GRID_HTML)

        present_records = [r for r in records if r["status"] == "Present"]
        # 7 present days in sample:
        # Week 1: M, T, H (3 present) - W is absent, F is tardy
        # Week 2: M, W, H, F (4 present) - T is excused
        assert len(present_records) == 7

    def test_parse_attendance_absent_status(self):
        """Parser correctly identifies absent status."""
        from src.scraper.parsers.attendance import parse_daily_attendance

        records = parse_daily_attendance(SAMPLE_ATTENDANCE_GRID_HTML)

        absent_records = [r for r in records if r["status"] == "Absent"]
        # 1 absent day (Wednesday Dec 4)
        assert len(absent_records) == 1
        assert absent_records[0]["date"] == "2024-12-04"
        assert absent_records[0]["code"] == "A"

    def test_parse_attendance_tardy_status(self):
        """Parser correctly identifies tardy status."""
        from src.scraper.parsers.attendance import parse_daily_attendance

        records = parse_daily_attendance(SAMPLE_ATTENDANCE_GRID_HTML)

        tardy_records = [r for r in records if r["status"] == "Tardy"]
        # 1 tardy day (Friday Dec 6)
        assert len(tardy_records) == 1
        assert tardy_records[0]["date"] == "2024-12-06"
        assert tardy_records[0]["code"] == "T"

    def test_parse_attendance_excused_status(self):
        """Parser correctly identifies excused absence status."""
        from src.scraper.parsers.attendance import parse_daily_attendance

        records = parse_daily_attendance(SAMPLE_ATTENDANCE_GRID_HTML)

        excused_records = [r for r in records if r["status"] == "Excused"]
        # 1 excused day (Tuesday Dec 10)
        assert len(excused_records) == 1
        assert excused_records[0]["date"] == "2024-12-10"
        assert excused_records[0]["code"] == "E"

    def test_parse_empty_grid(self):
        """Parser handles empty attendance grid gracefully."""
        from src.scraper.parsers.attendance import parse_daily_attendance

        records = parse_daily_attendance(SAMPLE_EMPTY_GRID_HTML)

        assert records == []

    def test_parse_empty_html(self):
        """Parser handles empty HTML gracefully."""
        from src.scraper.parsers.attendance import parse_daily_attendance

        result = parse_daily_attendance("")
        assert result == []

        result = parse_daily_attendance("<html></html>")
        assert result == []

    def test_parse_invalid_html(self):
        """Parser handles malformed HTML gracefully."""
        from src.scraper.parsers.attendance import parse_daily_attendance

        result = parse_daily_attendance("<table><tr><td>")
        assert result == []

        result = parse_daily_attendance("not html at all")
        assert result == []

    def test_date_format_validation(self):
        """Parser returns dates in YYYY-MM-DD format."""
        from src.scraper.parsers.attendance import parse_daily_attendance

        records = parse_daily_attendance(SAMPLE_ATTENDANCE_GRID_HTML)

        for record in records:
            date_str = record["date"]
            # Validate format YYYY-MM-DD
            assert len(date_str) == 10, f"Invalid date format: {date_str}"
            assert date_str[4] == "-" and date_str[7] == "-"
            # Validate it's a parseable date
            year, month, day = date_str.split("-")
            assert 2020 <= int(year) <= 2030
            assert 1 <= int(month) <= 12
            assert 1 <= int(day) <= 31


class TestAttendancePatternDetection:
    """Tests for attendance pattern detection."""

    def test_detect_day_of_week_patterns(self):
        """Detect which days of week have most absences."""
        from src.scraper.parsers.attendance import detect_attendance_patterns

        records = [
            {"date": "2024-12-02", "status": "Present", "code": "."},  # Monday
            {"date": "2024-12-03", "status": "Present", "code": "."},  # Tuesday
            {"date": "2024-12-04", "status": "Absent", "code": "A"},  # Wednesday
            {"date": "2024-12-05", "status": "Present", "code": "."},  # Thursday
            {"date": "2024-12-06", "status": "Present", "code": "."},  # Friday
            {"date": "2024-12-09", "status": "Present", "code": "."},  # Monday
            {"date": "2024-12-10", "status": "Present", "code": "."},  # Tuesday
            {"date": "2024-12-11", "status": "Absent", "code": "A"},  # Wednesday
            {"date": "2024-12-12", "status": "Present", "code": "."},  # Thursday
            {"date": "2024-12-13", "status": "Present", "code": "."},  # Friday
        ]

        patterns = detect_attendance_patterns(records)

        assert isinstance(patterns, dict)
        assert "by_day_of_week" in patterns
        # Wednesday should have 2 absences (100% absence rate)
        assert patterns["by_day_of_week"]["Wednesday"]["absence_count"] == 2
        assert patterns["by_day_of_week"]["Wednesday"]["total_records"] == 2

    def test_detect_absence_streaks(self):
        """Detect consecutive absence streaks."""
        from src.scraper.parsers.attendance import detect_attendance_patterns

        records = [
            {"date": "2024-12-02", "status": "Present", "code": "."},
            {"date": "2024-12-03", "status": "Absent", "code": "A"},
            {"date": "2024-12-04", "status": "Absent", "code": "A"},
            {"date": "2024-12-05", "status": "Absent", "code": "A"},
            {"date": "2024-12-06", "status": "Present", "code": "."},
        ]

        patterns = detect_attendance_patterns(records)

        assert "longest_absence_streak" in patterns
        assert patterns["longest_absence_streak"] == 3

    def test_pattern_summary_fields(self):
        """Pattern detection returns expected summary fields."""
        from src.scraper.parsers.attendance import detect_attendance_patterns

        records = [
            {"date": "2024-12-02", "status": "Present", "code": "."},
            {"date": "2024-12-03", "status": "Absent", "code": "A"},
            {"date": "2024-12-04", "status": "Tardy", "code": "T"},
        ]

        patterns = detect_attendance_patterns(records)

        assert "total_present" in patterns
        assert "total_absent" in patterns
        assert "total_tardy" in patterns
        assert "attendance_rate" in patterns

        assert patterns["total_present"] == 1
        assert patterns["total_absent"] == 1
        assert patterns["total_tardy"] == 1

    def test_empty_records_pattern_detection(self):
        """Pattern detection handles empty records."""
        from src.scraper.parsers.attendance import detect_attendance_patterns

        patterns = detect_attendance_patterns([])

        assert patterns["total_present"] == 0
        assert patterns["total_absent"] == 0
        assert patterns["attendance_rate"] == 100.0


class TestNormalizationFunctions:
    """Tests for attendance status normalization."""

    def test_normalize_status_present(self):
        """Normalizes various present indicators."""
        from src.scraper.parsers.attendance import normalize_attendance_status

        assert normalize_attendance_status(".", "att-present") == "Present"
        assert normalize_attendance_status("", "present") == "Present"
        assert normalize_attendance_status("P", "") == "Present"

    def test_normalize_status_absent(self):
        """Normalizes various absent indicators."""
        from src.scraper.parsers.attendance import normalize_attendance_status

        assert normalize_attendance_status("A", "att-absent") == "Absent"
        assert normalize_attendance_status("A", "") == "Absent"
        assert normalize_attendance_status("", "absent") == "Absent"

    def test_normalize_status_tardy(self):
        """Normalizes various tardy indicators."""
        from src.scraper.parsers.attendance import normalize_attendance_status

        assert normalize_attendance_status("T", "att-tardy") == "Tardy"
        assert normalize_attendance_status("T", "") == "Tardy"
        assert normalize_attendance_status("", "tardy") == "Tardy"

    def test_normalize_status_excused(self):
        """Normalizes various excused indicators."""
        from src.scraper.parsers.attendance import normalize_attendance_status

        assert normalize_attendance_status("E", "att-excused") == "Excused"
        assert normalize_attendance_status("EX", "") == "Excused"
        assert normalize_attendance_status("", "excused") == "Excused"

    def test_normalize_status_unknown(self):
        """Returns Unknown for unrecognized status."""
        from src.scraper.parsers.attendance import normalize_attendance_status

        assert normalize_attendance_status("X", "unknown-class") == "Unknown"
        assert normalize_attendance_status("", "") == "Unknown"


class TestDateParsing:
    """Tests for date parsing utilities."""

    def test_parse_date_iso_format(self):
        """Parses ISO format dates."""
        from src.scraper.parsers.attendance import parse_attendance_date

        result = parse_attendance_date("2024-12-15")
        assert result == "2024-12-15"

    def test_parse_date_us_format(self):
        """Parses US format dates (MM/DD/YYYY)."""
        from src.scraper.parsers.attendance import parse_attendance_date

        result = parse_attendance_date("12/15/2024")
        assert result == "2024-12-15"

    def test_parse_date_short_year(self):
        """Parses short year format (MM/DD/YY)."""
        from src.scraper.parsers.attendance import parse_attendance_date

        result = parse_attendance_date("12/15/24")
        assert result == "2024-12-15"

    def test_parse_date_invalid(self):
        """Returns None for invalid dates."""
        from src.scraper.parsers.attendance import parse_attendance_date

        assert parse_attendance_date("not-a-date") is None
        assert parse_attendance_date("") is None
        assert parse_attendance_date(None) is None
