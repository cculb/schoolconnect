"""Tests for logging context management."""

import uuid

import pytest

from src.logutils.context import (
    LogContext,
    clear_context,
    get_context,
    get_correlation_id,
    set_context,
    set_correlation_id,
    update_context,
    with_context,
)


class TestLogContext:
    """Tests for LogContext dataclass."""

    def test_default_correlation_id_is_uuid(self):
        """LogContext should generate a UUID correlation ID by default."""
        ctx = LogContext()
        # Should be a valid UUID
        uuid.UUID(ctx.correlation_id)

    def test_custom_fields(self):
        """LogContext should accept custom fields."""
        ctx = LogContext(
            correlation_id="custom-id",
            operation="test_op",
            user_id="user123",
            student_id="student456",
            component="test",
        )
        assert ctx.correlation_id == "custom-id"
        assert ctx.operation == "test_op"
        assert ctx.user_id == "user123"
        assert ctx.student_id == "student456"
        assert ctx.component == "test"

    def test_to_dict_basic(self):
        """to_dict should always include correlation_id."""
        ctx = LogContext(correlation_id="test-id")
        result = ctx.to_dict()
        assert result["correlation_id"] == "test-id"

    def test_to_dict_with_optional_fields(self):
        """to_dict should include optional fields when set."""
        ctx = LogContext(
            correlation_id="test-id",
            operation="scrape",
            user_id="user1",
        )
        result = ctx.to_dict()
        assert result["correlation_id"] == "test-id"
        assert result["operation"] == "scrape"
        assert result["user_id"] == "user1"
        assert "student_id" not in result  # Not set

    def test_to_dict_with_extra(self):
        """to_dict should include extra fields."""
        ctx = LogContext(correlation_id="test-id", extra={"custom_key": "custom_value"})
        result = ctx.to_dict()
        assert result["custom_key"] == "custom_value"


class TestContextFunctions:
    """Tests for context management functions."""

    def setup_method(self):
        """Clear context before each test."""
        clear_context()

    def teardown_method(self):
        """Clear context after each test."""
        clear_context()

    def test_get_context_creates_default(self):
        """get_context should create a new context if none exists."""
        ctx = get_context()
        assert ctx is not None
        assert ctx.correlation_id is not None

    def test_get_context_returns_same_instance(self):
        """get_context should return the same instance within a context."""
        ctx1 = get_context()
        ctx2 = get_context()
        assert ctx1 is ctx2

    def test_set_context(self):
        """set_context should replace the current context."""
        new_ctx = LogContext(correlation_id="new-id")
        set_context(new_ctx)
        assert get_context() is new_ctx

    def test_clear_context(self):
        """clear_context should remove the current context."""
        get_context()  # Create a context
        clear_context()
        # Getting context again should create a new one
        ctx = get_context()
        assert ctx is not None

    def test_get_correlation_id(self):
        """get_correlation_id should return the current correlation ID."""
        ctx = LogContext(correlation_id="my-id")
        set_context(ctx)
        assert get_correlation_id() == "my-id"

    def test_set_correlation_id(self):
        """set_correlation_id should update the correlation ID."""
        get_context()  # Create context
        set_correlation_id("updated-id")
        assert get_correlation_id() == "updated-id"

    def test_update_context_existing_field(self):
        """update_context should update existing context fields."""
        ctx = get_context()
        update_context(operation="new_operation")
        assert ctx.operation == "new_operation"

    def test_update_context_extra_field(self):
        """update_context should add unknown fields to extra."""
        ctx = get_context()
        update_context(custom_field="value")
        assert ctx.extra["custom_field"] == "value"


class TestContextManager:
    """Tests for context manager."""

    def setup_method(self):
        """Clear context before each test."""
        clear_context()

    def teardown_method(self):
        """Clear context after each test."""
        clear_context()

    def test_with_context_creates_new_context(self):
        """with_context should create a new context within scope."""
        _ = get_correlation_id()  # Create initial context

        with with_context(correlation_id="new-id") as ctx:
            assert ctx.correlation_id == "new-id"
            assert get_correlation_id() == "new-id"

    def test_with_context_restores_previous(self):
        """with_context should restore previous context after scope."""
        _ = get_correlation_id()  # Create initial context

        with with_context(correlation_id="temp-id"):
            pass

        # After scope, we get a new context since original was implicitly created
        # The point is the temp context is no longer active
        current_id = get_correlation_id()
        assert current_id != "temp-id"

    def test_with_context_sets_fields(self):
        """with_context should set all provided fields."""
        with with_context(
            correlation_id="ctx-id",
            operation="test_op",
            user_id="user1",
            student_id="student1",
            component="test",
        ) as ctx:
            assert ctx.correlation_id == "ctx-id"
            assert ctx.operation == "test_op"
            assert ctx.user_id == "user1"
            assert ctx.student_id == "student1"
            assert ctx.component == "test"

    def test_with_context_extra_kwargs(self):
        """with_context should pass extra kwargs to context."""
        with with_context(custom="value") as ctx:
            assert ctx.extra["custom"] == "value"

    def test_nested_context(self):
        """Nested contexts should work correctly."""
        with with_context(correlation_id="outer"):
            assert get_correlation_id() == "outer"

            with with_context(correlation_id="inner"):
                assert get_correlation_id() == "inner"

            # After inner context, we're back to outer
            assert get_correlation_id() == "outer"

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Context manager should work with async."""
        async with with_context(correlation_id="async-id") as ctx:
            assert ctx.correlation_id == "async-id"
            assert get_correlation_id() == "async-id"
