"""Attendance-related MCP tools."""

from typing import Any

from mcp.server import Server

from ...database.connection import Database
from ...database.repository import Repository


def register_attendance_tools(mcp: Server, db_path: str) -> None:
    """Register attendance-related tools with the MCP server."""

    @mcp.tool()
    async def get_attendance_summary(student_name: str) -> dict[str, Any]:
        """Get attendance summary with rate, absences, tardies.

        Args:
            student_name: The name of the student (partial match supported)

        Returns:
            Dictionary with attendance statistics and alert level
        """
        async with Database(db_path) as db:
            repo = Repository(db)

            student = await repo.get_student_by_name(student_name)
            if not student:
                return {"error": f"Student '{student_name}' not found"}

            summary = await repo.get_attendance_summary(student["student_id"])
            if not summary:
                return {
                    "student_name": f"{student['first_name']} {student['last_name']}",
                    "message": "No attendance data available",
                }

            # Determine alert level
            rate = summary.get("attendance_rate", 100)
            if rate < 90:
                alert_level = "Critical"
            elif rate < 95:
                alert_level = "Warning"
            else:
                alert_level = "Good"

            return {
                "student_name": f"{student['first_name']} {student['last_name']}",
                "term": summary.get("term", "YTD"),
                "attendance_rate": summary.get("attendance_rate"),
                "days_enrolled": summary.get("days_enrolled"),
                "days_present": summary.get("days_present"),
                "days_absent": summary.get("days_absent"),
                "days_absent_excused": summary.get("days_absent_excused"),
                "days_absent_unexcused": summary.get("days_absent_unexcused"),
                "tardies": summary.get("tardies"),
                "tardies_excused": summary.get("tardies_excused"),
                "tardies_unexcused": summary.get("tardies_unexcused"),
                "alert_level": alert_level,
            }

    @mcp.tool()
    async def get_attendance_alerts() -> list[dict[str, Any]]:
        """Get all students with attendance issues (below 95%).

        Returns:
            List of students with attendance concerns, sorted by rate
        """
        async with Database(db_path) as db:
            repo = Repository(db)
            alerts = await repo.get_attendance_alerts()
            return [
                {
                    "student_name": a["student_name"],
                    "grade_level": a["grade_level"],
                    "attendance_rate": a["attendance_rate"],
                    "days_absent": a["days_absent"],
                    "tardies": a["tardies"],
                    "alert_level": a["alert_level"],
                }
                for a in alerts
            ]

    @mcp.tool()
    async def identify_attendance_patterns(student_name: str) -> dict[str, Any]:
        """Find patterns: trends over time, excused vs unexcused, etc.

        Args:
            student_name: The name of the student (partial match supported)

        Returns:
            Dictionary with attendance pattern analysis
        """
        async with Database(db_path) as db:
            repo = Repository(db)

            student = await repo.get_student_by_name(student_name)
            if not student:
                return {"error": f"Student '{student_name}' not found"}

            summary = await repo.get_attendance_summary(student["student_id"])
            if not summary:
                return {
                    "student_name": f"{student['first_name']} {student['last_name']}",
                    "message": "No attendance data available",
                }

            # Calculate patterns
            total_absent = summary.get("days_absent", 0)
            excused = summary.get("days_absent_excused", 0)
            unexcused = summary.get("days_absent_unexcused", 0)

            # Excused percentage
            excused_pct = (excused / total_absent * 100) if total_absent > 0 else 0

            # Tardy analysis
            total_tardies = summary.get("tardies", 0)
            tardies_excused = summary.get("tardies_excused", 0)

            # Generate insights
            insights = []
            if excused_pct == 100 and total_absent > 0:
                insights.append("All absences are excused - good documentation practices")
            elif unexcused > 0:
                insights.append(f"{unexcused} unexcused absence(s) need attention")

            rate = summary.get("attendance_rate", 100)
            if rate < 90:
                insights.append("Attendance is below 90% - chronic absenteeism threshold")
                insights.append("Consider meeting with school counselor")
            elif rate < 95:
                insights.append("Attendance is between 90-95% - approaching warning level")

            if total_tardies > 5:
                insights.append(f"High number of tardies ({total_tardies}) may indicate morning routine issues")

            return {
                "student_name": f"{student['first_name']} {student['last_name']}",
                "attendance_rate": rate,
                "total_absences": total_absent,
                "excused_absences": excused,
                "unexcused_absences": unexcused,
                "excused_percentage": round(excused_pct, 1),
                "total_tardies": total_tardies,
                "tardies_excused": tardies_excused,
                "insights": insights,
                "recommendations": _generate_attendance_recommendations(summary),
            }


def _generate_attendance_recommendations(summary: dict) -> list[str]:
    """Generate attendance recommendations based on data."""
    recommendations = []
    rate = summary.get("attendance_rate", 100)
    unexcused = summary.get("days_absent_unexcused", 0)
    tardies = summary.get("tardies", 0)

    if rate < 90:
        recommendations.append("Schedule meeting with school attendance officer")
        recommendations.append("Review any health issues that may be causing absences")
    elif rate < 95:
        recommendations.append("Monitor attendance closely for the rest of the term")

    if unexcused > 0:
        recommendations.append("Submit documentation for unexcused absences if available")

    if tardies > 5:
        recommendations.append("Establish consistent morning routine")
        recommendations.append("Consider earlier bedtime to improve morning alertness")

    if not recommendations:
        recommendations.append("Maintain current attendance habits - doing great!")

    return recommendations
