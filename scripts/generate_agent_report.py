#!/usr/bin/env python3
"""Generate both agent-readable JSON and human-readable markdown reports.

This script is designed to run as a CI stage after tests complete,
producing artifacts for both AI agents and human reviewers.
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from current directory if available
load_dotenv()


def load_test_summary() -> dict:
    """Load the test summary JSON if it exists."""
    summary_path = Path("reports/test-summary.json")
    if summary_path.exists():
        with open(summary_path) as f:
            return json.load(f)
    return {}


def get_database_stats(db_path: Path) -> dict:
    """Get statistics from the database."""
    if not db_path.exists():
        return {}

    stats = {}
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM assignments WHERE status = 'Missing'")
        stats["missing_assignments"] = cursor.fetchone()[0]

        cursor.execute("SELECT attendance_rate FROM attendance_summary WHERE term = 'YTD' LIMIT 1")
        row = cursor.fetchone()
        stats["attendance_rate"] = row[0] if row else None

        cursor.execute("SELECT COUNT(*) FROM courses")
        stats["courses"] = cursor.fetchone()[0]

    except sqlite3.Error:
        pass
    finally:
        conn.close()

    return stats


def generate_agent_report(summary: dict, db_stats: dict) -> dict:
    """Generate structured report for AI agents."""
    report = {
        "generated_at": datetime.now().isoformat(),
        "pipeline_id": os.getenv("CI_PIPELINE_ID", os.getenv("GITHUB_RUN_ID", "local")),
        "branch": os.getenv("CI_COMMIT_REF_NAME", os.getenv("GITHUB_REF_NAME", "unknown")),
        "status": summary.get("status", "unknown"),
        "test_summary": summary.get("totals", {}),
        "database_stats": db_stats,
        "validations": summary.get("ground_truth_validation", {}),
        "agent_guidance": summary.get("agent_summary", {}),
    }

    # Add actionable next steps
    next_steps = []

    if report["status"] == "failed":
        agent_summary = summary.get("agent_summary", {})
        for issue in agent_summary.get("blocking_issues", []):
            next_steps.append({
                "type": "fix",
                "priority": "high",
                "description": issue,
            })

        for recommendation in agent_summary.get("recommendations", []):
            next_steps.append({
                "type": "investigate",
                "priority": "medium",
                "description": recommendation,
            })
    else:
        next_steps.append({
            "type": "proceed",
            "priority": "low",
            "description": "All tests passed. Ready for next development phase.",
        })

    report["next_steps"] = next_steps

    return report


def generate_human_report(summary: dict, db_stats: dict) -> str:
    """Generate markdown report for human readers."""
    lines = []
    lines.append("# PowerSchool Portal - Test Report")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Branch:** {os.getenv('CI_COMMIT_REF_NAME', os.getenv('GITHUB_REF_NAME', 'local'))}")
    lines.append(f"**Pipeline:** {os.getenv('CI_PIPELINE_ID', os.getenv('GITHUB_RUN_ID', 'N/A'))}")
    lines.append("")

    # Status badge
    status = summary.get("status", "unknown")
    if status == "passed":
        lines.append("## ✅ Status: PASSED")
    else:
        lines.append("## ❌ Status: FAILED")
    lines.append("")

    # Test summary table
    totals = summary.get("totals", {})
    lines.append("## Test Results")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total Tests | {totals.get('tests', 'N/A')} |")
    lines.append(f"| Passed | {totals.get('passed', 'N/A')} |")
    lines.append(f"| Failed | {totals.get('failed', 'N/A')} |")
    lines.append(f"| Skipped | {totals.get('skipped', 'N/A')} |")
    lines.append("")

    # Database statistics
    if db_stats:
        lines.append("## Database Statistics")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Missing Assignments | {db_stats.get('missing_assignments', 'N/A')} |")
        lines.append(f"| Attendance Rate | {db_stats.get('attendance_rate', 'N/A')}% |")
        lines.append(f"| Courses | {db_stats.get('courses', 'N/A')} |")
        lines.append("")

    # Ground truth validation
    validations = summary.get("ground_truth_validation", {})
    if validations:
        lines.append("## Ground Truth Validation")
        lines.append("")
        for key, passed in validations.items():
            if key == "all_passed":
                continue
            icon = "✅" if passed else "❌"
            label = key.replace("_", " ").title()
            lines.append(f"- {icon} {label}")
        lines.append("")

    # Issues and recommendations
    agent_summary = summary.get("agent_summary", {})
    blocking = agent_summary.get("blocking_issues", [])
    if blocking:
        lines.append("## Blocking Issues")
        lines.append("")
        for issue in blocking:
            lines.append(f"- ❌ {issue}")
        lines.append("")

    warnings = agent_summary.get("warnings", [])
    if warnings:
        lines.append("## Warnings")
        lines.append("")
        for warning in warnings:
            lines.append(f"- ⚠️ {warning}")
        lines.append("")

    recommendations = agent_summary.get("recommendations", [])
    if recommendations:
        lines.append("## Recommendations")
        lines.append("")
        for rec in recommendations:
            lines.append(f"- 💡 {rec}")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("*Report generated by PowerSchool Portal CI pipeline*")

    return "\n".join(lines)


def main():
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    db_path = Path("powerschool.db")
    if not db_path.exists():
        db_path = Path("../powerschool.db")

    # Load existing test summary or create minimal one
    summary = load_test_summary()
    db_stats = get_database_stats(db_path)

    # Generate reports
    agent_report = generate_agent_report(summary, db_stats)
    human_report = generate_human_report(summary, db_stats)

    # Write reports
    agent_report_path = reports_dir / "agent-report.json"
    with open(agent_report_path, "w") as f:
        json.dump(agent_report, f, indent=2)
    print(f"Agent report written to: {agent_report_path}")

    human_report_path = reports_dir / "human-report.md"
    with open(human_report_path, "w") as f:
        f.write(human_report)
    print(f"Human report written to: {human_report_path}")

    # Also output agent report to stdout for CI visibility
    print("\n" + "=" * 60)
    print("AGENT REPORT")
    print("=" * 60)
    print(json.dumps(agent_report, indent=2))


if __name__ == "__main__":
    main()
