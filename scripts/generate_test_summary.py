#!/usr/bin/env python3
"""Generate structured test summary for AI agents.

This script produces machine-readable JSON output that agents
can parse to determine next steps in iterative development.
"""

import json
import sqlite3
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from current directory if available
load_dotenv()


def parse_junit_xml(xml_path: Path) -> dict:
    """Parse JUnit XML to extract test results."""
    if not xml_path.exists():
        return {"error": f"File not found: {xml_path}"}

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Handle both single testsuite and testsuites wrapper
        if root.tag == "testsuites":
            testsuite = root.find("testsuite")
        else:
            testsuite = root

        if testsuite is None:
            return {"error": "No testsuite found"}

        # Extract test case details for failures
        failures = []
        for testcase in testsuite.findall(".//testcase"):
            failure = testcase.find("failure")
            error = testcase.find("error")
            result_element = failure if failure is not None else error
            if result_element is not None:
                failures.append({
                    "name": testcase.get("name"),
                    "classname": testcase.get("classname"),
                    "message": result_element.get("message", ""),
                })

        return {
            "tests": int(testsuite.get("tests", 0)),
            "failures": int(testsuite.get("failures", 0)),
            "errors": int(testsuite.get("errors", 0)),
            "skipped": int(testsuite.get("skipped", 0)),
            "time": float(testsuite.get("time", 0)),
            "failure_details": failures[:5],  # Limit to first 5
        }
    except ET.ParseError as e:
        return {"error": f"XML parse error: {e}"}


def get_database_stats(db_path: Path) -> dict:
    """Extract stats from the PowerSchool database."""
    if not db_path.exists():
        return {"error": "Database not found", "exists": False}

    stats = {"exists": True}

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Count students
        try:
            cursor.execute("SELECT COUNT(*) FROM students")
            stats["students"] = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            stats["students"] = 0

        # Count courses
        try:
            cursor.execute("SELECT COUNT(*) FROM courses")
            stats["courses"] = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            stats["courses"] = 0

        # Count assignments
        try:
            cursor.execute("SELECT COUNT(*) FROM assignments")
            stats["total_assignments"] = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            stats["total_assignments"] = 0

        # Count missing assignments
        try:
            cursor.execute("SELECT COUNT(*) FROM assignments WHERE status = 'Missing'")
            stats["missing_assignments"] = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            stats["missing_assignments"] = 0

        # Get attendance rate
        try:
            cursor.execute(
                "SELECT attendance_rate FROM attendance_summary WHERE term = 'YTD' LIMIT 1"
            )
            row = cursor.fetchone()
            stats["attendance_rate"] = row[0] if row else None
        except sqlite3.OperationalError:
            stats["attendance_rate"] = None

        # Get days absent
        try:
            cursor.execute(
                "SELECT days_absent FROM attendance_summary WHERE term = 'YTD' LIMIT 1"
            )
            row = cursor.fetchone()
            stats["days_absent"] = row[0] if row else None
        except sqlite3.OperationalError:
            stats["days_absent"] = None

        conn.close()

    except sqlite3.Error as e:
        stats["db_error"] = str(e)

    return stats


def validate_ground_truth(stats: dict) -> dict:
    """Check if extracted data matches known ground truth."""
    ground_truth = {
        "expected_missing_assignments_min": 2,
        "expected_attendance_rate_min": 85.0,
        "expected_attendance_rate_max": 92.0,
        "expected_min_courses": 8,
    }

    validations = {}

    # Check missing assignments
    missing = stats.get("missing_assignments", 0)
    validations["missing_assignments_correct"] = (
        missing >= ground_truth["expected_missing_assignments_min"]
    )

    # Check attendance rate
    rate = stats.get("attendance_rate")
    if rate is not None:
        validations["attendance_rate_correct"] = (
            ground_truth["expected_attendance_rate_min"]
            <= rate
            <= ground_truth["expected_attendance_rate_max"]
        )
    else:
        validations["attendance_rate_correct"] = False

    # Check course count
    courses = stats.get("courses", 0)
    validations["courses_found"] = courses >= ground_truth["expected_min_courses"]

    validations["all_passed"] = all(validations.values())

    return validations


def generate_agent_summary(
    test_results: dict, db_stats: dict, validations: dict
) -> dict:
    """Generate agent-friendly summary with recommendations."""
    summary = {
        "ready_for_next_phase": True,
        "blocking_issues": [],
        "warnings": [],
        "recommendations": [],
    }

    # Check test failures
    for key, results in test_results.items():
        if isinstance(results, dict) and results.get("failures", 0) > 0:
            summary["blocking_issues"].append(
                f"Test failures in {key}: {results['failures']} failed"
            )
            summary["ready_for_next_phase"] = False

            # Add failure details
            for failure in results.get("failure_details", []):
                summary["blocking_issues"].append(
                    f"  - {failure['name']}: {failure['message'][:100]}"
                )

    # Check validations
    if not validations.get("missing_assignments_correct"):
        summary["blocking_issues"].append(
            "Missing assignments not detected correctly. "
            f"Found: {db_stats.get('missing_assignments', 0)}, Expected: >= 2"
        )
        summary["recommendations"].append(
            "Check scraper parser for assignment status detection"
        )
        summary["ready_for_next_phase"] = False

    if not validations.get("attendance_rate_correct"):
        rate = db_stats.get("attendance_rate")
        if rate is None:
            summary["blocking_issues"].append(
                "Attendance rate not extracted. Check attendance parser."
            )
        else:
            summary["warnings"].append(
                f"Attendance rate {rate}% outside expected range (85-92%)"
            )
        summary["recommendations"].append("Verify attendance scraper targets correct elements")

    if not validations.get("courses_found"):
        summary["warnings"].append(
            f"Found {db_stats.get('courses', 0)} courses, expected >= 8"
        )
        summary["recommendations"].append("Check schedule scraper for missing courses")

    # Database health
    if not db_stats.get("exists"):
        summary["blocking_issues"].append("Database file not found")
        summary["ready_for_next_phase"] = False

    return summary


def main():
    # Determine paths
    reports_dir = Path("reports")
    db_path = Path("powerschool.db")

    # Check alternative paths
    if not reports_dir.exists():
        reports_dir = Path(".")
    if not db_path.exists():
        db_path = Path("../powerschool.db")

    summary = {
        "timestamp": datetime.now().isoformat(),
        "status": "unknown",
        "pipeline_source": "local",
    }

    # Parse test results from all JUnit XML files
    test_results = {}
    for xml_pattern in ["*-results.xml", "*_results.xml"]:
        for xml_file in reports_dir.glob(xml_pattern):
            key = xml_file.stem.replace("-results", "").replace("_results", "")
            test_results[key] = parse_junit_xml(xml_file)

    summary["test_results"] = test_results

    # Get database stats
    db_stats = get_database_stats(db_path)
    summary["database"] = db_stats

    # Validate against ground truth
    validations = validate_ground_truth(db_stats)
    summary["ground_truth_validation"] = validations

    # Calculate overall test stats
    total_tests = sum(
        r.get("tests", 0) for r in test_results.values() if isinstance(r, dict)
    )
    total_failures = sum(
        r.get("failures", 0) + r.get("errors", 0)
        for r in test_results.values()
        if isinstance(r, dict)
    )
    total_skipped = sum(
        r.get("skipped", 0) for r in test_results.values() if isinstance(r, dict)
    )

    summary["totals"] = {
        "tests": total_tests,
        "passed": total_tests - total_failures - total_skipped,
        "failed": total_failures,
        "skipped": total_skipped,
    }

    # Overall status
    all_tests_passed = total_failures == 0

    summary["status"] = (
        "passed"
        if (all_tests_passed and validations.get("all_passed"))
        else "failed"
    )

    # Generate agent summary
    summary["agent_summary"] = generate_agent_summary(
        test_results, db_stats, validations
    )

    # Output as JSON
    print(json.dumps(summary, indent=2, default=str))

    # Exit with appropriate code for CI
    sys.exit(0 if summary["status"] == "passed" else 1)


if __name__ == "__main__":
    main()
