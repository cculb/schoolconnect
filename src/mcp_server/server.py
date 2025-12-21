#!/usr/bin/env python3
"""MCP Server for PowerSchool Parent Portal data.

This server exposes tools for AI agents to query student academic data,
enabling natural language questions like "How is my kid doing in school?"
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env file from current directory if available
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from src.database.connection import verify_database
from src.database.repository import Repository

# Initialize MCP server
app = Server("powerschool-portal")

# Repository instance (will be initialized with database)
_repo: Optional[Repository] = None


def get_repo() -> Repository:
    """Get or create the repository instance."""
    global _repo
    if _repo is None:
        _repo = Repository()
    return _repo


# ==================== TOOL DEFINITIONS ====================


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        # Student Tools
        Tool(
            name="list_students",
            description="List all students in the PowerSchool account. Returns name, grade level, and school for each student.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_student_summary",
            description="Get a comprehensive summary for a student including: current courses, missing assignments count, attendance rate, and recent action items. Use student name (e.g., 'John') or 'all' for all students.",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_name": {
                        "type": "string",
                        "description": "Student's first name or 'all' for all students",
                    },
                },
                "required": ["student_name"],
            },
        ),
        # Grade Tools
        Tool(
            name="get_current_grades",
            description="Get current grades for a student across all courses. Shows letter grades, percentages, and teacher names.",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_name": {
                        "type": "string",
                        "description": "Student's first name",
                    },
                },
                "required": ["student_name"],
            },
        ),
        Tool(
            name="get_grade_trends",
            description="Show how grades have changed over the year (Q1 -> Q2 -> Q3 -> Q4). Useful for identifying improvement or decline.",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_name": {
                        "type": "string",
                        "description": "Student's first name",
                    },
                    "course_name": {
                        "type": "string",
                        "description": "Optional: filter to specific course",
                    },
                },
                "required": ["student_name"],
            },
        ),
        # Assignment Tools
        Tool(
            name="get_missing_assignments",
            description="Get all missing assignments for a student. These are assignments that were not turned in. Critical for identifying immediate action items.",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_name": {
                        "type": "string",
                        "description": "Student's first name or 'all' for all students",
                    },
                },
                "required": ["student_name"],
            },
        ),
        Tool(
            name="get_upcoming_assignments",
            description="Get assignments due in the next N days. Helps with planning and avoiding future missing work.",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_name": {
                        "type": "string",
                        "description": "Student's first name",
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look ahead (default: 14)",
                        "default": 14,
                    },
                },
                "required": ["student_name"],
            },
        ),
        Tool(
            name="get_assignment_completion_rates",
            description="Get assignment completion rates by course. Shows percentage of assignments completed, missing, and late.",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_name": {
                        "type": "string",
                        "description": "Student's first name",
                    },
                },
                "required": ["student_name"],
            },
        ),
        # Attendance Tools
        Tool(
            name="get_attendance_summary",
            description="Get attendance summary including: attendance rate percentage, days present, absences, and tardies.",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_name": {
                        "type": "string",
                        "description": "Student's first name",
                    },
                },
                "required": ["student_name"],
            },
        ),
        Tool(
            name="get_attendance_alerts",
            description="Get students with attendance concerns (below 95%). Shows alert level (warning/critical).",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        # Insight Tools
        Tool(
            name="get_action_items",
            description="Get prioritized action items for a parent. Includes missing assignments, attendance warnings, and suggested actions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_name": {
                        "type": "string",
                        "description": "Student's first name or 'all' for all students",
                    },
                },
                "required": ["student_name"],
            },
        ),
        Tool(
            name="generate_weekly_report",
            description="Generate a comprehensive weekly report for a student. Includes grades, missing work, attendance, and recommendations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_name": {
                        "type": "string",
                        "description": "Student's first name",
                    },
                },
                "required": ["student_name"],
            },
        ),
        Tool(
            name="prepare_teacher_meeting",
            description="Prepare talking points for a parent-teacher meeting about a specific course. Includes grade info, assignments, and suggested questions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_name": {
                        "type": "string",
                        "description": "Student's first name",
                    },
                    "course_name": {
                        "type": "string",
                        "description": "Course name (partial match allowed)",
                    },
                },
                "required": ["student_name", "course_name"],
            },
        ),
        # Teacher Tools
        Tool(
            name="list_teachers",
            description="List all teachers with their contact information. Shows name, email, and courses taught.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="get_teacher_profile",
            description="Get detailed profile for a specific teacher including courses, contact info, and communication history.",
            inputSchema={
                "type": "object",
                "properties": {
                    "teacher_name": {
                        "type": "string",
                        "description": "Teacher's name (partial match allowed)",
                    },
                },
                "required": ["teacher_name"],
            },
        ),
        Tool(
            name="draft_teacher_email",
            description="Draft an email to a teacher about a specific topic. Provides a suggested email based on context (missing work, grade concern, general check-in, or meeting request).",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_name": {
                        "type": "string",
                        "description": "Student's first name",
                    },
                    "teacher_name": {
                        "type": "string",
                        "description": "Teacher's name (partial match allowed)",
                    },
                    "topic": {
                        "type": "string",
                        "enum": ["missing_work", "grade_concern", "general", "meeting_request"],
                        "description": "Topic of the email",
                    },
                    "custom_message": {
                        "type": "string",
                        "description": "Optional: custom message or additional context to include",
                    },
                },
                "required": ["student_name", "teacher_name", "topic"],
            },
        ),
        Tool(
            name="get_communication_suggestions",
            description="Get suggested topics to discuss with teachers based on current student data (missing work, grade trends, attendance patterns).",
            inputSchema={
                "type": "object",
                "properties": {
                    "student_name": {
                        "type": "string",
                        "description": "Student's first name",
                    },
                },
                "required": ["student_name"],
            },
        ),
        Tool(
            name="save_communication_draft",
            description="Save a communication draft for later editing or sending.",
            inputSchema={
                "type": "object",
                "properties": {
                    "teacher_name": {
                        "type": "string",
                        "description": "Teacher's name",
                    },
                    "student_name": {
                        "type": "string",
                        "description": "Student's name",
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line",
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body",
                    },
                },
                "required": ["teacher_name", "student_name", "subject", "body"],
            },
        ),
        Tool(
            name="list_communication_drafts",
            description="List all saved communication drafts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["draft", "sent", "all"],
                        "description": "Filter by status (default: draft)",
                    },
                },
                "required": [],
            },
        ),
        # Utility Tools
        Tool(
            name="run_custom_query",
            description="Run a custom read-only SQL query against the database. Only SELECT statements are allowed.",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL SELECT query to execute",
                    },
                },
                "required": ["sql"],
            },
        ),
        Tool(
            name="get_database_status",
            description="Get database status including: table names, row counts, and last sync time.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


# ==================== TOOL HANDLERS ====================


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    repo = get_repo()

    try:
        if name == "list_students":
            return await handle_list_students(repo)
        elif name == "get_student_summary":
            return await handle_student_summary(repo, arguments.get("student_name", "all"))
        elif name == "get_current_grades":
            return await handle_current_grades(repo, arguments["student_name"])
        elif name == "get_grade_trends":
            return await handle_grade_trends(
                repo, arguments["student_name"], arguments.get("course_name")
            )
        elif name == "get_missing_assignments":
            return await handle_missing_assignments(repo, arguments.get("student_name", "all"))
        elif name == "get_upcoming_assignments":
            return await handle_upcoming_assignments(
                repo, arguments["student_name"], arguments.get("days", 14)
            )
        elif name == "get_assignment_completion_rates":
            return await handle_completion_rates(repo, arguments["student_name"])
        elif name == "get_attendance_summary":
            return await handle_attendance_summary(repo, arguments["student_name"])
        elif name == "get_attendance_alerts":
            return await handle_attendance_alerts(repo)
        elif name == "get_action_items":
            return await handle_action_items(repo, arguments.get("student_name", "all"))
        elif name == "generate_weekly_report":
            return await handle_weekly_report(repo, arguments["student_name"])
        elif name == "prepare_teacher_meeting":
            return await handle_teacher_meeting(
                repo, arguments["student_name"], arguments["course_name"]
            )
        elif name == "list_teachers":
            return await handle_list_teachers(repo)
        elif name == "get_teacher_profile":
            return await handle_teacher_profile(repo, arguments["teacher_name"])
        elif name == "draft_teacher_email":
            return await handle_draft_email(
                repo,
                arguments["student_name"],
                arguments["teacher_name"],
                arguments["topic"],
                arguments.get("custom_message"),
            )
        elif name == "get_communication_suggestions":
            return await handle_communication_suggestions(repo, arguments["student_name"])
        elif name == "save_communication_draft":
            return await handle_save_draft(
                repo,
                arguments["teacher_name"],
                arguments["student_name"],
                arguments["subject"],
                arguments["body"],
            )
        elif name == "list_communication_drafts":
            return await handle_list_drafts(repo, arguments.get("status", "draft"))
        elif name == "run_custom_query":
            return await handle_custom_query(repo, arguments["sql"])
        elif name == "get_database_status":
            return await handle_database_status(repo)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# ==================== HANDLER IMPLEMENTATIONS ====================


async def handle_list_students(repo: Repository) -> list[TextContent]:
    """List all students."""
    students = repo.get_students()
    if not students:
        return [TextContent(type="text", text="No students found in the database.")]

    result = "## Students\n\n"
    for s in students:
        name = f"{s['first_name']} {s.get('last_name', '')}".strip()
        grade = s.get("grade_level", "N/A")
        school = s.get("school_name", "N/A")
        result += f"- **{name}** - Grade: {grade}, School: {school}\n"

    return [TextContent(type="text", text=result)]


async def handle_student_summary(repo: Repository, student_name: str) -> list[TextContent]:
    """Get student summary."""
    if student_name.lower() == "all":
        students = repo.get_students()
    else:
        student = repo.get_student_by_name(student_name)
        students = [student] if student else []

    if not students:
        return [TextContent(type="text", text=f"No student found matching '{student_name}'.")]

    result = ""
    for student in students:
        summary = repo.get_student_summary(student["id"])
        if summary:
            result += f"## {summary['student_name']}\n\n"
            result += f"- **Courses**: {summary['course_count']}\n"
            result += f"- **Missing Assignments**: {summary['missing_assignments']}\n"
            if summary.get("attendance_rate"):
                result += f"- **Attendance Rate**: {summary['attendance_rate']:.1f}%\n"
            result += "\n"

    return [TextContent(type="text", text=result)]


async def handle_current_grades(repo: Repository, student_name: str) -> list[TextContent]:
    """Get current grades."""
    student = repo.get_student_by_name(student_name)
    if not student:
        return [TextContent(type="text", text=f"No student found matching '{student_name}'.")]

    grades = repo.get_current_grades(student["id"])
    if not grades:
        return [TextContent(type="text", text=f"No grades found for {student_name}.")]

    result = f"## Current Grades for {student['first_name']}\n\n"
    result += "| Course | Grade | Term | Teacher |\n"
    result += "|--------|-------|------|----------|\n"

    for g in grades:
        grade = g.get("letter_grade", "N/A")
        if g.get("percent"):
            grade = f"{grade} ({g['percent']:.0f}%)"
        result += (
            f"| {g['course_name']} | {grade} | {g['term']} | {g.get('teacher_name', 'N/A')} |\n"
        )

    return [TextContent(type="text", text=result)]


async def handle_grade_trends(
    repo: Repository, student_name: str, course_name: Optional[str]
) -> list[TextContent]:
    """Get grade trends."""
    student = repo.get_student_by_name(student_name)
    if not student:
        return [TextContent(type="text", text=f"No student found matching '{student_name}'.")]

    trends = repo.get_grade_trends(student["id"])
    if course_name:
        trends = [t for t in trends if course_name.lower() in t["course_name"].lower()]

    if not trends:
        return [TextContent(type="text", text="No grade trends found.")]

    result = f"## Grade Trends for {student['first_name']}\n\n"
    result += "| Course | Q1 | Q2 | S1 | Q3 | Q4 | S2 |\n"
    result += "|--------|----|----|----|----|----|----- |\n"

    for t in trends:
        result += f"| {t['course_name'][:30]} | {t.get('q1', '-')} | {t.get('q2', '-')} | {t.get('s1', '-')} | {t.get('q3', '-')} | {t.get('q4', '-')} | {t.get('s2', '-')} |\n"

    return [TextContent(type="text", text=result)]


async def handle_missing_assignments(repo: Repository, student_name: str) -> list[TextContent]:
    """Get missing assignments."""
    if student_name.lower() == "all":
        student_id = None
    else:
        student = repo.get_student_by_name(student_name)
        if not student:
            return [TextContent(type="text", text=f"No student found matching '{student_name}'.")]
        student_id = student["id"]

    missing = repo.get_missing_assignments(student_id)
    if not missing:
        msg = (
            "No missing assignments! 🎉"
            if student_name.lower() != "all"
            else "No missing assignments for any student!"
        )
        return [TextContent(type="text", text=msg)]

    result = "## Missing Assignments\n\n"
    for m in missing:
        days = m.get("days_overdue", 0)
        overdue = f" ({int(days)} days overdue)" if days and days > 0 else ""
        result += f"- **{m['assignment_name']}**{overdue}\n"
        result += f"  - Course: {m['course_name']}\n"
        result += f"  - Teacher: {m.get('teacher_name', 'N/A')}\n"
        if m.get("due_date"):
            result += f"  - Due: {m['due_date']}\n"
        result += "\n"

    return [TextContent(type="text", text=result)]


async def handle_upcoming_assignments(
    repo: Repository, student_name: str, days: int
) -> list[TextContent]:
    """Get upcoming assignments."""
    student = repo.get_student_by_name(student_name)
    if not student:
        return [TextContent(type="text", text=f"No student found matching '{student_name}'.")]

    upcoming = repo.get_upcoming_assignments(student["id"], days)
    if not upcoming:
        return [TextContent(type="text", text=f"No upcoming assignments in the next {days} days.")]

    result = f"## Upcoming Assignments (Next {days} Days)\n\n"
    for a in upcoming:
        result += f"- **{a['assignment_name']}**\n"
        result += f"  - Course: {a['course_name']}\n"
        result += f"  - Due: {a.get('due_date', 'N/A')}\n"
        result += f"  - Status: {a.get('status', 'N/A')}\n\n"

    return [TextContent(type="text", text=result)]


async def handle_completion_rates(repo: Repository, student_name: str) -> list[TextContent]:
    """Get assignment completion rates."""
    student = repo.get_student_by_name(student_name)
    if not student:
        return [TextContent(type="text", text=f"No student found matching '{student_name}'.")]

    rates = repo.get_completion_rates(student["id"])
    if not rates:
        return [TextContent(type="text", text="No completion rate data available.")]

    result = f"## Assignment Completion Rates for {student['first_name']}\n\n"
    result += "| Course | Total | Completed | Missing | Late | Rate |\n"
    result += "|--------|-------|-----------|---------|------|------|\n"

    for r in rates:
        result += f"| {r['course_name'][:25]} | {r['total_assignments']} | {r['completed']} | {r['missing']} | {r['late']} | {r['completion_rate']:.0f}% |\n"

    return [TextContent(type="text", text=result)]


async def handle_attendance_summary(repo: Repository, student_name: str) -> list[TextContent]:
    """Get attendance summary."""
    student = repo.get_student_by_name(student_name)
    if not student:
        return [TextContent(type="text", text=f"No student found matching '{student_name}'.")]

    attendance = repo.get_attendance_summary(student["id"])
    if not attendance:
        return [TextContent(type="text", text=f"No attendance data available for {student_name}.")]

    result = f"## Attendance Summary for {student['first_name']}\n\n"
    result += f"- **Attendance Rate**: {attendance.get('attendance_rate', 0):.1f}%\n"
    result += f"- **Days Present**: {attendance.get('days_present', 'N/A')}\n"
    result += f"- **Days Absent**: {attendance.get('days_absent', 0)}\n"
    result += f"- **Tardies**: {attendance.get('tardies', 0)}\n"
    result += f"- **Total School Days**: {attendance.get('total_days', 'N/A')}\n"

    rate = attendance.get("attendance_rate", 100)
    if rate < 80:
        result += "\n⚠️ **CRITICAL**: Attendance is below 80%. This may affect academic progress."
    elif rate < 90:
        result += "\n⚠️ **WARNING**: Attendance is below 90%. Consider reviewing absence patterns."

    return [TextContent(type="text", text=result)]


async def handle_attendance_alerts(repo: Repository) -> list[TextContent]:
    """Get attendance alerts."""
    alerts = repo.get_attendance_alerts()
    if not alerts:
        return [TextContent(type="text", text="No attendance concerns - all students above 95%!")]

    result = "## Attendance Alerts\n\n"
    for a in alerts:
        level = a.get("alert_level", "warning").upper()
        emoji = "🔴" if level == "CRITICAL" else "🟡"
        result += f"{emoji} **{a['student_name']}**: {a['attendance_rate']:.1f}% ({level})\n"
        result += f"   - Absences: {a['days_absent']}, Tardies: {a['tardies']}\n\n"

    return [TextContent(type="text", text=result)]


async def handle_action_items(repo: Repository, student_name: str) -> list[TextContent]:
    """Get prioritized action items."""
    if student_name.lower() == "all":
        student_id = None
    else:
        student = repo.get_student_by_name(student_name)
        if not student:
            return [TextContent(type="text", text=f"No student found matching '{student_name}'.")]
        student_id = student["id"]

    actions = repo.get_action_items(student_id)
    if not actions:
        return [TextContent(type="text", text="No action items - everything looks good! 🎉")]

    result = "## Action Items\n\n"
    for a in actions:
        priority = a.get("priority", "medium").upper()
        emoji = "🔴" if priority in ["HIGH", "CRITICAL"] else "🟡"
        result += f"{emoji} **[{priority}]** {a['message']}\n"
        if a.get("suggested_action"):
            result += f"   → {a['suggested_action']}\n"
        result += "\n"

    return [TextContent(type="text", text=result)]


async def handle_weekly_report(repo: Repository, student_name: str) -> list[TextContent]:
    """Generate weekly report."""
    student = repo.get_student_by_name(student_name)
    if not student:
        return [TextContent(type="text", text=f"No student found matching '{student_name}'.")]

    summary = repo.get_student_summary(student["id"])
    grades = repo.get_current_grades(student["id"])
    missing = repo.get_missing_assignments(student["id"])
    attendance = repo.get_attendance_summary(student["id"])
    actions = repo.get_action_items(student["id"])

    result = f"# Weekly Report: {student['first_name']}\n"
    result += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"

    # Overview
    result += "## Overview\n"
    if summary:
        result += f"- **Courses**: {summary['course_count']}\n"
        result += f"- **Missing Assignments**: {summary['missing_assignments']}\n"
    if attendance:
        rate = attendance.get("attendance_rate", 0)
        status = "✅" if rate >= 95 else "⚠️" if rate >= 90 else "🔴"
        result += f"- **Attendance**: {rate:.1f}% {status}\n"
    result += "\n"

    # Current Grades
    result += "## Current Grades\n"
    if grades:
        result += "| Course | Grade |\n|--------|-------|\n"
        for g in grades:
            result += f"| {g['course_name'][:30]} | {g.get('letter_grade', 'N/A')} |\n"
    else:
        result += "No grades recorded.\n"
    result += "\n"

    # Missing Work
    result += "## Missing Work\n"
    if missing:
        for m in missing:
            result += f"- ❌ {m['assignment_name']} ({m['course_name']})\n"
    else:
        result += "✅ No missing assignments!\n"
    result += "\n"

    # Action Items
    result += "## Recommended Actions\n"
    if actions:
        for i, a in enumerate(actions[:5], 1):
            result += f"{i}. {a.get('suggested_action', a['message'])}\n"
    else:
        result += "No immediate actions needed.\n"

    return [TextContent(type="text", text=result)]


async def handle_teacher_meeting(
    repo: Repository, student_name: str, course_name: str
) -> list[TextContent]:
    """Prepare for teacher meeting."""
    student = repo.get_student_by_name(student_name)
    if not student:
        return [TextContent(type="text", text=f"No student found matching '{student_name}'.")]

    # Find matching course
    courses = repo.get_courses(student["id"])
    course = None
    for c in courses:
        if course_name.lower() in c["course_name"].lower():
            course = c
            break

    if not course:
        available = ", ".join([c["course_name"] for c in courses])
        return [
            TextContent(
                type="text", text=f"No course matching '{course_name}'. Available: {available}"
            )
        ]

    # Get course-specific data
    grades = [
        g
        for g in repo.get_current_grades(student["id"])
        if g["course_name"] == course["course_name"]
    ]
    assignments = repo.get_assignments(student["id"], course_name=course["course_name"])
    missing = [a for a in assignments if a["status"] == "Missing"]

    result = f"# Teacher Meeting Prep: {course['course_name']}\n"
    result += f"*Student: {student['first_name']}*\n\n"

    # Teacher Info
    result += "## Teacher Information\n"
    result += f"- **Name**: {course.get('teacher_name', 'N/A')}\n"
    result += f"- **Room**: {course.get('room', 'N/A')}\n"
    if course.get("teacher_email"):
        result += f"- **Email**: {course['teacher_email']}\n"
    result += "\n"

    # Current Standing
    result += "## Current Standing\n"
    if grades:
        for g in grades:
            result += f"- **Grade**: {g.get('letter_grade', 'N/A')} ({g['term']})\n"
    result += f"- **Total Assignments**: {len(assignments)}\n"
    result += f"- **Missing**: {len(missing)}\n"
    result += "\n"

    # Missing Work
    if missing:
        result += "## Missing Work to Discuss\n"
        for m in missing:
            result += f"- {m['assignment_name']} (due: {m.get('due_date', 'N/A')})\n"
        result += "\n"

    # Suggested Questions
    result += "## Suggested Questions\n"
    result += "1. What are the most important skills for success in this class?\n"
    if missing:
        result += "2. Is there an opportunity to make up the missing work?\n"
    result += "3. How can we better support learning at home?\n"
    result += "4. What resources are available for extra help?\n"
    result += "5. Are there any upcoming major projects or tests to prepare for?\n"

    return [TextContent(type="text", text=result)]


async def handle_custom_query(repo: Repository, sql: str) -> list[TextContent]:
    """Run custom SQL query."""
    try:
        results = repo.execute_query(sql)
        if not results:
            return [TextContent(type="text", text="Query returned no results.")]

        # Format as table
        if results:
            headers = list(results[0].keys())
            result = "| " + " | ".join(headers) + " |\n"
            result += "|" + "|".join(["---"] * len(headers)) + "|\n"
            for row in results[:50]:  # Limit to 50 rows
                result += "| " + " | ".join(str(row.get(h, "")) for h in headers) + " |\n"

            if len(results) > 50:
                result += f"\n*... and {len(results) - 50} more rows*"

            return [TextContent(type="text", text=result)]
    except ValueError as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Query error: {str(e)}")]


async def handle_database_status(repo: Repository) -> list[TextContent]:
    """Get database status."""
    info = verify_database()

    result = "## Database Status\n\n"
    result += f"**Tables**: {', '.join(info.get('tables', []))}\n\n"
    result += "**Row Counts**:\n"
    for table, count in info.get("row_counts", {}).items():
        if not table.startswith("sqlite_"):
            result += f"- {table}: {count}\n"

    return [TextContent(type="text", text=result)]


# ==================== TEACHER HANDLERS ====================


async def handle_list_teachers(repo: Repository) -> list[TextContent]:
    """List all teachers."""
    teachers = repo.get_teachers()
    if not teachers:
        return [TextContent(type="text", text="No teachers found in the database.")]

    result = "## Teachers\n\n"
    result += "| Name | Email | Courses |\n"
    result += "|------|-------|----------|\n"

    for t in teachers:
        courses = t.get("courses_taught", "[]")
        try:
            courses_list = json.loads(courses) if courses else []
            courses_str = ", ".join(courses_list[:3])
            if len(courses_list) > 3:
                courses_str += f" (+{len(courses_list) - 3} more)"
        except (json.JSONDecodeError, TypeError, ValueError):
            courses_str = str(courses)[:30]

        result += f"| {t['name']} | {t.get('email', 'N/A')} | {courses_str} |\n"

    return [TextContent(type="text", text=result)]


async def handle_teacher_profile(repo: Repository, teacher_name: str) -> list[TextContent]:
    """Get teacher profile."""
    teacher = repo.get_teacher_by_name(teacher_name)
    if not teacher:
        teachers = repo.get_teachers()
        names = ", ".join([t["name"] for t in teachers])
        return [
            TextContent(
                type="text", text=f"No teacher found matching '{teacher_name}'. Available: {names}"
            )
        ]

    result = f"## Teacher Profile: {teacher['name']}\n\n"
    result += f"- **Email**: {teacher.get('email', 'N/A')}\n"
    result += f"- **Room**: {teacher.get('room', 'N/A')}\n"

    if teacher.get("last_contacted"):
        result += f"- **Last Contacted**: {teacher['last_contacted']}\n"
    result += f"- **Communication Count**: {teacher.get('communication_count', 0)}\n"

    # Courses taught
    courses = teacher.get("courses_taught", "[]")
    try:
        courses_list = json.loads(courses) if courses else []
        if courses_list:
            result += "\n### Courses Taught\n"
            for c in courses_list:
                result += f"- {c}\n"
    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    # Notes
    if teacher.get("notes"):
        result += f"\n### Notes\n{teacher['notes']}\n"

    return [TextContent(type="text", text=result)]


async def handle_draft_email(
    repo: Repository,
    student_name: str,
    teacher_name: str,
    topic: str,
    custom_message: Optional[str] = None,
) -> list[TextContent]:
    """Draft an email to a teacher."""
    student = repo.get_student_by_name(student_name)
    if not student:
        return [TextContent(type="text", text=f"No student found matching '{student_name}'.")]

    teacher = repo.get_teacher_by_name(teacher_name)
    if not teacher:
        return [TextContent(type="text", text=f"No teacher found matching '{teacher_name}'.")]

    # Get relevant data for the email
    missing = [
        a
        for a in repo.get_missing_assignments(student["id"])
        if teacher_name.lower() in (a.get("teacher_name", "") or "").lower()
    ]
    grades = [
        g
        for g in repo.get_current_grades(student["id"])
        if teacher_name.lower() in (g.get("teacher_name", "") or "").lower()
    ]

    # Generate email based on topic
    student_first = student["first_name"]
    # teacher_last available if needed for formal addressing
    _ = teacher["name"].split(",")[0] if "," in teacher["name"] else teacher["name"].split()[-1]

    if topic == "missing_work":
        subject = f"Regarding {student_first}'s Missing Assignment(s)"
        body = f"""Dear {teacher["name"]},

I hope this email finds you well. I am writing regarding my child {student_first}'s missing assignment(s) in your class.

"""
        if missing:
            body += "I understand the following assignment(s) are currently marked as missing:\n"
            for m in missing:
                body += f"- {m['assignment_name']} (due: {m.get('due_date', 'N/A')})\n"
            body += "\n"

        body += """I wanted to reach out to discuss how we can help {student_first} get caught up. Is there an opportunity for the work to be submitted late, or would you recommend an alternative approach?

Please let me know if there's anything we can do at home to better support {student_first}'s progress in your class.

Thank you for your time and dedication to your students.

Best regards,
[Parent Name]""".format(student_first=student_first)

    elif topic == "grade_concern":
        subject = f"Checking in on {student_first}'s Progress"
        current_grade = grades[0].get("letter_grade", "N/A") if grades else "N/A"
        body = f"""Dear {teacher["name"]},

I hope this message finds you well. I wanted to reach out to discuss {student_first}'s current progress in your class.

I noticed that {student_first}'s current grade is {current_grade}, and I wanted to better understand what areas might need improvement and how we can support their learning at home.

Could you share any insights on:
- Specific areas where {student_first} could improve
- Study strategies that might be helpful
- Any upcoming assignments or tests to focus on

I appreciate your guidance and partnership in {student_first}'s education.

Thank you,
[Parent Name]"""

    elif topic == "meeting_request":
        subject = f"Request for Parent-Teacher Conference - {student_first}"
        body = f"""Dear {teacher["name"]},

I hope this email finds you well. I would like to request a parent-teacher conference to discuss {student_first}'s progress in your class.

I am available at the following times:
- [Day/Time Option 1]
- [Day/Time Option 2]
- [Day/Time Option 3]

Please let me know what works best for your schedule. I am flexible and can accommodate other times if needed.

Thank you for your time.

Best regards,
[Parent Name]"""

    else:  # general
        subject = f"Checking in - {student_first} in Your Class"
        body = f"""Dear {teacher["name"]},

I hope this message finds you well. I wanted to touch base regarding {student_first}'s experience in your class.

{custom_message if custom_message else "I would appreciate any updates you could share about how " + student_first + " is doing academically and socially in your class."}

Thank you for your dedication to your students. Please don't hesitate to reach out if there's anything we should be aware of or ways we can better support {student_first}'s learning.

Best regards,
[Parent Name]"""

    if custom_message and topic != "general":
        body += f"\n\nAdditional note: {custom_message}"

    result = f"## Draft Email to {teacher['name']}\n\n"
    result += f"**To**: {teacher.get('email', '[no email available]')}\n"
    result += f"**Subject**: {subject}\n\n"
    result += "---\n\n"
    result += body
    result += "\n\n---\n\n"
    result += "*This is a draft. Edit as needed before sending.*"

    return [TextContent(type="text", text=result)]


async def handle_communication_suggestions(
    repo: Repository, student_name: str
) -> list[TextContent]:
    """Get communication suggestions."""
    student = repo.get_student_by_name(student_name)
    if not student:
        return [TextContent(type="text", text=f"No student found matching '{student_name}'.")]

    missing = repo.get_missing_assignments(student["id"])
    grades = repo.get_current_grades(student["id"])
    attendance = repo.get_attendance_summary(student["id"])

    result = f"## Communication Suggestions for {student['first_name']}\n\n"
    suggestions = []

    # Missing work suggestions
    if missing:
        by_teacher = {}
        for m in missing:
            teacher = m.get("teacher_name", "Unknown")
            if teacher not in by_teacher:
                by_teacher[teacher] = []
            by_teacher[teacher].append(m)

        for teacher, items in by_teacher.items():
            suggestions.append(
                {
                    "priority": "HIGH",
                    "teacher": teacher,
                    "topic": "missing_work",
                    "reason": f"{len(items)} missing assignment(s)",
                    "items": [i["assignment_name"] for i in items],
                }
            )

    # Low grade suggestions
    low_grades = [g for g in grades if g.get("letter_grade") in ["1", "2", "D", "F"]]
    for g in low_grades:
        suggestions.append(
            {
                "priority": "MEDIUM",
                "teacher": g.get("teacher_name", "Unknown"),
                "topic": "grade_concern",
                "reason": f"Grade of {g['letter_grade']} in {g['course_name']}",
            }
        )

    # Attendance suggestions
    if attendance and attendance.get("attendance_rate", 100) < 90:
        suggestions.append(
            {
                "priority": "MEDIUM",
                "teacher": "Counselor/Admin",
                "topic": "general",
                "reason": f"Attendance rate at {attendance['attendance_rate']:.1f}%",
            }
        )

    if not suggestions:
        result += "✅ **No urgent communications needed!**\n\n"
        result += "Everything looks good. Consider reaching out for:\n"
        result += "- Regular check-ins with teachers\n"
        result += "- Thank-you notes for positive experiences\n"
        result += "- Questions about upcoming projects or curriculum\n"
    else:
        result += "### Recommended Outreach\n\n"
        for s in sorted(suggestions, key=lambda x: x["priority"]):
            emoji = "🔴" if s["priority"] == "HIGH" else "🟡"
            result += f"{emoji} **{s['priority']}**: Contact **{s['teacher']}**\n"
            result += f"   - Topic: {s['topic'].replace('_', ' ').title()}\n"
            result += f"   - Reason: {s['reason']}\n"
            if "items" in s:
                result += f"   - Details: {', '.join(s['items'][:3])}\n"
            result += "\n"

    return [TextContent(type="text", text=result)]


async def handle_save_draft(
    repo: Repository, teacher_name: str, student_name: str, subject: str, body: str
) -> list[TextContent]:
    """Save a communication draft."""
    student = repo.get_student_by_name(student_name)
    if not student:
        return [TextContent(type="text", text=f"No student found matching '{student_name}'.")]

    teacher = repo.get_teacher_by_name(teacher_name)
    if not teacher:
        return [TextContent(type="text", text=f"No teacher found matching '{teacher_name}'.")]

    context = json.dumps({"subject": subject})

    draft_id = repo.create_communication(
        teacher_id=teacher["id"],
        student_id=student["id"],
        type="email",
        subject=subject,
        body=body,
        context=context,
        status="draft",
    )

    result = f"✅ Draft saved (ID: {draft_id})\n\n"
    result += f"- **To**: {teacher['name']} ({teacher.get('email', 'N/A')})\n"
    result += f"- **Subject**: {subject}\n"
    result += "- **Status**: Draft\n"

    return [TextContent(type="text", text=result)]


async def handle_list_drafts(repo: Repository, status: str) -> list[TextContent]:
    """List communication drafts."""
    if status == "all":
        drafts = repo.get_communications()
    else:
        drafts = repo.get_communications(status=status)

    if not drafts:
        return [TextContent(type="text", text=f"No {status} communications found.")]

    result = f"## Communications ({status})\n\n"
    for d in drafts:
        status_emoji = "📝" if d["status"] == "draft" else "✅" if d["status"] == "sent" else "📁"
        result += f"{status_emoji} **ID {d['id']}**: {d.get('subject', 'No subject')}\n"
        result += f"   - To: {d.get('teacher_name', 'Unknown')}\n"
        result += f"   - Student: {d.get('student_name', 'Unknown')}\n"
        result += f"   - Created: {d['created_at']}\n"
        if d.get("sent_at"):
            result += f"   - Sent: {d['sent_at']}\n"
        result += "\n"

    return [TextContent(type="text", text=result)]


# ==================== MAIN ====================


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
