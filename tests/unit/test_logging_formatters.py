"""Tests for log formatters."""

import json
import logging

import pytest

from src.logutils.context import clear_context, with_context
from src.logutils.formatters import CompactFormatter, JSONFormatter, StandardFormatter


@pytest.fixture(autouse=True)
def clear_log_context():
    """Clear log context before and after each test."""
    clear_context()
    yield
    clear_context()


class TestJSONFormatter:
    """Tests for JSONFormatter."""

    def create_log_record(
        self,
        msg: str = "Test message",
        level: int = logging.INFO,
        name: str = "test.logger",
        exc_info: tuple | None = None,
    ) -> logging.LogRecord:
        """Create a log record for testing."""
        record = logging.LogRecord(
            name=name,
            level=level,
            pathname="/test/file.py",
            lineno=42,
            msg=msg,
            args=(),
            exc_info=exc_info,
        )
        return record

    def test_basic_format(self):
        """Basic log record should format as valid JSON."""
        formatter = JSONFormatter()
        record = self.create_log_record("Hello world")
        output = formatter.format(record)

        data = json.loads(output)
        assert data["level"] == "INFO"
        assert data["message"] == "Hello world"
        assert data["logger"] == "test.logger"

    def test_includes_timestamp(self):
        """Output should include ISO timestamp by default."""
        formatter = JSONFormatter(include_timestamp=True)
        record = self.create_log_record()
        output = formatter.format(record)

        data = json.loads(output)
        assert "timestamp" in data
        # Should be ISO format
        assert "T" in data["timestamp"]

    def test_excludes_timestamp_when_disabled(self):
        """Output should not include timestamp when disabled."""
        formatter = JSONFormatter(include_timestamp=False)
        record = self.create_log_record()
        output = formatter.format(record)

        data = json.loads(output)
        assert "timestamp" not in data

    def test_includes_source_location(self):
        """Output should include source file and line."""
        formatter = JSONFormatter()
        record = self.create_log_record()
        output = formatter.format(record)

        data = json.loads(output)
        assert "source" in data
        assert data["source"]["line"] == 42
        assert "file.py" in data["source"]["file"]

    def test_includes_correlation_id(self):
        """Output should include correlation ID from context."""
        formatter = JSONFormatter(include_context=True)

        with with_context(correlation_id="test-correlation-id"):
            record = self.create_log_record()
            output = formatter.format(record)

        data = json.loads(output)
        assert "context" in data
        assert data["context"]["correlation_id"] == "test-correlation-id"

    def test_includes_context_fields(self):
        """Output should include all context fields."""
        formatter = JSONFormatter(include_context=True)

        with with_context(
            correlation_id="ctx-id",
            operation="test_op",
            user_id="user123",
        ):
            record = self.create_log_record()
            output = formatter.format(record)

        data = json.loads(output)
        assert data["context"]["operation"] == "test_op"
        assert data["context"]["user_id"] == "user123"

    def test_masks_sensitive_data(self):
        """Sensitive data in message should be masked."""
        formatter = JSONFormatter(mask_sensitive=True)
        record = self.create_log_record("Login with password=secret123")
        output = formatter.format(record)

        data = json.loads(output)
        assert "secret123" not in data["message"]

    def test_no_masking_when_disabled(self):
        """Sensitive data should not be masked when disabled."""
        formatter = JSONFormatter(mask_sensitive=False)
        record = self.create_log_record("Login with password=secret123")
        output = formatter.format(record)

        data = json.loads(output)
        assert "secret123" in data["message"]

    def test_exception_info(self):
        """Exception info should be included when present."""
        formatter = JSONFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            record = self.create_log_record("Error occurred", exc_info=sys.exc_info())

        output = formatter.format(record)
        data = json.loads(output)

        assert "exception" in data
        assert data["exception"]["type"] == "ValueError"
        assert "Test error" in data["exception"]["message"]
        assert "traceback" in data["exception"]

    def test_extra_fields(self):
        """Extra static fields should be included."""
        formatter = JSONFormatter(extra_fields={"app": "schoolconnect", "version": "1.0"})
        record = self.create_log_record()
        output = formatter.format(record)

        data = json.loads(output)
        assert data["app"] == "schoolconnect"
        assert data["version"] == "1.0"

    def test_extra_data_from_record(self):
        """Extra data attached to record should be included."""
        formatter = JSONFormatter()
        record = self.create_log_record()
        record.extra_data = {"count": 42, "status": "success"}
        output = formatter.format(record)

        data = json.loads(output)
        assert "extra" in data
        assert data["extra"]["count"] == 42


class TestStandardFormatter:
    """Tests for StandardFormatter."""

    def create_log_record(
        self,
        msg: str = "Test message",
        level: int = logging.INFO,
        name: str = "test.logger",
    ) -> logging.LogRecord:
        """Create a log record for testing."""
        record = logging.LogRecord(
            name=name,
            level=level,
            pathname="/test/file.py",
            lineno=42,
            msg=msg,
            args=(),
            exc_info=None,
        )
        return record

    def test_includes_correlation_id(self):
        """Output should include correlation ID."""
        formatter = StandardFormatter()

        with with_context(correlation_id="std-corr-id"):
            record = self.create_log_record()
            output = formatter.format(record)

        assert "std-corr-id" in output

    def test_includes_level_and_logger(self):
        """Output should include level and logger name."""
        formatter = StandardFormatter()
        record = self.create_log_record()
        output = formatter.format(record)

        assert "INFO" in output
        assert "test.logger" in output

    def test_masks_sensitive_data(self):
        """Sensitive data should be masked."""
        formatter = StandardFormatter(mask_sensitive=True)
        record = self.create_log_record("password=mysecret")
        output = formatter.format(record)

        assert "mysecret" not in output

    def test_custom_format(self):
        """Custom format string should be used."""
        formatter = StandardFormatter(fmt="%(levelname)s: %(message)s")
        record = self.create_log_record("Hello")
        output = formatter.format(record)

        assert output.startswith("INFO:")


class TestCompactFormatter:
    """Tests for CompactFormatter."""

    def create_log_record(
        self,
        msg: str = "Test message",
        level: int = logging.INFO,
    ) -> logging.LogRecord:
        """Create a log record for testing."""
        record = logging.LogRecord(
            name="test",
            level=level,
            pathname="/test/file.py",
            lineno=42,
            msg=msg,
            args=(),
            exc_info=None,
        )
        return record

    def test_compact_format(self):
        """Output should be compact [LEVEL] MESSAGE format."""
        formatter = CompactFormatter()
        record = self.create_log_record("Hello world")
        output = formatter.format(record)

        assert output == "[INFO ] Hello world"

    def test_level_styles(self):
        """Different levels should use appropriate styles."""
        formatter = CompactFormatter()

        for level, expected in [
            (logging.DEBUG, "DEBUG"),
            (logging.INFO, "INFO "),
            (logging.WARNING, "WARN "),
            (logging.ERROR, "ERROR"),
            (logging.CRITICAL, "CRIT "),
        ]:
            record = self.create_log_record(level=level)
            output = formatter.format(record)
            assert f"[{expected}]" in output

    def test_masks_sensitive_data(self):
        """Sensitive data should be masked."""
        formatter = CompactFormatter(mask_sensitive=True)
        record = self.create_log_record("token=abc123")
        output = formatter.format(record)

        assert "abc123" not in output
