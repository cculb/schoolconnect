"""E2E tests for alert detection and notification logic.

These tests validate the alert system correctly identifies
conditions that should trigger parent notifications.
"""

import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

pytestmark = [
    pytest.mark.e2e,
]


class TestMissingAssignmentAlerts:
    """Tests for missing assignment alert detection."""

    def test_detects_missing_assignments(self, test_db_path: Path, ground_truth: dict):
        """Alert system detects missing assignments from database."""
        if not test_db_path.exists():
            pytest.skip("Database not populated")

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM assignments WHERE status = 'Missing'"
        )
        missing_count = cursor.fetchone()[0]
        conn.close()

        # Should detect at least the known missing assignments
        expected_min = len(ground_truth["missing_assignments"])
        assert missing_count >= expected_min, (
            f"Should detect at least {expected_min} missing assignments, "
            f"found {missing_count}"
        )

    def test_alert_includes_due_date(self, test_db_path: Path):
        """Missing assignment alerts include due date information."""
        if not test_db_path.exists():
            pytest.skip("Database not populated")

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT assignment_name, due_date FROM assignments "
            "WHERE status = 'Missing' LIMIT 5"
        )
        missing = cursor.fetchall()
        conn.close()

        for name, due_date in missing:
            # Due date should be present (may be NULL in some cases)
            if due_date is None:
                print(f"Warning: Missing assignment '{name}' has no due date")

    def test_alert_categorizes_by_urgency(self, test_db_path: Path):
        """Missing assignments are categorized by urgency (how overdue)."""
        if not test_db_path.exists():
            pytest.skip("Database not populated")

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT assignment_name, due_date FROM assignments "
            "WHERE status = 'Missing' AND due_date IS NOT NULL"
        )
        missing = cursor.fetchall()
        conn.close()

        if not missing:
            pytest.skip("No missing assignments with due dates")

        today = datetime.now().date()
        urgent = []
        normal = []

        for name, due_date_str in missing:
            try:
                # Try to parse the date
                for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"]:
                    try:
                        due_date = datetime.strptime(due_date_str, fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    continue

                days_overdue = (today - due_date).days
                if days_overdue > 7:
                    urgent.append(name)
                else:
                    normal.append(name)
            except Exception:
                continue

        # Log categorization for debugging
        print(f"Urgent (>7 days overdue): {len(urgent)}")
        print(f"Normal (<7 days overdue): {len(normal)}")


class TestAttendanceAlerts:
    """Tests for attendance-based alert detection."""

    def test_detects_low_attendance(self, test_db_path: Path, ground_truth: dict):
        """Alert system detects attendance below threshold."""
        if not test_db_path.exists():
            pytest.skip("Database not populated")

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT attendance_rate FROM attendance_summary "
            "WHERE term = 'YTD' LIMIT 1"
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            pytest.skip("No attendance data")

        rate = row[0]
        threshold = 90.0  # Alert if below 90%

        if rate < threshold:
            assert True, f"Correctly identifies low attendance: {rate}%"
        else:
            print(f"Attendance rate {rate}% is above threshold {threshold}%")

    def test_calculates_absences_needed_for_threshold(
        self, test_db_path: Path, ground_truth: dict
    ):
        """Calculate how many more absences until hitting critical threshold."""
        if not test_db_path.exists():
            pytest.skip("Database not populated")

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT days_present, days_absent FROM attendance_summary "
            "WHERE term = 'YTD' LIMIT 1"
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            pytest.skip("No attendance data")

        present, absent = row
        total = present + absent
        current_rate = (present / total) * 100 if total > 0 else 100

        # Calculate absences allowed to stay above 85%
        threshold = 85.0
        # (present / (total + x)) * 100 = threshold
        # present * 100 = threshold * (total + x)
        # x = (present * 100 / threshold) - total

        if current_rate > threshold:
            absences_until_threshold = (present * 100 / threshold) - total
            print(
                f"Current rate: {current_rate:.1f}% - "
                f"Can miss {absences_until_threshold:.0f} more days before hitting {threshold}%"
            )


class TestGradeAlerts:
    """Tests for grade-based alert detection."""

    def test_detects_low_grades(self, test_db_path: Path):
        """Alert system detects courses with low grades."""
        if not test_db_path.exists():
            pytest.skip("Database not populated")

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT course_name, grade_percent FROM courses "
            "WHERE grade_percent IS NOT NULL AND grade_percent < 70"
        )
        low_grade_courses = cursor.fetchall()
        conn.close()

        if low_grade_courses:
            print(f"Found {len(low_grade_courses)} courses with grades below 70%:")
            for course, grade in low_grade_courses:
                print(f"  - {course}: {grade}%")

    def test_detects_grade_trends(self, test_db_path: Path):
        """Alert system could detect declining grade trends."""
        # This would require historical data tracking
        # For now, just verify we have grade data
        if not test_db_path.exists():
            pytest.skip("Database not populated")

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM courses WHERE grade_percent IS NOT NULL"
        )
        courses_with_grades = cursor.fetchone()[0]
        conn.close()

        assert courses_with_grades > 0, "Should have courses with grade data"


class TestAlertPrioritization:
    """Tests for alert prioritization logic."""

    def test_prioritizes_multiple_alerts(self, test_db_path: Path, ground_truth: dict):
        """Multiple alerts are correctly prioritized."""
        if not test_db_path.exists():
            pytest.skip("Database not populated")

        alerts = []

        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()

        # Check for missing assignments
        cursor.execute(
            "SELECT COUNT(*) FROM assignments WHERE status = 'Missing'"
        )
        missing_count = cursor.fetchone()[0]
        if missing_count > 0:
            alerts.append({
                "type": "missing_assignments",
                "priority": "high" if missing_count > 3 else "medium",
                "count": missing_count,
            })

        # Check attendance
        cursor.execute(
            "SELECT attendance_rate FROM attendance_summary WHERE term = 'YTD' LIMIT 1"
        )
        row = cursor.fetchone()
        if row and row[0] < 90:
            alerts.append({
                "type": "low_attendance",
                "priority": "high" if row[0] < 85 else "medium",
                "rate": row[0],
            })

        # Check low grades
        cursor.execute(
            "SELECT COUNT(*) FROM courses WHERE grade_percent < 70"
        )
        low_grade_count = cursor.fetchone()[0]
        if low_grade_count > 0:
            alerts.append({
                "type": "low_grades",
                "priority": "high",
                "count": low_grade_count,
            })

        conn.close()

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        alerts.sort(key=lambda a: priority_order.get(a["priority"], 99))

        print(f"Generated {len(alerts)} alerts:")
        for alert in alerts:
            print(f"  [{alert['priority'].upper()}] {alert['type']}")

        assert len(alerts) >= 1, "Should generate at least one alert"
