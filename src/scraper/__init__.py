"""Scraper module for PowerSchool data extraction."""

from .auth import (
    AuthenticationError,
    get_available_students,
    get_base_url,
    get_credentials,
    get_current_student,
    login,
    login_or_raise,
    switch_to_student,
)

__all__ = [
    "AuthenticationError",
    "get_available_students",
    "get_base_url",
    "get_credentials",
    "get_current_student",
    "login",
    "login_or_raise",
    "switch_to_student",
]
