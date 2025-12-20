"""Scraper module for PowerSchool data extraction."""

from .auth import (
    AuthenticationError,
    get_base_url,
    get_credentials,
    login,
    login_or_raise,
)

__all__ = [
    "AuthenticationError",
    "get_base_url",
    "get_credentials",
    "login",
    "login_or_raise",
]
