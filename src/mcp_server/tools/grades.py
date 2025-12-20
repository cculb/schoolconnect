"""Grade-related MCP tools."""

from typing import Any

from mcp.server import Server

from ...database.connection import Database
from ...database.repository import Repository


def register_grade_tools(mcp: Server, db_path: str) -> None:
    """Register grade-related tools with the MCP server."""

    @mcp.tool()
    async def get_current_grades(student_name: str) -> list[dict[str, Any]]:
        """Get current quarter/semester grades for a student.

        Args:
            student_name: The name of the student (partial match supported)

        Returns:
            List of current grades by course with teacher info
        """
        async with Database(db_path) as db:
            repo = Repository(db)

            student = await repo.get_student_by_name(student_name)
            if not student:
                return [{"error": f"Student '{student_name}' not found"}]

            grades = await repo.get_current_grades(student["student_id"])
            return [
                {
                    "course_name": g["course_name"],
                    "teacher_name": g["teacher_name"],
                    "term": g["term"],
                    "letter_grade": g["letter_grade"],
                    "percent": g["percent"],
                    "gpa_points": g["gpa_points"],
                }
                for g in grades
            ]

    @mcp.tool()
    async def get_grade_history(
        student_name: str, course_name: str | None = None
    ) -> list[dict[str, Any]]:
        """Get historical grade progression. Optionally filter by course.

        Args:
            student_name: The name of the student (partial match supported)
            course_name: Optional course name to filter by (partial match supported)

        Returns:
            List of grades showing progression across terms
        """
        async with Database(db_path) as db:
            repo = Repository(db)

            student = await repo.get_student_by_name(student_name)
            if not student:
                return [{"error": f"Student '{student_name}' not found"}]

            course_id = None
            if course_name:
                course = await repo.get_course_by_name(student["student_id"], course_name)
                if course:
                    course_id = course["course_id"]

            history = await repo.get_grade_history(student["student_id"], course_id)
            return [
                {
                    "course_name": h["course_name"],
                    "term": h["term"],
                    "letter_grade": h["letter_grade"],
                    "percent": h["percent"],
                    "gpa_points": h["gpa_points"],
                    "recorded_at": h["recorded_at"],
                }
                for h in history
            ]

    @mcp.tool()
    async def get_grade_trends(student_name: str) -> list[dict[str, Any]]:
        """Get grade trends showing Q1-Q4 and S1-S2 progression by course.

        Args:
            student_name: The name of the student (partial match supported)

        Returns:
            List of courses with grades across all terms
        """
        async with Database(db_path) as db:
            repo = Repository(db)

            student = await repo.get_student_by_name(student_name)
            if not student:
                return [{"error": f"Student '{student_name}' not found"}]

            trends = await repo.get_grade_trends(student["student_id"])
            return [
                {
                    "course_name": t["course_name"],
                    "Q1": t["Q1"],
                    "Q2": t["Q2"],
                    "Q3": t["Q3"],
                    "Q4": t["Q4"],
                    "S1": t["S1"],
                    "S2": t["S2"],
                }
                for t in trends
            ]

    @mcp.tool()
    async def calculate_gpa(student_name: str, term: str | None = None) -> dict[str, Any]:
        """Calculate GPA for a student. Optionally for a specific term.

        Args:
            student_name: The name of the student (partial match supported)
            term: Optional term (Q1, Q2, Q3, Q4, S1, S2) - if not provided, calculates overall

        Returns:
            Dictionary with GPA, course count, and term
        """
        async with Database(db_path) as db:
            repo = Repository(db)

            student = await repo.get_student_by_name(student_name)
            if not student:
                return {"error": f"Student '{student_name}' not found"}

            gpa_info = await repo.calculate_gpa(student["student_id"], term)
            return {
                "student_name": f"{student['first_name']} {student['last_name']}",
                "term": gpa_info.get("term", "Overall"),
                "gpa": round(gpa_info.get("gpa") or 0, 2) if gpa_info.get("gpa") else None,
                "course_count": gpa_info.get("course_count", 0),
            }

    @mcp.tool()
    async def identify_grade_drops(
        student_name: str, threshold: float = 0.5
    ) -> list[dict[str, Any]]:
        """Find courses where grade dropped by more than threshold between terms.

        Args:
            student_name: The name of the student (partial match supported)
            threshold: Minimum GPA point drop to flag (default 0.5)

        Returns:
            List of courses with significant grade drops
        """
        async with Database(db_path) as db:
            repo = Repository(db)

            student = await repo.get_student_by_name(student_name)
            if not student:
                return [{"error": f"Student '{student_name}' not found"}]

            trends = await repo.get_grade_trends(student["student_id"])
            drops = []

            # GPA mapping for letter grades
            gpa_map = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}
            # Also handle numeric grades (1-4 scale)
            for i in range(1, 5):
                gpa_map[str(i)] = float(i)

            for trend in trends:
                # Check Q1 -> Q2
                if trend.get("Q1") and trend.get("Q2"):
                    q1_gpa = gpa_map.get(trend["Q1"])
                    q2_gpa = gpa_map.get(trend["Q2"])
                    if q1_gpa and q2_gpa and (q1_gpa - q2_gpa) >= threshold:
                        drops.append({
                            "course_name": trend["course_name"],
                            "from_term": "Q1",
                            "to_term": "Q2",
                            "from_grade": trend["Q1"],
                            "to_grade": trend["Q2"],
                            "drop": round(q1_gpa - q2_gpa, 1),
                        })

                # Check Q2 -> Q3
                if trend.get("Q2") and trend.get("Q3"):
                    q2_gpa = gpa_map.get(trend["Q2"])
                    q3_gpa = gpa_map.get(trend["Q3"])
                    if q2_gpa and q3_gpa and (q2_gpa - q3_gpa) >= threshold:
                        drops.append({
                            "course_name": trend["course_name"],
                            "from_term": "Q2",
                            "to_term": "Q3",
                            "from_grade": trend["Q2"],
                            "to_grade": trend["Q3"],
                            "drop": round(q2_gpa - q3_gpa, 1),
                        })

                # Check Q3 -> Q4
                if trend.get("Q3") and trend.get("Q4"):
                    q3_gpa = gpa_map.get(trend["Q3"])
                    q4_gpa = gpa_map.get(trend["Q4"])
                    if q3_gpa and q4_gpa and (q3_gpa - q4_gpa) >= threshold:
                        drops.append({
                            "course_name": trend["course_name"],
                            "from_term": "Q3",
                            "to_term": "Q4",
                            "from_grade": trend["Q3"],
                            "to_grade": trend["Q4"],
                            "drop": round(q3_gpa - q4_gpa, 1),
                        })

            return drops
