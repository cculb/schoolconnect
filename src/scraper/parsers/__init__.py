"""PowerSchool HTML parsers."""

from .assignments import parse_assignments_page
from .grades import parse_grades_page
from .attendance import parse_attendance_page, parse_attendance_dashboard

__all__ = [
    "parse_assignments_page",
    "parse_grades_page",
    "parse_attendance_page",
    "parse_attendance_dashboard",
]
