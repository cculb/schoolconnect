"""Sensitive data masking for log output.

This module provides utilities for masking PII and sensitive information
in log messages to prevent credential and data leakage.
"""

from __future__ import annotations

import re
from typing import Any

# Patterns for sensitive data detection
SENSITIVE_PATTERNS: dict[str, re.Pattern[str]] = {
    # Passwords in various formats
    "password_param": re.compile(
        r'(["\']?password["\']?\s*[:=]\s*)["\']?[^"\'\s,}\]]+["\']?', re.IGNORECASE
    ),
    "password_field": re.compile(r"(password\s*=\s*)[^\s,]+", re.IGNORECASE),
    # API keys and tokens
    "api_key": re.compile(
        r'(["\']?api[_-]?key["\']?\s*[:=]\s*)["\']?[a-zA-Z0-9_\-]+["\']?', re.IGNORECASE
    ),
    "token": re.compile(
        r'(["\']?(?:(?:auth|bearer|access)[_-]?)?token["\']?\s*[:=]\s*)["\']?[a-zA-Z0-9_\-\.]+["\']?',
        re.IGNORECASE,
    ),
    "secret": re.compile(
        r'(["\']?(?:client[_-]?)?secret["\']?\s*[:=]\s*)["\']?[a-zA-Z0-9_\-]+["\']?', re.IGNORECASE
    ),
    # Credentials in URLs
    "url_credentials": re.compile(r"(https?://)[^:]+:[^@]+(@)", re.IGNORECASE),
    # Base64 encoded passwords (common in CI)
    "base64_password": re.compile(
        r'(["\']?password[_-]?b(?:ase)?64["\']?\s*[:=]\s*)["\']?[a-zA-Z0-9+/=]+["\']?',
        re.IGNORECASE,
    ),
    # Email addresses (PII)
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    # Student IDs (could be sensitive)
    "student_id_value": re.compile(r'(["\']?student[_-]?id["\']?\s*[:=]\s*)\d+', re.IGNORECASE),
}

# Keywords that indicate sensitive field names
SENSITIVE_KEYWORDS: set[str] = {
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "auth",
    "credential",
    "credentials",
    "private_key",
    "privatekey",
    "access_token",
    "refresh_token",
    "bearer",
    "authorization",
}

# Mask replacement string
MASK = "***MASKED***"


def mask_sensitive_string(text: str) -> str:
    """Mask sensitive patterns in a string.

    Args:
        text: The text to mask

    Returns:
        Text with sensitive data replaced by MASK
    """
    if not text:
        return text

    result = text

    # Apply pattern-based masking
    for _name, pattern in SENSITIVE_PATTERNS.items():
        if _name == "email":
            # For emails, mask the local part
            result = pattern.sub(
                lambda m: m.group(0).split("@")[0][:2] + "***@" + m.group(0).split("@")[1], result
            )
        elif _name == "url_credentials":
            # For URL credentials, keep the protocol and host
            result = pattern.sub(r"\1" + MASK + r"\2", result)
        elif _name in (
            "password_param",
            "password_field",
            "api_key",
            "token",
            "secret",
            "base64_password",
        ):
            # For these patterns, group 1 is the key part, replace the value
            result = pattern.sub(r"\g<1>" + MASK, result)
        elif _name == "student_id_value":
            # Mask student IDs partially
            result = pattern.sub(r"\g<1>***", result)

    return result


def mask_dict(data: dict[str, Any], depth: int = 0, max_depth: int = 10) -> dict[str, Any]:
    """Recursively mask sensitive values in a dictionary.

    Args:
        data: Dictionary to mask
        depth: Current recursion depth
        max_depth: Maximum recursion depth

    Returns:
        Dictionary with sensitive values masked
    """
    if depth >= max_depth:
        return data

    result: dict[str, Any] = {}

    for key, value in data.items():
        lower_key = key.lower()

        # Check if key indicates sensitive data
        if any(keyword in lower_key for keyword in SENSITIVE_KEYWORDS):
            result[key] = MASK
        elif isinstance(value, dict):
            result[key] = mask_dict(value, depth + 1, max_depth)
        elif isinstance(value, list):
            result[key] = [
                mask_dict(item, depth + 1, max_depth) if isinstance(item, dict) else item
                for item in value
            ]
        elif isinstance(value, str):
            result[key] = mask_sensitive_string(value)
        else:
            result[key] = value

    return result


def is_sensitive_key(key: str) -> bool:
    """Check if a key name indicates sensitive data.

    Args:
        key: The key name to check

    Returns:
        True if the key appears to be sensitive
    """
    lower_key = key.lower()
    return any(keyword in lower_key for keyword in SENSITIVE_KEYWORDS)


class SensitiveValue:
    """Wrapper for sensitive values that masks them when converted to string.

    Usage:
        password = SensitiveValue(os.getenv("PASSWORD"))
        logger.info(f"Using password: {password}")  # Logs "Using password: ***MASKED***"
    """

    def __init__(self, value: Any) -> None:
        self._value = value

    def get(self) -> Any:
        """Get the actual value (use with caution)."""
        return self._value

    def __str__(self) -> str:
        return MASK

    def __repr__(self) -> str:
        return f"SensitiveValue({MASK})"

    def __bool__(self) -> bool:
        return bool(self._value)
