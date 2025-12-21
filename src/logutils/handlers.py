"""Custom log handlers for SchoolConnect.

This module provides specialized handlers for different output targets:
- Rich console handler for enhanced CLI output
- Rotating file handler with automatic cleanup
- Async-safe handler for MCP server
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import IO

try:
    from rich.console import Console
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class RichConsoleHandler(logging.Handler):
    """Log handler that outputs to Rich console with styling.

    This handler provides colorized, formatted output using the Rich library.
    Falls back to standard StreamHandler if Rich is not available.
    """

    LEVEL_STYLES = {
        "DEBUG": "dim",
        "INFO": "blue",
        "WARNING": "yellow",
        "ERROR": "red bold",
        "CRITICAL": "red bold reverse",
    }

    def __init__(
        self,
        console: Console | None = None,
        show_path: bool = False,
        show_time: bool = True,
        markup: bool = True,
    ) -> None:
        """Initialize the Rich console handler.

        Args:
            console: Rich Console instance (creates new if None)
            show_path: Show file path and line number
            show_time: Show timestamp
            markup: Enable Rich markup in messages
        """
        super().__init__()

        if RICH_AVAILABLE:
            self.console = console or Console(stderr=True)
        else:
            self.console = None

        self.show_path = show_path
        self.show_time = show_time
        self.markup = markup

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to the Rich console.

        Args:
            record: The log record to emit
        """
        try:
            message = self.format(record)

            if self.console and RICH_AVAILABLE:
                style = self.LEVEL_STYLES.get(record.levelname, "")
                text = Text()

                # Add level indicator
                level_text = Text(f"[{record.levelname:8}]", style=style)
                text.append(level_text)
                text.append(" ")

                # Add message
                if self.markup:
                    text.append(message)
                else:
                    text.append(Text(message))

                # Add path if requested
                if self.show_path:
                    path_text = Text(
                        f" ({record.filename}:{record.lineno})",
                        style="dim",
                    )
                    text.append(path_text)

                self.console.print(text)
            else:
                # Fallback to stderr
                sys.stderr.write(f"[{record.levelname:8}] {message}\n")
                sys.stderr.flush()

        except Exception:
            self.handleError(record)


class SafeRotatingFileHandler(RotatingFileHandler):
    """Rotating file handler with safe defaults and automatic directory creation.

    This handler extends RotatingFileHandler with:
    - Automatic log directory creation
    - Configurable backup count
    - UTF-8 encoding by default
    """

    DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    DEFAULT_BACKUP_COUNT = 5

    def __init__(
        self,
        filename: str | Path,
        max_bytes: int = DEFAULT_MAX_BYTES,
        backup_count: int = DEFAULT_BACKUP_COUNT,
        encoding: str = "utf-8",
    ) -> None:
        """Initialize the rotating file handler.

        Args:
            filename: Path to the log file
            max_bytes: Maximum size before rotation
            backup_count: Number of backup files to keep
            encoding: File encoding
        """
        # Ensure directory exists
        log_path = Path(filename)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        super().__init__(
            filename=str(log_path),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding=encoding,
        )


class BufferingHandler(logging.Handler):
    """Handler that buffers log records for batch processing.

    Useful for collecting logs during a specific operation and
    processing them together (e.g., for testing or batch uploads).
    """

    def __init__(self, capacity: int = 1000) -> None:
        """Initialize the buffering handler.

        Args:
            capacity: Maximum number of records to buffer
        """
        super().__init__()
        self.capacity = capacity
        self.buffer: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        """Add a record to the buffer.

        Args:
            record: The log record to buffer
        """
        self.buffer.append(record)
        if len(self.buffer) > self.capacity:
            self.buffer.pop(0)

    def get_records(self) -> list[logging.LogRecord]:
        """Get all buffered records.

        Returns:
            List of buffered log records
        """
        return list(self.buffer)

    def clear(self) -> None:
        """Clear the buffer."""
        self.buffer.clear()


class StreamHandlerWithFlush(logging.StreamHandler):
    """StreamHandler that always flushes after each emit.

    Useful for ensuring immediate output in CI/CD environments.
    """

    def __init__(self, stream: IO[str] | None = None) -> None:
        """Initialize the stream handler.

        Args:
            stream: Output stream (defaults to stderr)
        """
        super().__init__(stream or sys.stderr)

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a record and flush the stream.

        Args:
            record: The log record to emit
        """
        try:
            super().emit(record)
            self.flush()
        except Exception:
            self.handleError(record)
