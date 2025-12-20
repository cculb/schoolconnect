"""MCP Tools for PowerSchool data access."""

from .students import register_student_tools
from .grades import register_grade_tools
from .assignments import register_assignment_tools
from .attendance import register_attendance_tools
from .insights import register_insight_tools

__all__ = [
    "register_student_tools",
    "register_grade_tools",
    "register_assignment_tools",
    "register_attendance_tools",
    "register_insight_tools",
]
