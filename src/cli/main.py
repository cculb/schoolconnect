"""CLI interface for PowerSchool Parent Portal."""

import asyncio
import os
import sqlite3
from pathlib import Path

import click

from ..database.connection import Database, init_db_sync
from ..database.repository import Repository


def get_db_path(db: str | None) -> str:
    """Get database path from argument or environment."""
    if db:
        return db
    return os.environ.get("DATABASE_PATH", "data/powerschool.db")


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """PowerSchool Parent Portal CLI - Manage and analyze student data."""
    pass


@cli.command("init-db")
@click.option("--db", default=None, help="Path to database file")
def init_db(db: str | None):
    """Initialize the database schema."""
    db_path = get_db_path(db)
    click.echo(f"Initializing database at {db_path}...")

    try:
        init_db_sync(db_path)
        click.echo(click.style("✓ Database initialized successfully!", fg="green"))
    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
        raise click.Abort()


@cli.command("seed")
@click.option("--db", default=None, help="Path to database file")
def seed(db: str | None):
    """Seed the database with test data."""
    db_path = get_db_path(db)

    async def _seed():
        # Import here to avoid circular imports
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
        from scripts.seed_test_data import seed_database

        await seed_database(db_path)

    click.echo(f"Seeding database at {db_path}...")
    try:
        asyncio.run(_seed())
        click.echo(click.style("✓ Database seeded successfully!", fg="green"))
    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
        raise click.Abort()


@cli.command("missing")
@click.option("--db", default=None, help="Path to database file")
@click.option("--student", "-s", default=None, help="Filter by student name")
def missing(db: str | None, student: str | None):
    """Show missing assignments."""
    db_path = get_db_path(db)

    async def _get_missing():
        async with Database(db_path) as database:
            repo = Repository(database)

            student_id = None
            if student:
                s = await repo.get_student_by_name(student)
                if s:
                    student_id = s["student_id"]
                else:
                    click.echo(click.style(f"Student '{student}' not found", fg="yellow"))
                    return []

            return await repo.get_missing_assignments(student_id)

    try:
        assignments = asyncio.run(_get_missing())

        if not assignments:
            click.echo(click.style("✓ No missing assignments!", fg="green"))
            return

        click.echo(click.style(f"\n📋 Missing Assignments ({len(assignments)}):", fg="yellow", bold=True))
        click.echo("=" * 60)

        for a in assignments:
            click.echo(f"\n{click.style(a['assignment_name'], fg='red', bold=True)}")
            click.echo(f"  Course: {a['course_name']}")
            click.echo(f"  Teacher: {a['teacher_name']} ({a.get('teacher_email', 'no email')})")
            click.echo(f"  Due: {a['due_date']} ({a['days_overdue']} days overdue)")
            if a.get("category"):
                click.echo(f"  Category: {a['category']}")

    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
        raise click.Abort()


@cli.command("grades")
@click.option("--db", default=None, help="Path to database file")
@click.option("--student", "-s", required=True, help="Student name")
def grades(db: str | None, student: str):
    """Show current grades for a student."""
    db_path = get_db_path(db)

    async def _get_grades():
        async with Database(db_path) as database:
            repo = Repository(database)

            s = await repo.get_student_by_name(student)
            if not s:
                click.echo(click.style(f"Student '{student}' not found", fg="yellow"))
                return None, []

            grades_list = await repo.get_current_grades(s["student_id"])
            gpa = await repo.calculate_gpa(s["student_id"])
            return gpa, grades_list

    try:
        gpa, grades_list = asyncio.run(_get_grades())

        if grades_list is None:
            return

        if not grades_list:
            click.echo(click.style("No grades found", fg="yellow"))
            return

        click.echo(click.style(f"\n📊 Current Grades for {student}:", fg="blue", bold=True))
        click.echo("=" * 60)

        for g in grades_list:
            grade_color = "green" if g.get("gpa_points", 0) >= 3.0 else "yellow" if g.get("gpa_points", 0) >= 2.0 else "red"
            click.echo(
                f"  {g['course_name']:<40} "
                f"{click.style(g.get('letter_grade', 'N/A'), fg=grade_color, bold=True)}"
            )

        if gpa and gpa.get("gpa"):
            click.echo(f"\n  GPA: {gpa['gpa']:.2f}")

    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
        raise click.Abort()


@cli.command("attendance")
@click.option("--db", default=None, help="Path to database file")
@click.option("--student", "-s", required=True, help="Student name")
def attendance(db: str | None, student: str):
    """Show attendance summary for a student."""
    db_path = get_db_path(db)

    async def _get_attendance():
        async with Database(db_path) as database:
            repo = Repository(database)

            s = await repo.get_student_by_name(student)
            if not s:
                click.echo(click.style(f"Student '{student}' not found", fg="yellow"))
                return None

            return await repo.get_attendance_summary(s["student_id"])

    try:
        summary = asyncio.run(_get_attendance())

        if summary is None:
            return

        if not summary:
            click.echo(click.style("No attendance data found", fg="yellow"))
            return

        rate = summary.get("attendance_rate", 0)
        rate_color = "green" if rate >= 95 else "yellow" if rate >= 90 else "red"

        click.echo(click.style(f"\n📅 Attendance Summary for {student}:", fg="blue", bold=True))
        click.echo("=" * 60)
        click.echo(f"  Attendance Rate: {click.style(f'{rate:.1f}%', fg=rate_color, bold=True)}")
        click.echo(f"  Days Enrolled:   {summary.get('days_enrolled', 'N/A')}")
        click.echo(f"  Days Present:    {summary.get('days_present', 'N/A')}")
        click.echo(f"  Days Absent:     {summary.get('days_absent', 0)}")
        click.echo(f"    - Excused:     {summary.get('days_absent_excused', 0)}")
        click.echo(f"    - Unexcused:   {summary.get('days_absent_unexcused', 0)}")
        click.echo(f"  Tardies:         {summary.get('tardies', 0)}")

        if rate < 90:
            click.echo(click.style("\n  ⚠️  ALERT: Attendance below 90% threshold!", fg="red", bold=True))
        elif rate < 95:
            click.echo(click.style("\n  ⚠️  Warning: Attendance below 95%", fg="yellow"))

    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
        raise click.Abort()


@cli.command("report")
@click.option("--db", default=None, help="Path to database file")
@click.option("--student", "-s", required=True, help="Student name")
def report(db: str | None, student: str):
    """Generate weekly report for a student."""
    db_path = get_db_path(db)

    async def _generate_report():
        async with Database(db_path) as database:
            repo = Repository(database)

            s = await repo.get_student_by_name(student)
            if not s:
                return f"Student '{student}' not found"

            student_id = s["student_id"]
            full_name = f"{s['first_name']} {s['last_name']}"

            # Gather all data
            grades_list = await repo.get_current_grades(student_id)
            missing_list = await repo.get_missing_assignments(student_id)
            upcoming = await repo.get_upcoming_assignments(student_id, days=7)
            attendance_info = await repo.get_attendance_summary(student_id)
            gpa = await repo.calculate_gpa(student_id)
            completion = await repo.get_assignment_completion_rates(student_id)

            return {
                "name": full_name,
                "grades": grades_list,
                "missing": missing_list,
                "upcoming": upcoming,
                "attendance": attendance_info,
                "gpa": gpa,
                "completion": completion,
            }

    try:
        from datetime import datetime

        data = asyncio.run(_generate_report())

        if isinstance(data, str):
            click.echo(click.style(data, fg="yellow"))
            return

        # Build report
        click.echo(click.style(f"\n📊 Weekly Report for {data['name']}", fg="blue", bold=True))
        click.echo(f"Week of {datetime.now().strftime('%B %d, %Y')}")
        click.echo("=" * 60)

        # Wins
        click.echo(click.style("\n✅ WINS THIS WEEK", fg="green", bold=True))
        total = sum(c.get("total_assignments", 0) for c in data["completion"])
        completed = sum(c.get("completed", 0) for c in data["completion"])
        if total > 0:
            click.echo(f"  - Completed {completed} of {total} assignments")

        good_grades = [g for g in data["grades"] if g.get("gpa_points", 0) >= 3.0]
        if good_grades:
            click.echo(f"  - Maintaining good grades in {len(good_grades)} courses")

        if data["attendance"] and data["attendance"].get("attendance_rate", 0) >= 95:
            click.echo(f"  - Excellent attendance: {data['attendance']['attendance_rate']:.1f}%")

        if not data["missing"]:
            click.echo("  - No missing assignments! 🎉")

        # Needs attention
        click.echo(click.style("\n⚠️  NEEDS ATTENTION", fg="yellow", bold=True))
        if data["missing"]:
            click.echo(f"  - {len(data['missing'])} missing assignment(s):")
            for m in data["missing"][:3]:
                click.echo(f"    • {m['course_name']}: {m['assignment_name']}")
        else:
            click.echo("  - Nothing urgent!")

        if data["attendance"] and data["attendance"].get("attendance_rate", 100) < 95:
            click.echo(f"  - Attendance: {data['attendance']['attendance_rate']:.1f}%")

        # Coming up
        click.echo(click.style("\n📅 COMING UP", fg="cyan", bold=True))
        if data["upcoming"]:
            for u in data["upcoming"][:3]:
                days = u.get("days_until_due", 0)
                click.echo(f"  - {u['course_name']}: {u['assignment_name']} (in {days} days)")
        else:
            click.echo("  - No assignments due in the next 7 days")

        # GPA
        if data["gpa"] and data["gpa"].get("gpa"):
            click.echo(f"\n📈 Current GPA: {data['gpa']['gpa']:.2f}")

    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
        raise click.Abort()


@cli.command("students")
@click.option("--db", default=None, help="Path to database file")
def students(db: str | None):
    """List all students in the database."""
    db_path = get_db_path(db)

    async def _list_students():
        async with Database(db_path) as database:
            repo = Repository(database)
            return await repo.list_students()

    try:
        student_list = asyncio.run(_list_students())

        if not student_list:
            click.echo(click.style("No students found. Run 'powerschool seed' to add test data.", fg="yellow"))
            return

        click.echo(click.style(f"\n👥 Students ({len(student_list)}):", fg="blue", bold=True))
        click.echo("=" * 60)

        for s in student_list:
            click.echo(f"  {s['first_name']} {s['last_name']} - Grade {s['grade_level']} @ {s['school_name']}")

    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
        raise click.Abort()


@cli.command("serve-mcp")
@click.option("--db", default=None, help="Path to database file")
def serve_mcp(db: str | None):
    """Start the MCP server for AI agent interaction."""
    db_path = get_db_path(db)

    click.echo(f"Starting MCP server with database: {db_path}")
    click.echo("Server running via stdio - connect your AI agent...")

    try:
        from ..mcp_server.server import main as mcp_main

        mcp_main(db_path)
    except KeyboardInterrupt:
        click.echo("\nServer stopped.")
    except Exception as e:
        click.echo(click.style(f"✗ Error: {e}", fg="red"))
        raise click.Abort()


@cli.command("sync")
@click.option("--db", default=None, help="Path to database file")
@click.option("--url", envvar="POWERSCHOOL_URL", help="PowerSchool URL")
@click.option("--username", envvar="POWERSCHOOL_USERNAME", help="Username")
@click.option("--password", envvar="POWERSCHOOL_PASSWORD", help="Password")
def sync(db: str | None, url: str, username: str, password: str):
    """Sync data from PowerSchool (requires scraper configuration)."""
    if not all([url, username, password]):
        click.echo(click.style(
            "Error: PowerSchool credentials required.\n"
            "Set POWERSCHOOL_URL, POWERSCHOOL_USERNAME, POWERSCHOOL_PASSWORD environment variables\n"
            "or use --url, --username, --password options.",
            fg="red"
        ))
        raise click.Abort()

    click.echo(f"Syncing from {url}...")
    click.echo(click.style("Note: Scraper not yet implemented. Use 'seed' command for test data.", fg="yellow"))


if __name__ == "__main__":
    cli()
