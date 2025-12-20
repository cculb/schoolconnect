"""Student-related MCP tools."""

from typing import Any

from mcp.server import Server

from ...database.connection import Database
from ...database.repository import Repository


def register_student_tools(mcp: Server, db_path: str) -> None:
    """Register student-related tools with the MCP server."""

    @mcp.tool()
    async def list_students() -> list[dict[str, Any]]:
        """List all students in the database with basic info.

        Returns a list of students with their ID, name, grade level, and school.
        """
        async with Database(db_path) as db:
            repo = Repository(db)
            students = await repo.list_students()
            return [
                {
                    "student_id": s["student_id"],
                    "name": f"{s['first_name']} {s['last_name']}",
                    "grade_level": s["grade_level"],
                    "school_name": s["school_name"],
                }
                for s in students
            ]

    @mcp.tool()
    async def get_student_summary(student_name: str) -> dict[str, Any]:
        """Get comprehensive summary for a student including GPA, attendance, missing work.

        Args:
            student_name: The name of the student (partial match supported)

        Returns:
            A dictionary with student summary including:
            - Basic info (name, grade, school)
            - Course count
            - Missing assignments count
            - Attendance rate
            - GPA
            - Action items
        """
        async with Database(db_path) as db:
            repo = Repository(db)

            # Find student by name
            student = await repo.get_student_by_name(student_name)
            if not student:
                return {"error": f"Student '{student_name}' not found"}

            student_id = student["student_id"]

            # Get summary from view
            summary = await repo.get_student_summary(student_id)

            # Get missing assignments
            missing = await repo.get_missing_assignments(student_id)

            # Get current grades
            grades = await repo.get_current_grades(student_id)

            # Get attendance
            attendance = await repo.get_attendance_summary(student_id)

            # Calculate GPA
            gpa_info = await repo.calculate_gpa(student_id)

            # Build action items
            action_items = []
            if missing:
                action_items.append({
                    "priority": 1,
                    "category": "missing_work",
                    "title": f"{len(missing)} missing assignment(s)",
                    "description": ", ".join(m["assignment_name"] for m in missing[:3]),
                })
            if attendance and attendance.get("attendance_rate", 100) < 90:
                action_items.append({
                    "priority": 2,
                    "category": "attendance",
                    "title": "Attendance below 90%",
                    "description": f"Current rate: {attendance.get('attendance_rate', 0):.1f}%",
                })

            return {
                "student_id": student_id,
                "name": f"{student['first_name']} {student['last_name']}",
                "grade_level": student["grade_level"],
                "school_name": student["school_name"],
                "course_count": summary.get("course_count", 0) if summary else 0,
                "missing_assignments": len(missing),
                "attendance_rate": attendance.get("attendance_rate") if attendance else None,
                "gpa": round(gpa_info.get("gpa") or 0, 2) if gpa_info.get("gpa") else None,
                "grades_summary": [
                    {
                        "course": g["course_name"],
                        "grade": g["letter_grade"],
                        "term": g["term"],
                    }
                    for g in grades
                ],
                "action_items": action_items,
            }
