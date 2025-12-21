"""Tests for logger factory and utilities."""

import logging

import pytest

from src.logutils.config import LogConfig, LogOutput, reset_config
from src.logutils.logger import (
    LoggerAdapter,
    configure_root_logger,
    get_logger,
    reset_logging,
    with_extra,
)


@pytest.fixture(autouse=True)
def reset_all():
    """Reset logging and config before and after each test."""
    reset_logging()
    reset_config()
    yield
    reset_logging()
    reset_config()


class TestGetLogger:
    """Tests for get_logger function."""

    def test_returns_logger_instance(self):
        """get_logger should return a Logger instance."""
        logger = get_logger("test.module")
        assert isinstance(logger, logging.Logger)

    def test_logger_name(self):
        """Logger should have the specified name."""
        logger = get_logger("my.custom.logger")
        assert logger.name == "my.custom.logger"

    def test_none_name_returns_root(self):
        """None name should return root logger."""
        logger = get_logger(None)
        assert logger.name == "root"

    def test_configured_only_once(self):
        """Logger should only be configured once."""
        logger1 = get_logger("test.logger")
        handler_count = len(logger1.handlers)

        # Get same logger again
        logger2 = get_logger("test.logger")

        assert logger1 is logger2
        assert len(logger2.handlers) == handler_count

    def test_custom_config(self):
        """Logger should use provided config."""
        config = LogConfig(level="ERROR")
        logger = get_logger("error.logger", config=config)
        assert logger.level == logging.ERROR


class TestConfigureRootLogger:
    """Tests for configure_root_logger function."""

    def test_configures_root(self):
        """Should configure root logger."""
        configure_root_logger()
        root = logging.getLogger()
        assert len(root.handlers) > 0

    def test_only_configures_once(self):
        """Should only configure once."""
        configure_root_logger()
        handler_count = len(logging.getLogger().handlers)

        configure_root_logger()
        assert len(logging.getLogger().handlers) == handler_count


class TestResetLogging:
    """Tests for reset_logging function."""

    def test_clears_handlers(self):
        """Should clear handlers from configured loggers."""
        logger = get_logger("reset.test")
        assert len(logger.handlers) > 0

        reset_logging()

        # Logger still exists but handlers are cleared
        assert len(logger.handlers) == 0

    def test_allows_reconfiguration(self):
        """Should allow loggers to be reconfigured."""
        _ = get_logger("reconfig.test")
        reset_logging()

        # Should be able to get and configure again
        logger2 = get_logger("reconfig.test")
        assert len(logger2.handlers) > 0


class TestWithExtra:
    """Tests for with_extra function."""

    def test_returns_adapter(self):
        """with_extra should return a LoggerAdapter."""
        logger = get_logger("extra.test")
        adapter = with_extra(logger, user_id="123")
        assert isinstance(adapter, LoggerAdapter)

    def test_adapter_includes_extra(self):
        """Adapter should include extra data in logs."""
        logger = get_logger("extra.test2")
        adapter = with_extra(logger, custom_field="value")

        # The adapter stores extra data
        assert adapter.extra == {"custom_field": "value"}


class TestLoggerAdapter:
    """Tests for LoggerAdapter class."""

    def test_process_adds_extra_data(self):
        """process should add extra_data to kwargs."""
        logger = get_logger("adapter.test")
        adapter = LoggerAdapter(logger, {"key": "value"})

        msg, kwargs = adapter.process("Test", {})
        assert "extra" in kwargs
        assert kwargs["extra"]["extra_data"]["key"] == "value"

    def test_process_merges_extra(self):
        """process should merge adapter extra with call-time extra."""
        logger = get_logger("adapter.test2")
        adapter = LoggerAdapter(logger, {"key1": "value1"})

        msg, kwargs = adapter.process("Test", {"extra": {"key2": "value2"}})
        assert kwargs["extra"]["extra_data"]["key1"] == "value1"
        assert kwargs["extra"]["extra_data"]["key2"] == "value2"

    def test_debug_with_data(self):
        """debug_with_data should log with structured data."""
        logger = get_logger("adapter.debug")
        adapter = LoggerAdapter(logger, {})

        # Should not raise
        adapter.debug_with_data("Debug message", count=42)

    def test_info_with_data(self):
        """info_with_data should log with structured data."""
        logger = get_logger("adapter.info")
        adapter = LoggerAdapter(logger, {})

        # Should not raise
        adapter.info_with_data("Info message", status="ok")

    def test_warning_with_data(self):
        """warning_with_data should log with structured data."""
        logger = get_logger("adapter.warning")
        adapter = LoggerAdapter(logger, {})

        # Should not raise
        adapter.warning_with_data("Warning message", code=123)

    def test_error_with_data(self):
        """error_with_data should log with structured data."""
        logger = get_logger("adapter.error")
        adapter = LoggerAdapter(logger, {})

        # Should not raise
        adapter.error_with_data("Error message", error_type="test")


class TestLogOutput:
    """Tests for log output functionality."""

    def test_console_output(self):
        """Logger should output to console."""
        config = LogConfig(
            level="DEBUG",
            output=LogOutput.CONSOLE,
            use_rich=False,
        )
        logger = get_logger("console.test", config=config)

        # Should have at least one handler
        assert len(logger.handlers) > 0

    def test_json_output(self):
        """Logger should output JSON when configured."""
        config = LogConfig(
            level="DEBUG",
            output=LogOutput.JSON,
        )
        logger = get_logger("json.test", config=config)

        # Should have handler
        assert len(logger.handlers) > 0


class TestLogLevels:
    """Tests for log level configuration."""

    def test_debug_level(self):
        """DEBUG level should be configurable."""
        config = LogConfig(level="DEBUG")
        logger = get_logger("level.debug", config=config)
        assert logger.level == logging.DEBUG

    def test_info_level(self):
        """INFO level should be configurable."""
        config = LogConfig(level="INFO")
        logger = get_logger("level.info", config=config)
        assert logger.level == logging.INFO

    def test_warning_level(self):
        """WARNING level should be configurable."""
        config = LogConfig(level="WARNING")
        logger = get_logger("level.warning", config=config)
        assert logger.level == logging.WARNING

    def test_error_level(self):
        """ERROR level should be configurable."""
        config = LogConfig(level="ERROR")
        logger = get_logger("level.error", config=config)
        assert logger.level == logging.ERROR

    def test_module_specific_levels(self):
        """Module-specific levels should override default."""
        config = LogConfig(
            level="INFO",
            module_levels={"specific.module": "DEBUG"},
        )
        logger = get_logger("specific.module", config=config)
        assert logger.level == logging.DEBUG
