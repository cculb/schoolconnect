"""Insight generation MCP tools."""

from datetime import datetime
from typing import Any

from mcp.server import Server

from ...database.connection import Database
from ...database.repository import Repository


def register_insight_tools(mcp: Server, db_path: str) -> None:
    """Register insight-related tools with the MCP server."""

    @mcp.tool()
    async def generate_weekly_report(student_name: str) -> str:
        """Generate a parent-friendly weekly summary report.

        Args:
            student_name: The name of the student (partial match supported)

        Returns:
            Formatted text report with weekly highlights and action items
        """
        async with Database(db_path) as db:
            repo = Repository(db)

            student = await repo.get_student_by_name(student_name)
            if not student:
                return f"Error: Student '{student_name}' not found"

            student_id = student["student_id"]
            full_name = f"{student['first_name']} {student['last_name']}"

            # Gather data
            grades = await repo.get_current_grades(student_id)
            missing = await repo.get_missing_assignments(student_id)
            upcoming = await repo.get_upcoming_assignments(student_id, days=7)
            attendance = await repo.get_attendance_summary(student_id)
            gpa_info = await repo.calculate_gpa(student_id)
            completion_rates = await repo.get_assignment_completion_rates(student_id)

            # Build report
            report_lines = [
                f"📊 Weekly Report for {full_name}",
                f"Week of {datetime.now().strftime('%B %d, %Y')}",
                "",
            ]

            # Wins section
            report_lines.append("✅ WINS THIS WEEK")
            total_assignments = sum(r.get("total_assignments", 0) for r in completion_rates)
            completed = sum(r.get("completed", 0) for r in completion_rates)
            if total_assignments > 0:
                report_lines.append(f"- Completed {completed} of {total_assignments} assignments")

            good_grades = [g for g in grades if g.get("gpa_points", 0) >= 3.0]
            if good_grades:
                report_lines.append(f"- Maintaining good grades in {len(good_grades)} courses")

            if attendance and attendance.get("attendance_rate", 0) >= 95:
                report_lines.append(f"- Excellent attendance: {attendance['attendance_rate']:.1f}%")

            if not missing:
                report_lines.append("- No missing assignments! 🎉")

            report_lines.append("")

            # Needs attention section
            report_lines.append("⚠️ NEEDS ATTENTION")
            if missing:
                report_lines.append(f"- {len(missing)} missing assignment(s):")
                for m in missing[:3]:
                    report_lines.append(f"  • {m['course_name']}: {m['assignment_name']} (due {m['due_date']})")
            else:
                report_lines.append("- Nothing urgent!")

            if attendance and attendance.get("attendance_rate", 100) < 95:
                rate = attendance["attendance_rate"]
                report_lines.append(f"- Attendance rate: {rate:.1f}% (goal: 95%+)")

            report_lines.append("")

            # Coming up section
            report_lines.append("📅 COMING UP")
            if upcoming:
                for u in upcoming[:3]:
                    days = u.get("days_until_due", 0)
                    day_text = "today" if days == 0 else f"in {days} day(s)"
                    report_lines.append(f"- {u['course_name']}: {u['assignment_name']} due {day_text}")
            else:
                report_lines.append("- No assignments due in the next 7 days")

            report_lines.append("")

            # Action items
            report_lines.append("💬 SUGGESTED PARENT ACTIONS")
            if missing:
                # Group by teacher
                teachers = {}
                for m in missing:
                    teacher = m.get("teacher_name", "Unknown")
                    email = m.get("teacher_email", "")
                    if teacher not in teachers:
                        teachers[teacher] = {"email": email, "assignments": []}
                    teachers[teacher]["assignments"].append(m["assignment_name"])

                for teacher, info in teachers.items():
                    if info["email"]:
                        report_lines.append(f"- Email {teacher} ({info['email']}) about missing work")
                    else:
                        report_lines.append(f"- Contact {teacher} about missing work")

            if attendance and attendance.get("attendance_rate", 100) < 90:
                report_lines.append("- Schedule meeting with school counselor about attendance")

            if not missing and attendance and attendance.get("attendance_rate", 100) >= 95:
                report_lines.append("- Celebrate the good work! Consider a small reward.")

            report_lines.append("")

            # GPA summary
            if gpa_info.get("gpa"):
                report_lines.append(f"📈 Current GPA: {gpa_info['gpa']:.2f}")

            return "\n".join(report_lines)

    @mcp.tool()
    async def get_action_items(student_name: str) -> list[dict[str, Any]]:
        """Get prioritized list of action items for parent/student.

        Args:
            student_name: The name of the student (partial match supported)

        Returns:
            List of action items sorted by priority
        """
        async with Database(db_path) as db:
            repo = Repository(db)

            student = await repo.get_student_by_name(student_name)
            if not student:
                return [{"error": f"Student '{student_name}' not found"}]

            student_id = student["student_id"]
            action_items = []

            # Check missing assignments (highest priority)
            missing = await repo.get_missing_assignments(student_id)
            for m in missing:
                action_items.append({
                    "priority": 1,
                    "category": "missing_work",
                    "title": f"Complete missing assignment: {m['assignment_name']}",
                    "description": f"Due {m['due_date']} for {m['course_name']}",
                    "action": f"Contact {m['teacher_name']} about completing this assignment",
                    "contact": m.get("teacher_email"),
                })

            # Check attendance
            attendance = await repo.get_attendance_summary(student_id)
            if attendance:
                rate = attendance.get("attendance_rate", 100)
                if rate < 90:
                    action_items.append({
                        "priority": 1,
                        "category": "attendance",
                        "title": "Critical: Attendance below 90%",
                        "description": f"Current rate: {rate:.1f}%. This is considered chronic absenteeism.",
                        "action": "Schedule meeting with school attendance officer",
                        "contact": None,
                    })
                elif rate < 95:
                    action_items.append({
                        "priority": 2,
                        "category": "attendance",
                        "title": "Warning: Attendance below 95%",
                        "description": f"Current rate: {rate:.1f}%. Monitor closely.",
                        "action": "Review absence patterns and address any issues",
                        "contact": None,
                    })

            # Check upcoming assignments
            upcoming = await repo.get_upcoming_assignments(student_id, days=3)
            for u in upcoming:
                action_items.append({
                    "priority": 2,
                    "category": "upcoming_work",
                    "title": f"Due soon: {u['assignment_name']}",
                    "description": f"Due in {u['days_until_due']} day(s) for {u['course_name']}",
                    "action": "Ensure assignment is completed on time",
                    "contact": u.get("teacher_email"),
                })

            # Check completion rates
            rates = await repo.get_assignment_completion_rates(student_id)
            for r in rates:
                if r.get("completion_rate", 100) < 70:
                    action_items.append({
                        "priority": 2,
                        "category": "completion_rate",
                        "title": f"Low completion rate in {r['course_name']}",
                        "description": f"Only {r['completion_rate']:.0f}% of assignments completed",
                        "action": f"Meet with {r['teacher_name']} to create catch-up plan",
                        "contact": None,
                    })

            # Sort by priority
            action_items.sort(key=lambda x: x["priority"])

            return action_items

    @mcp.tool()
    async def prepare_teacher_meeting(
        student_name: str, course_name: str
    ) -> dict[str, Any]:
        """Prepare talking points and questions for parent-teacher conference.

        Args:
            student_name: The name of the student (partial match supported)
            course_name: The course name (partial match supported)

        Returns:
            Dictionary with meeting preparation materials
        """
        async with Database(db_path) as db:
            repo = Repository(db)

            student = await repo.get_student_by_name(student_name)
            if not student:
                return {"error": f"Student '{student_name}' not found"}

            student_id = student["student_id"]
            full_name = f"{student['first_name']} {student['last_name']}"

            course = await repo.get_course_by_name(student_id, course_name)
            if not course:
                return {"error": f"Course '{course_name}' not found for {full_name}"}

            # Get grade history for course
            grade_history = await repo.get_grade_history(student_id, course["course_id"])

            # Get missing assignments for course
            all_missing = await repo.get_missing_assignments(student_id)
            course_missing = [m for m in all_missing if m["course_id"] == course["course_id"]]

            # Get completion rate for course
            rates = await repo.get_assignment_completion_rates(student_id)
            course_rate = next((r for r in rates if r["course_id"] == course["course_id"]), None)

            # Build discussion points
            discussion_points = []
            if course_missing:
                discussion_points.append(f"Missing assignments: {len(course_missing)} assignments need attention")
            if grade_history:
                latest = grade_history[-1] if grade_history else None
                if latest:
                    discussion_points.append(f"Current grade: {latest['letter_grade']} ({latest['term']})")
            if course_rate:
                discussion_points.append(f"Completion rate: {course_rate['completion_rate']:.0f}%")

            # Generate questions
            questions = [
                f"How is {student['first_name']} participating in class?",
                f"What areas should we focus on to improve?",
                "Are there any upcoming projects or tests we should prepare for?",
                "How can we better support learning at home?",
            ]
            if course_missing:
                questions.insert(0, f"What's the best way to make up the {len(course_missing)} missing assignment(s)?")

            # Strengths and concerns (based on data)
            concerns = []
            if course_missing:
                concerns.append(f"Missing {len(course_missing)} assignment(s)")
            if course_rate and course_rate["completion_rate"] < 80:
                concerns.append(f"Low assignment completion rate ({course_rate['completion_rate']:.0f}%)")

            return {
                "student_name": full_name,
                "course_name": course["course_name"],
                "teacher_name": course["teacher_name"],
                "teacher_email": course["teacher_email"],
                "room": course["room"],
                "discussion_points": discussion_points,
                "questions_to_ask": questions,
                "concerns_to_raise": concerns,
                "missing_assignments": [
                    {"name": m["assignment_name"], "due_date": m["due_date"]}
                    for m in course_missing
                ],
                "grade_history": [
                    {"term": g["term"], "grade": g["letter_grade"]}
                    for g in grade_history
                ],
            }

    @mcp.tool()
    async def run_custom_query(sql: str) -> list[dict[str, Any]]:
        """Run a read-only SQL query against the database. For advanced analysis.

        Args:
            sql: A SELECT query to run (only SELECT statements are allowed)

        Returns:
            Query results as a list of dictionaries
        """
        async with Database(db_path) as db:
            repo = Repository(db)
            try:
                results = await repo.run_custom_query(sql)
                return results
            except ValueError as e:
                return [{"error": str(e)}]
            except Exception as e:
                return [{"error": f"Query failed: {str(e)}"}]

    @mcp.tool()
    async def get_last_sync_time() -> dict[str, Any]:
        """Get timestamp of last successful data sync.

        Returns:
            Dictionary with last sync timestamp and status
        """
        async with Database(db_path) as db:
            repo = Repository(db)
            result = await repo.get_last_sync_time()
            if result.get("completed_at"):
                return {
                    "last_sync": result["completed_at"],
                    "student_id": result.get("student_id"),
                    "status": "Data is available",
                }
            return {
                "last_sync": None,
                "status": "No sync has been performed yet",
            }
