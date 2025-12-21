"""Log formatters for structured and human-readable output.

This module provides formatters for different logging output formats:
- JSON structured logging for machine parsing
- Human-readable console output
- Rich-enhanced console output
"""

from __future__ import annotations

import json
import logging
import traceback
from datetime import datetime, timezone
from typing import Any

from .context import get_context
from .masking import mask_dict, mask_sensitive_string


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging output.

    Produces log records in JSON format with consistent field names,
    suitable for ingestion by log aggregation systems like ELK or Splunk.
    """

    def __init__(
        self,
        include_timestamp: bool = True,
        include_context: bool = True,
        mask_sensitive: bool = True,
        extra_fields: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the JSON formatter.

        Args:
            include_timestamp: Include ISO timestamp in output
            include_context: Include correlation ID and context fields
            mask_sensitive: Mask sensitive data in log messages
            extra_fields: Additional static fields to include in every log
        """
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_context = include_context
        self.mask_sensitive = mask_sensitive
        self.extra_fields = extra_fields or {}

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON.

        Args:
            record: The log record to format

        Returns:
            JSON string representation of the log record
        """
        log_data: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": self._format_message(record),
        }

        # Add timestamp
        if self.include_timestamp:
            log_data["timestamp"] = datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat()

        # Add source location
        log_data["source"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
        }

        # Add context (correlation ID, etc.)
        if self.include_context:
            ctx = get_context()
            log_data["context"] = ctx.to_dict()

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self._format_exception(record.exc_info),
            }

        # Add any extra fields from the record
        if hasattr(record, "extra_data") and record.extra_data:
            extra = record.extra_data
            if self.mask_sensitive:
                extra = mask_dict(extra) if isinstance(extra, dict) else extra
            log_data["extra"] = extra

        # Add static extra fields
        log_data.update(self.extra_fields)

        return json.dumps(log_data, default=str)

    def _format_message(self, record: logging.LogRecord) -> str:
        """Format the log message, optionally masking sensitive data.

        Args:
            record: The log record

        Returns:
            Formatted (and potentially masked) message
        """
        message = record.getMessage()
        if self.mask_sensitive:
            message = mask_sensitive_string(message)
        return message

    def _format_exception(self, exc_info: tuple[Any, ...] | None) -> str | None:
        """Format exception traceback.

        Args:
            exc_info: Exception info tuple

        Returns:
            Formatted traceback string or None
        """
        if exc_info and exc_info[0]:
            return "".join(traceback.format_exception(*exc_info))
        return None


class StandardFormatter(logging.Formatter):
    """Standard human-readable formatter with context support.

    Format: TIMESTAMP - LEVEL - LOGGER - [CORRELATION_ID] - MESSAGE
    """

    DEFAULT_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - [%(correlation_id)s] - %(message)s"
    DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        mask_sensitive: bool = True,
    ) -> None:
        """Initialize the standard formatter.

        Args:
            fmt: Log format string
            datefmt: Date format string
            mask_sensitive: Mask sensitive data in log messages
        """
        super().__init__(
            fmt=fmt or self.DEFAULT_FORMAT,
            datefmt=datefmt or self.DEFAULT_DATE_FORMAT,
        )
        self.mask_sensitive = mask_sensitive

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record.

        Args:
            record: The log record to format

        Returns:
            Formatted string representation
        """
        # Add correlation ID to record
        ctx = get_context()
        record.correlation_id = ctx.correlation_id

        # Mask sensitive data in message
        if self.mask_sensitive:
            original_msg = record.msg
            if isinstance(original_msg, str):
                record.msg = mask_sensitive_string(original_msg)

        result = super().format(record)

        # Restore original message
        if self.mask_sensitive:
            record.msg = original_msg

        return result


class CompactFormatter(logging.Formatter):
    """Compact formatter for CLI output.

    Format: [LEVEL] MESSAGE
    """

    LEVEL_STYLES = {
        "DEBUG": "DEBUG",
        "INFO": "INFO ",
        "WARNING": "WARN ",
        "ERROR": "ERROR",
        "CRITICAL": "CRIT ",
    }

    def __init__(self, mask_sensitive: bool = True) -> None:
        """Initialize the compact formatter.

        Args:
            mask_sensitive: Mask sensitive data in log messages
        """
        super().__init__()
        self.mask_sensitive = mask_sensitive

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record compactly.

        Args:
            record: The log record to format

        Returns:
            Compact formatted string
        """
        level = self.LEVEL_STYLES.get(record.levelname, record.levelname)
        message = record.getMessage()

        if self.mask_sensitive:
            message = mask_sensitive_string(message)

        return f"[{level}] {message}"
