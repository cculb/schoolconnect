"""Logger factory and utilities for SchoolConnect.

This module provides the main interface for creating and configuring
loggers throughout the application.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

from .config import LogConfig, LogOutput, get_config
from .formatters import CompactFormatter, JSONFormatter, StandardFormatter
from .handlers import RichConsoleHandler, SafeRotatingFileHandler, StreamHandlerWithFlush

# Track configured loggers
_configured_loggers: set[str] = set()
_root_configured: bool = False


def get_logger(
    name: str | None = None,
    config: LogConfig | None = None,
) -> logging.Logger:
    """Get a configured logger instance.

    Args:
        name: Logger name (usually __name__)
        config: Optional LogConfig to use

    Returns:
        Configured Logger instance
    """
    logger = logging.getLogger(name)

    # Configure if not already done
    if name not in _configured_loggers:
        _configure_logger(logger, config or get_config())
        _configured_loggers.add(name or "root")

    return logger


def _configure_logger(logger: logging.Logger, config: LogConfig) -> None:
    """Configure a logger with handlers and formatters.

    Args:
        logger: Logger to configure
        config: Configuration to apply
    """
    # Set log level
    level = config.module_levels.get(logger.name, config.level)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    logger.handlers.clear()

    # Don't propagate to root unless this is the root logger
    if logger.name:
        logger.propagate = False

    # Add handlers based on configuration
    handlers = _create_handlers(config)
    for handler in handlers:
        logger.addHandler(handler)


def _create_handlers(config: LogConfig) -> list[logging.Handler]:
    """Create handlers based on configuration.

    Args:
        config: Log configuration

    Returns:
        List of configured handlers
    """
    handlers: list[logging.Handler] = []

    # Console handler
    if config.output in (LogOutput.CONSOLE, LogOutput.BOTH):
        if config.json_format:
            handler = StreamHandlerWithFlush(sys.stderr)
            handler.setFormatter(
                JSONFormatter(
                    mask_sensitive=config.mask_sensitive,
                    extra_fields=config.extra_fields,
                )
            )
        elif config.use_rich:
            handler = RichConsoleHandler()
            handler.setFormatter(CompactFormatter(mask_sensitive=config.mask_sensitive))
        else:
            handler = StreamHandlerWithFlush(sys.stderr)
            handler.setFormatter(StandardFormatter(mask_sensitive=config.mask_sensitive))

        handlers.append(handler)

    # JSON-only output
    if config.output == LogOutput.JSON:
        handler = StreamHandlerWithFlush(sys.stderr)
        handler.setFormatter(
            JSONFormatter(
                mask_sensitive=config.mask_sensitive,
                extra_fields=config.extra_fields,
            )
        )
        handlers.append(handler)

    # File handler
    if config.output in (LogOutput.FILE, LogOutput.BOTH) and config.log_file:
        handler = SafeRotatingFileHandler(
            filename=config.log_file,
            max_bytes=config.max_file_size,
            backup_count=config.backup_count,
        )
        # Always use JSON for file output
        handler.setFormatter(
            JSONFormatter(
                mask_sensitive=config.mask_sensitive,
                extra_fields=config.extra_fields,
            )
        )
        handlers.append(handler)

    return handlers


def configure_root_logger(config: LogConfig | None = None) -> None:
    """Configure the root logger for the application.

    This should be called once at application startup.

    Args:
        config: Optional configuration to use
    """
    global _root_configured

    if _root_configured:
        return

    cfg = config or get_config()
    root_logger = logging.getLogger()

    # Clear existing handlers
    root_logger.handlers.clear()

    # Configure root logger
    _configure_logger(root_logger, cfg)
    _root_configured = True


def reset_logging() -> None:
    """Reset all logging configuration.

    Useful for testing or reinitializing logging.
    """
    global _configured_loggers, _root_configured

    # Clear all handlers from configured loggers
    for name in _configured_loggers:
        logger = logging.getLogger(name if name != "root" else None)
        logger.handlers.clear()

    _configured_loggers.clear()
    _root_configured = False


class LoggerAdapter(logging.LoggerAdapter):
    """Adapter that adds extra context to log messages.

    This adapter allows adding structured extra data to log messages
    that will be included in the JSON output.
    """

    def __init__(self, logger: logging.Logger, extra: dict[str, Any] | None = None) -> None:
        """Initialize the adapter.

        Args:
            logger: Base logger
            extra: Extra data to include in all logs
        """
        super().__init__(logger, extra or {})

    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """Process a log message to add extra data.

        Args:
            msg: Log message
            kwargs: Keyword arguments

        Returns:
            Tuple of processed message and kwargs
        """
        # Combine adapter extra with call-time extra
        extra = {**self.extra, **kwargs.get("extra", {})}
        kwargs["extra"] = {"extra_data": extra}
        return msg, kwargs

    def debug_with_data(self, msg: str, **data: Any) -> None:
        """Log debug message with structured data."""
        self.debug(msg, extra={"extra_data": data})

    def info_with_data(self, msg: str, **data: Any) -> None:
        """Log info message with structured data."""
        self.info(msg, extra={"extra_data": data})

    def warning_with_data(self, msg: str, **data: Any) -> None:
        """Log warning message with structured data."""
        self.warning(msg, extra={"extra_data": data})

    def error_with_data(self, msg: str, **data: Any) -> None:
        """Log error message with structured data."""
        self.error(msg, extra={"extra_data": data})


def with_extra(logger: logging.Logger, **extra: Any) -> LoggerAdapter:
    """Create a logger adapter with extra context.

    Args:
        logger: Base logger
        **extra: Extra context to include

    Returns:
        LoggerAdapter with extra context
    """
    return LoggerAdapter(logger, extra)
