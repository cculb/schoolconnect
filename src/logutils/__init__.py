"""SchoolConnect Logging Infrastructure.

This module provides a comprehensive logging solution with:
- Structured JSON logging for production
- Rich console output for development
- Correlation ID tracking for request tracing
- Sensitive data masking for security
- Environment-aware configuration

Usage:
    from src.logging import get_logger, with_context

    logger = get_logger(__name__)

    with with_context(operation="scrape", student_id="12345"):
        logger.info("Starting scrape operation")

    # With extra structured data
    logger.info("Processed records", extra={"extra_data": {"count": 42}})
"""

from .config import Environment, LogConfig, LogOutput, get_config, reset_config, set_config
from .context import (
    ContextManager,
    LogContext,
    clear_context,
    get_context,
    get_correlation_id,
    set_context,
    set_correlation_id,
    update_context,
    with_context,
)
from .formatters import CompactFormatter, JSONFormatter, StandardFormatter
from .handlers import (
    BufferingHandler,
    RichConsoleHandler,
    SafeRotatingFileHandler,
    StreamHandlerWithFlush,
)
from .logger import (
    LoggerAdapter,
    configure_root_logger,
    get_logger,
    reset_logging,
    with_extra,
)
from .masking import (
    MASK,
    SensitiveValue,
    is_sensitive_key,
    mask_dict,
    mask_sensitive_string,
)

__all__ = [
    # Core logger functions
    "get_logger",
    "configure_root_logger",
    "reset_logging",
    "with_extra",
    "LoggerAdapter",
    # Context management
    "with_context",
    "get_context",
    "set_context",
    "clear_context",
    "get_correlation_id",
    "set_correlation_id",
    "update_context",
    "LogContext",
    "ContextManager",
    # Configuration
    "LogConfig",
    "LogOutput",
    "Environment",
    "get_config",
    "set_config",
    "reset_config",
    # Formatters
    "JSONFormatter",
    "StandardFormatter",
    "CompactFormatter",
    # Handlers
    "RichConsoleHandler",
    "SafeRotatingFileHandler",
    "BufferingHandler",
    "StreamHandlerWithFlush",
    # Masking
    "mask_sensitive_string",
    "mask_dict",
    "is_sensitive_key",
    "SensitiveValue",
    "MASK",
]
