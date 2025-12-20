"""Assignment-related MCP tools."""

from typing import Any

from mcp.server import Server

from ...database.connection import Database
from ...database.repository import Repository


def register_assignment_tools(mcp: Server, db_path: str) -> None:
    """Register assignment-related tools with the MCP server."""

    @mcp.tool()
    async def get_missing_assignments(
        student_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get all missing assignments, optionally filtered by student.

        Args:
            student_name: Optional student name to filter by (partial match supported)

        Returns:
            List of missing assignments with course and teacher info
        """
        async with Database(db_path) as db:
            repo = Repository(db)

            student_id = None
            if student_name:
                student = await repo.get_student_by_name(student_name)
                if not student:
                    return [{"error": f"Student '{student_name}' not found"}]
                student_id = student["student_id"]

            missing = await repo.get_missing_assignments(student_id)
            return [
                {
                    "student_name": m["student_name"],
                    "course_name": m["course_name"],
                    "teacher_name": m["teacher_name"],
                    "teacher_email": m["teacher_email"],
                    "assignment_name": m["assignment_name"],
                    "category": m["category"],
                    "due_date": m["due_date"],
                    "days_overdue": m["days_overdue"],
                }
                for m in missing
            ]

    @mcp.tool()
    async def get_upcoming_assignments(
        student_name: str, days: int = 14
    ) -> list[dict[str, Any]]:
        """Get assignments due in the next N days.

        Args:
            student_name: The name of the student (partial match supported)
            days: Number of days to look ahead (default 14)

        Returns:
            List of upcoming assignments sorted by due date
        """
        async with Database(db_path) as db:
            repo = Repository(db)

            student = await repo.get_student_by_name(student_name)
            if not student:
                return [{"error": f"Student '{student_name}' not found"}]

            upcoming = await repo.get_upcoming_assignments(student["student_id"], days)
            return [
                {
                    "course_name": u["course_name"],
                    "teacher_name": u["teacher_name"],
                    "assignment_name": u["assignment_name"],
                    "category": u["category"],
                    "due_date": u["due_date"],
                    "days_until_due": u["days_until_due"],
                }
                for u in upcoming
            ]

    @mcp.tool()
    async def get_assignment_completion_rates(
        student_name: str,
    ) -> list[dict[str, Any]]:
        """Get completion rate breakdown by course for a student.

        Args:
            student_name: The name of the student (partial match supported)

        Returns:
            List of courses with completion statistics
        """
        async with Database(db_path) as db:
            repo = Repository(db)

            student = await repo.get_student_by_name(student_name)
            if not student:
                return [{"error": f"Student '{student_name}' not found"}]

            rates = await repo.get_assignment_completion_rates(student["student_id"])
            return [
                {
                    "course_name": r["course_name"],
                    "teacher_name": r["teacher_name"],
                    "total_assignments": r["total_assignments"],
                    "completed": r["completed"],
                    "missing": r["missing"],
                    "late": r["late"],
                    "completion_rate": r["completion_rate"],
                }
                for r in rates
            ]

    @mcp.tool()
    async def get_recent_scores(
        student_name: str, days: int = 7
    ) -> list[dict[str, Any]]:
        """Get assignments graded in the last N days.

        Args:
            student_name: The name of the student (partial match supported)
            days: Number of days to look back (default 7)

        Returns:
            List of recently scored assignments
        """
        async with Database(db_path) as db:
            repo = Repository(db)

            student = await repo.get_student_by_name(student_name)
            if not student:
                return [{"error": f"Student '{student_name}' not found"}]

            scores = await repo.get_recent_scores(student["student_id"], days)
            return [
                {
                    "course_name": s.get("course_name"),
                    "assignment_name": s["assignment_name"],
                    "category": s["category"],
                    "score": s["score"],
                    "max_score": s["max_score"],
                    "percent": s["percent"],
                    "letter_grade": s["letter_grade"],
                    "recorded_at": s["recorded_at"],
                }
                for s in scores
            ]

    @mcp.tool()
    async def analyze_assignment_patterns(student_name: str) -> dict[str, Any]:
        """Analyze patterns: which subjects have most missing work, timing patterns, etc.

        Args:
            student_name: The name of the student (partial match supported)

        Returns:
            Dictionary with pattern analysis including problem subjects and timing
        """
        async with Database(db_path) as db:
            repo = Repository(db)

            student = await repo.get_student_by_name(student_name)
            if not student:
                return {"error": f"Student '{student_name}' not found"}

            student_id = student["student_id"]

            # Get completion rates
            rates = await repo.get_assignment_completion_rates(student_id)

            # Get missing assignments
            missing = await repo.get_missing_assignments(student_id)

            # Analyze patterns
            problem_courses = [r for r in rates if r["completion_rate"] < 80]
            high_missing = [r for r in rates if r["missing"] > 2]

            # Group missing by category
            category_counts: dict[str, int] = {}
            for m in missing:
                cat = m.get("category", "Unknown")
                category_counts[cat] = category_counts.get(cat, 0) + 1

            return {
                "student_name": f"{student['first_name']} {student['last_name']}",
                "total_missing": len(missing),
                "problem_courses": [
                    {
                        "course_name": c["course_name"],
                        "completion_rate": c["completion_rate"],
                        "missing_count": c["missing"],
                    }
                    for c in problem_courses
                ],
                "courses_with_high_missing": [c["course_name"] for c in high_missing],
                "missing_by_category": category_counts,
                "recommendations": _generate_recommendations(problem_courses, missing),
            }


def _generate_recommendations(
    problem_courses: list[dict], missing: list[dict]
) -> list[str]:
    """Generate recommendations based on patterns."""
    recommendations = []

    if len(missing) > 5:
        recommendations.append(
            "Consider setting up a daily homework routine to track assignments"
        )

    if problem_courses:
        course_names = [c["course_name"] for c in problem_courses[:2]]
        recommendations.append(
            f"Focus on catching up in: {', '.join(course_names)}"
        )

    if any(c.get("missing", 0) > 3 for c in problem_courses):
        recommendations.append(
            "Schedule meetings with teachers of courses with multiple missing assignments"
        )

    if not recommendations:
        recommendations.append("Great job staying on top of assignments!")

    return recommendations
