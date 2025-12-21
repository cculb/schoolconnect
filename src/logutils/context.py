"""Context management for logging with correlation IDs and request context.

This module provides thread-safe and async-safe context management using
Python's contextvars for propagating logging context across function calls.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LogContext:
    """Holds contextual information for logging."""

    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation: str | None = None
    user_id: str | None = None
    student_id: str | None = None
    component: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary for log enrichment."""
        result: dict[str, Any] = {"correlation_id": self.correlation_id}

        if self.operation:
            result["operation"] = self.operation
        if self.user_id:
            result["user_id"] = self.user_id
        if self.student_id:
            result["student_id"] = self.student_id
        if self.component:
            result["component"] = self.component

        result.update(self.extra)
        return result


# Context variable to hold the current log context
_log_context: ContextVar[LogContext | None] = ContextVar("log_context", default=None)


def get_context() -> LogContext:
    """Get the current log context, creating a new one if none exists."""
    ctx = _log_context.get()
    if ctx is None:
        ctx = LogContext()
        _log_context.set(ctx)
    return ctx


def set_context(context: LogContext) -> None:
    """Set the current log context."""
    _log_context.set(context)


def clear_context() -> None:
    """Clear the current log context."""
    _log_context.set(None)


def get_correlation_id() -> str:
    """Get the current correlation ID."""
    return get_context().correlation_id


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for the current context."""
    ctx = get_context()
    ctx.correlation_id = correlation_id


class ContextManager:
    """Context manager for managing log context within a scope."""

    def __init__(
        self,
        correlation_id: str | None = None,
        operation: str | None = None,
        user_id: str | None = None,
        student_id: str | None = None,
        component: str | None = None,
        **extra: Any,
    ) -> None:
        self.new_context = LogContext(
            correlation_id=correlation_id or str(uuid.uuid4()),
            operation=operation,
            user_id=user_id,
            student_id=student_id,
            component=component,
            extra=extra,
        )
        self._previous_context: LogContext | None = None
        self._token: Any = None

    def __enter__(self) -> LogContext:
        self._previous_context = _log_context.get()
        self._token = _log_context.set(self.new_context)
        return self.new_context

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        _log_context.set(self._previous_context)

    async def __aenter__(self) -> LogContext:
        return self.__enter__()

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.__exit__(exc_type, exc_val, exc_tb)


def with_context(
    correlation_id: str | None = None,
    operation: str | None = None,
    user_id: str | None = None,
    student_id: str | None = None,
    component: str | None = None,
    **extra: Any,
) -> ContextManager:
    """Create a context manager with the specified logging context.

    Usage:
        with with_context(operation="login", user_id="user123"):
            logger.info("Processing login")
    """
    return ContextManager(
        correlation_id=correlation_id,
        operation=operation,
        user_id=user_id,
        student_id=student_id,
        component=component,
        **extra,
    )


def update_context(**kwargs: Any) -> None:
    """Update the current context with additional fields."""
    ctx = get_context()
    for key, value in kwargs.items():
        if hasattr(ctx, key):
            setattr(ctx, key, value)
        else:
            ctx.extra[key] = value
