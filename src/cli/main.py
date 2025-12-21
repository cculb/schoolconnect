#!/usr/bin/env python3
"""CLI for PowerSchool Parent Portal.

Commands:
    init-db     Create or reset the database
    sync        Sync data from PowerSchool (runs scraper)
    missing     Show missing assignments
    grades      Show current grades
    report      Generate weekly report
    serve-mcp   Start MCP server for AI agents
    status      Show database status and student overview
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from current directory if available
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import click  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.markdown import Markdown  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402

from src.database.connection import init_database, verify_database  # noqa: E402
from src.database.repository import Repository  # noqa: E402

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="powerschool")
def cli():
    """PowerSchool Parent Portal CLI - Manage and query student academic data."""
    pass


@cli.command()
@click.option("--force", is_flag=True, help="Force reset existing database")
def init_db(force: bool):
    """Initialize or reset the database."""
    if not force:
        db_path = Path("powerschool.db")
        if db_path.exists():
            if not click.confirm("Database exists. Reset it?", default=False):
                console.print("[yellow]Aborted.[/yellow]")
                return

    console.print("[blue]Initializing database...[/blue]")
    init_database(force=force)
    info = verify_database()

    console.print("[green]✓ Database initialized[/green]")
    console.print(f"  Tables: {', '.join(info.get('tables', []))}")
    console.print(f"  Views: {len(info.get('views', []))} views created")


@cli.command()
@click.option("--headless", is_flag=True, help="Run browser in headless mode")
@click.option("--student", "-s", help="Sync specific student only")
def sync(headless: bool, student: str):
    """Sync data from PowerSchool (runs scraper)."""
    try:
        # Import scraper (will fail if not installed)
        from scripts.load_data import load_scraped_data
        from scripts.scrape_full import run_full_scrape

        console.print("[blue]Starting PowerSchool sync...[/blue]")
        console.print("This will open a browser and log into PowerSchool.")

        # Run scraper
        run_full_scrape(headless=headless, student_name=student)

        # Load data
        console.print("\n[blue]Loading data into database...[/blue]")
        load_scraped_data()

        console.print("[green]✓ Sync complete![/green]")

    except ImportError as e:
        console.print(f"[red]Error: Scraper not available. {e}[/red]")
        console.print("Run manually: python scripts/scrape_full.py && python scripts/load_data.py")
    except Exception as e:
        console.print(f"[red]Sync failed: {e}[/red]")


@cli.command()
@click.option("--student", "-s", default="all", help="Student name (default: all)")
def missing(student: str):
    """Show missing assignments."""
    repo = Repository()

    if student.lower() == "all":
        student_id = None
        title = "All Students"
    else:
        s = repo.get_student_by_name(student)
        if not s:
            console.print(f"[red]Student not found: {student}[/red]")
            return
        student_id = s["id"]
        title = s["first_name"]

    missing_list = repo.get_missing_assignments(student_id)

    if not missing_list:
        console.print(
            Panel(
                "[green]No missing assignments! 🎉[/green]", title=f"Missing Assignments - {title}"
            )
        )

    table = Table(title=f"Missing Assignments - {title}")
    table.add_column("Assignment", style="red")
    table.add_column("Course")
    table.add_column("Teacher")
    table.add_column("Due Date")
    table.add_column("Days Overdue", justify="right")

    for m in missing_list:
        days = m.get("days_overdue", 0)
        days_str = f"{int(days)}" if days else "-"
        table.add_row(
            m["assignment_name"][:40],
            m["course_name"][:25],
            m.get("teacher_name", "N/A")[:20],
            str(m.get("due_date", "N/A")),
            days_str,
        )

    console.print(table)
    console.print(f"\n[bold red]Total missing: {len(missing_list)}[/bold red]")


@cli.command()
@click.option("--student", "-s", required=True, help="Student name")
def grades(student: str):
    """Show current grades for a student."""
    repo = Repository()

    s = repo.get_student_by_name(student)
    if not s:
        console.print(f"[red]Student not found: {student}[/red]")
        # Show available students
        students = repo.get_students()
        if students:
            names = ", ".join([st["first_name"] for st in students])
            console.print(f"[yellow]Available students: {names}[/yellow]")
        return

    grades_list = repo.get_current_grades(s["id"])

    if not grades_list:
        console.print(f"[yellow]No grades found for {student}[/yellow]")
        return

    table = Table(title=f"Current Grades - {s['first_name']}")
    table.add_column("Course")
    table.add_column("Grade", justify="center")
    table.add_column("Term")
    table.add_column("Teacher")

    for g in grades_list:
        grade = g.get("letter_grade", "N/A")
        grade_style = (
            "green"
            if grade in ["A", "4", "3.5", "P"]
            else "yellow"
            if grade in ["B", "3"]
            else "red"
        )
        table.add_row(
            g["course_name"][:30],
            f"[{grade_style}]{grade}[/{grade_style}]",
            g["term"],
            g.get("teacher_name", "N/A")[:20],
        )

    console.print(table)


@cli.command()
@click.option("--student", "-s", required=True, help="Student name")
def report(student: str):
    """Generate weekly report for a student."""
    repo = Repository()

    s = repo.get_student_by_name(student)
    if not s:
        console.print(f"[red]Student not found: {student}[/red]")
        return

    summary = repo.get_student_summary(s["id"])
    grades_list = repo.get_current_grades(s["id"])
    missing_list = repo.get_missing_assignments(s["id"])
    attendance = repo.get_attendance_summary(s["id"])
    actions = repo.get_action_items(s["id"])

    # Build report
    from datetime import datetime

    report_md = f"""# Weekly Report: {s["first_name"]}
*Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}*

## Overview
"""
    if summary:
        report_md += f"- **Courses**: {summary['course_count']}\n"
        report_md += f"- **Missing Assignments**: {summary['missing_assignments']}\n"

    if attendance:
        rate = attendance.get("attendance_rate", 0)
        status = "✅" if rate >= 95 else "⚠️" if rate >= 90 else "🔴"
        report_md += f"- **Attendance**: {rate:.1f}% {status}\n"

    report_md += "\n## Current Grades\n"
    if grades_list:
        for g in grades_list:
            grade = g.get("letter_grade", "-")
            report_md += f"- {g['course_name']}: **{grade}**\n"

    report_md += "\n## Missing Work\n"
    if missing_list:
        for m in missing_list:
            report_md += f"- ❌ {m['assignment_name']} ({m['course_name']})\n"
    else:
        report_md += "✅ No missing assignments!\n"

    report_md += "\n## Action Items\n"
    if actions:
        for i, a in enumerate(actions[:5], 1):
            report_md += f"{i}. {a.get('suggested_action', a['message'])}\n"
    else:
        report_md += "No immediate actions needed.\n"

    console.print(Markdown(report_md))


@cli.command("serve-mcp")
def serve_mcp():
    """Start MCP server for AI agents."""
    console.print("[blue]Starting MCP server...[/blue]")
    console.print("Server will listen on stdio for MCP protocol messages.")
    console.print("Press Ctrl+C to stop.\n")

    try:
        import asyncio

        from src.mcp_server.server import main

        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped.[/yellow]")
    except Exception as e:
        console.print(f"[red]Server error: {e}[/red]")


@cli.command()
def status():
    """Show database status and student overview."""
    repo = Repository()
    info = verify_database()

    # Database info
    console.print(Panel("[bold]Database Status[/bold]"))
    table = Table(show_header=False)
    table.add_column("Item", style="cyan")
    table.add_column("Value")

    for item, count in info.get("row_counts", {}).items():
        if not item.startswith("sqlite_"):
            table.add_row(item.title(), str(count))

    console.print(table)

    # Students overview
    students = repo.get_students()
    if students:
        console.print("\n[bold]Students[/bold]")
        for s in students:
            summary = repo.get_student_summary(s["id"])
            if summary:
                missing_count = summary.get("missing_assignments", 0)
                missing_style = "red" if missing_count > 0 else "green"
                console.print(
                    f"  • {s['first_name']}: "
                    f"[{missing_style}]{missing_count} missing[/{missing_style}], "
                    f"{summary.get('course_count', 0)} courses"
                )


@cli.command()
@click.option("--student", "-s", required=True, help="Student name")
def actions(student: str):
    """Show action items for a student."""
    repo = Repository()

    s = repo.get_student_by_name(student)
    if not s:
        console.print(f"[red]Student not found: {student}[/red]")
        return

    action_list = repo.get_action_items(s["id"])

    if not action_list:
        console.print(
            Panel(
                "[green]No action items - everything looks good! 🎉[/green]",
                title=f"Action Items - {s['first_name']}",
            )
        )
        return

    console.print(Panel(f"[bold]Action Items - {s['first_name']}[/bold]"))

    for a in action_list:
        priority = a.get("priority", "medium").upper()
        if priority in ["HIGH", "CRITICAL"]:
            emoji = "🔴"
            style = "red"
        else:
            emoji = "🟡"
            style = "yellow"

        console.print(f"{emoji} [{style}][{priority}][/{style}] {a['message']}")
        if a.get("suggested_action"):
            console.print(f"   → {a['suggested_action']}")
        console.print()


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
