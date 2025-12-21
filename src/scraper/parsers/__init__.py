# Parsers module
"""HTML parsers for PowerSchool pages."""

from .course_scores import (
    parse_course_scores,
    parse_percent,
    parse_score,
    parse_standards,
    parse_weight,
)

__all__ = [
    "parse_course_scores",
    "parse_percent",
    "parse_score",
    "parse_standards",
    "parse_weight",
]
