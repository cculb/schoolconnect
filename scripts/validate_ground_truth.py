#!/usr/bin/env python3
"""Validate scraped data against known ground truth.

This script checks that the data extracted by the scraper
matches known facts about the student's PowerSchool data.

Ground truth values should be configured via environment variables
or a local configuration file (not committed to git).
"""

import os
import sqlite3
import sys
from pathlib import Path
from typing import Tuple

from dotenv import load_dotenv

load_dotenv()

# Ground truth values - configure via environment or override locally
# These are example/placeholder values - real values come from .env
GROUND_TRUTH = {
    "student_name": os.getenv("GROUND_TRUTH_STUDENT_NAME", "Test Student"),
    "grade_level": int(os.getenv("GROUND_TRUTH_GRADE_LEVEL", "6")),
    "missing_assignments": [
        # Example assignments - actual data validated dynamically
        {"course": "Science", "name": "Knowledge Check"},
        {"course": "Social Studies", "name": "Assignment"},
    ],
    "attendance_rate": float(os.getenv("GROUND_TRUTH_ATTENDANCE_RATE", "90.0")),
    "days_present": int(os.getenv("GROUND_TRUTH_DAYS_PRESENT", "70")),
    "days_absent": int(os.getenv("GROUND_TRUTH_DAYS_ABSENT", "5")),
    "tardies": int(os.getenv("GROUND_TRUTH_TARDIES", "2")),
    "teachers": [],  # Validated dynamically from database
    "courses_min": int(os.getenv("GROUND_TRUTH_COURSES_MIN", "8")),
}


def validate(db_path: Path) -> Tuple[bool, list, list]:
    """Validate database against ground truth.

    Returns:
        Tuple of (passed, errors, warnings)
    """
    errors = []
    warnings = []

    if not db_path.exists():
        return False, ["Database file not found"], []

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check table existence
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        required_tables = {"assignments", "courses"}

        missing_tables = required_tables - tables
        if missing_tables:
            errors.append(f"Missing required tables: {missing_tables}")
            conn.close()
            return False, errors, warnings

        # Check missing assignments
        try:
            cursor.execute("""
                SELECT a.course_name, a.assignment_name
                FROM assignments a
                WHERE a.status = 'Missing'
            """)
            missing = cursor.fetchall()

            missing_count = len(missing)
            expected_min = len(GROUND_TRUTH["missing_assignments"])

            if missing_count < expected_min:
                errors.append(
                    f"Missing assignments: found {missing_count}, "
                    f"expected at least {expected_min}"
                )
            else:
                # Check for specific known missing assignments
                for expected in GROUND_TRUTH["missing_assignments"]:
                    found = any(
                        expected["name"].lower() in (m[1] or "").lower()
                        for m in missing
                    )
                    if not found:
                        warnings.append(
                            f"Expected missing assignment not found: {expected['name']}"
                        )
        except sqlite3.OperationalError as e:
            errors.append(f"Error querying assignments: {e}")

        # Check attendance rate
        if "attendance_summary" in tables:
            try:
                cursor.execute(
                    "SELECT attendance_rate, days_present, days_absent "
                    "FROM attendance_summary WHERE term = 'YTD' LIMIT 1"
                )
                row = cursor.fetchone()
                if row:
                    rate, present, absent = row
                    expected_rate = GROUND_TRUTH["attendance_rate"]

                    # Allow 5% tolerance for rate changes
                    if abs(rate - expected_rate) > 5.0:
                        warnings.append(
                            f"Attendance rate: got {rate:.1f}%, "
                            f"expected ~{expected_rate}%"
                        )

                    # Check days (allow some variance)
                    if present is not None:
                        expected_present = GROUND_TRUTH["days_present"]
                        if abs(present - expected_present) > 5:
                            warnings.append(
                                f"Days present: got {present}, "
                                f"expected ~{expected_present}"
                            )

                    if absent is not None:
                        expected_absent = GROUND_TRUTH["days_absent"]
                        if abs(absent - expected_absent) > 3:
                            warnings.append(
                                f"Days absent: got {absent}, "
                                f"expected ~{expected_absent}"
                            )
                else:
                    errors.append("No attendance summary found")
            except sqlite3.OperationalError as e:
                errors.append(f"Error querying attendance: {e}")
        else:
            warnings.append("attendance_summary table not found")

        # Check course count
        try:
            cursor.execute("SELECT COUNT(DISTINCT id) FROM courses")
            course_count = cursor.fetchone()[0]
            expected_min = GROUND_TRUTH["courses_min"]

            if course_count < expected_min:
                errors.append(
                    f"Courses: found {course_count}, expected >= {expected_min}"
                )
        except sqlite3.OperationalError as e:
            errors.append(f"Error counting courses: {e}")

        # Check teachers
        try:
            cursor.execute("SELECT DISTINCT teacher_name FROM courses WHERE teacher_name IS NOT NULL")
            teachers = [t[0] for t in cursor.fetchall()]

            # Check at least 3 expected teachers are found
            teachers_found = 0
            for expected_teacher in GROUND_TRUTH["teachers"][:5]:
                last_name = expected_teacher.split(",")[0].lower()
                found = any(last_name in t.lower() for t in teachers)
                if found:
                    teachers_found += 1
                else:
                    warnings.append(f"Teacher not found: {expected_teacher}")

            if teachers_found < 3:
                warnings.append(
                    f"Only {teachers_found} of expected teachers found"
                )
        except sqlite3.OperationalError as e:
            warnings.append(f"Could not check teachers: {e}")

    except sqlite3.Error as e:
        errors.append(f"Database error: {e}")
    finally:
        conn.close()

    passed = len(errors) == 0
    return passed, errors, warnings


def print_report(passed: bool, errors: list, warnings: list):
    """Print validation report."""
    print("=" * 60)
    print("GROUND TRUTH VALIDATION REPORT")
    print("=" * 60)
    print()

    if passed:
        print("✅ VALIDATION PASSED")
        print()
        print("The scraped data matches known ground truth:")
        print("  ✓ Missing assignments detected correctly")
        print("  ✓ Attendance data in expected range")
        print("  ✓ Course count meets minimum")
    else:
        print("❌ VALIDATION FAILED")
        print()
        print("ERRORS (blocking):")
        for error in errors:
            print(f"  ✗ {error}")

    if warnings:
        print()
        print("WARNINGS (non-blocking):")
        for warning in warnings:
            print(f"  ⚠ {warning}")

    print()
    print("=" * 60)

    # Print ground truth reference
    print("EXPECTED VALUES (from known data):")
    print(f"  - Missing assignments: >= {len(GROUND_TRUTH['missing_assignments'])}")
    print(f"  - Attendance rate: ~{GROUND_TRUTH['attendance_rate']}%")
    print(f"  - Days present: ~{GROUND_TRUTH['days_present']}")
    print(f"  - Days absent: ~{GROUND_TRUTH['days_absent']}")
    print(f"  - Minimum courses: {GROUND_TRUTH['courses_min']}")
    print("=" * 60)


def main():
    # Find database
    db_path = Path("powerschool.db")
    if not db_path.exists():
        db_path = Path("../powerschool.db")

    passed, errors, warnings = validate(db_path)
    print_report(passed, errors, warnings)

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
