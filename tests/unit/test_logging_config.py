"""Tests for logging configuration."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.logutils.config import (
    Environment,
    LogConfig,
    LogOutput,
    get_config,
    reset_config,
    set_config,
)


@pytest.fixture(autouse=True)
def reset_global_config():
    """Reset global config before and after each test."""
    reset_config()
    yield
    reset_config()


class TestLogConfig:
    """Tests for LogConfig dataclass."""

    def test_defaults(self):
        """LogConfig should have sensible defaults."""
        config = LogConfig()
        assert config.level == "INFO"
        assert config.output == LogOutput.CONSOLE
        assert config.json_format is False
        assert config.use_rich is True
        assert config.mask_sensitive is True
        assert config.include_correlation_id is True

    def test_custom_values(self):
        """LogConfig should accept custom values."""
        config = LogConfig(
            level="DEBUG",
            output=LogOutput.BOTH,
            json_format=True,
            use_rich=False,
            log_file=Path("/tmp/test.log"),
        )
        assert config.level == "DEBUG"
        assert config.output == LogOutput.BOTH
        assert config.json_format is True
        assert config.use_rich is False
        assert config.log_file == Path("/tmp/test.log")


class TestEnvironmentDetection:
    """Tests for environment detection."""

    @patch.dict(os.environ, {"CI": "true"}, clear=False)
    def test_detect_ci_env(self):
        """Should detect CI environment."""
        reset_config()
        config = LogConfig.from_env()
        assert config.use_rich is False  # CI default

    @patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=False)
    def test_detect_github_actions(self):
        """Should detect GitHub Actions environment."""
        reset_config()
        config = LogConfig.from_env()
        assert config.use_rich is False

    @patch.dict(os.environ, {"ENVIRONMENT": "production"}, clear=False)
    def test_detect_production(self):
        """Should detect production environment."""
        reset_config()
        config = LogConfig.from_env()
        assert config.json_format is True
        assert config.level == "INFO"

    @patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "test_something"}, clear=False)
    def test_detect_testing(self):
        """Should detect testing environment."""
        reset_config()
        config = LogConfig.from_env()
        assert config.level == "DEBUG"


class TestEnvironmentOverrides:
    """Tests for environment variable overrides."""

    @patch.dict(os.environ, {"LOG_LEVEL": "WARNING"}, clear=False)
    def test_log_level_override(self):
        """LOG_LEVEL should override default."""
        config = LogConfig.from_env()
        assert config.level == "WARNING"

    @patch.dict(os.environ, {"LOG_OUTPUT": "both"}, clear=False)
    def test_log_output_override(self):
        """LOG_OUTPUT should override default."""
        config = LogConfig.from_env()
        assert config.output == LogOutput.BOTH

    @patch.dict(os.environ, {"LOG_JSON": "true"}, clear=False)
    def test_log_json_override(self):
        """LOG_JSON should enable JSON format."""
        config = LogConfig.from_env()
        assert config.json_format is True

    @patch.dict(os.environ, {"LOG_RICH": "false"}, clear=False)
    def test_log_rich_override(self):
        """LOG_RICH should control Rich output."""
        config = LogConfig.from_env()
        assert config.use_rich is False

    @patch.dict(os.environ, {"LOG_MASK_SENSITIVE": "false"}, clear=False)
    def test_log_mask_sensitive_override(self):
        """LOG_MASK_SENSITIVE should control masking."""
        config = LogConfig.from_env()
        assert config.mask_sensitive is False

    @patch.dict(os.environ, {"LOG_FILE": "/var/log/app.log"}, clear=False)
    def test_log_file_override(self):
        """LOG_FILE should set log file path."""
        config = LogConfig.from_env()
        assert config.log_file == Path("/var/log/app.log")

    @patch.dict(os.environ, {"LOG_MAX_SIZE": "5000000"}, clear=False)
    def test_log_max_size_override(self):
        """LOG_MAX_SIZE should set max file size."""
        config = LogConfig.from_env()
        assert config.max_file_size == 5000000

    @patch.dict(os.environ, {"LOG_BACKUP_COUNT": "10"}, clear=False)
    def test_log_backup_count_override(self):
        """LOG_BACKUP_COUNT should set backup count."""
        config = LogConfig.from_env()
        assert config.backup_count == 10


class TestLogOutput:
    """Tests for LogOutput enum."""

    def test_enum_values(self):
        """LogOutput should have expected values."""
        assert LogOutput.CONSOLE.value == "console"
        assert LogOutput.FILE.value == "file"
        assert LogOutput.BOTH.value == "both"
        assert LogOutput.JSON.value == "json"


class TestEnvironment:
    """Tests for Environment enum."""

    def test_enum_values(self):
        """Environment should have expected values."""
        assert Environment.DEVELOPMENT.value == "development"
        assert Environment.TESTING.value == "testing"
        assert Environment.PRODUCTION.value == "production"
        assert Environment.CI.value == "ci"


class TestGlobalConfig:
    """Tests for global config functions."""

    def test_get_config_creates_default(self):
        """get_config should create default config."""
        config = get_config()
        assert config is not None
        assert isinstance(config, LogConfig)

    def test_get_config_returns_same_instance(self):
        """get_config should return same instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_set_config(self):
        """set_config should replace global config."""
        new_config = LogConfig(level="ERROR")
        set_config(new_config)
        assert get_config() is new_config
        assert get_config().level == "ERROR"

    def test_reset_config(self):
        """reset_config should clear global config."""
        get_config()  # Initialize
        reset_config()
        # Next get should create new instance
        config = get_config()
        assert config is not None


class TestEnvironmentDefaults:
    """Tests for environment-specific defaults."""

    def test_development_defaults(self):
        """Development environment should have debug-friendly defaults."""
        config = LogConfig._get_defaults_for_env(Environment.DEVELOPMENT)
        assert config.level == "DEBUG"
        assert config.use_rich is True
        assert config.json_format is False

    def test_production_defaults(self):
        """Production environment should have production-friendly defaults."""
        config = LogConfig._get_defaults_for_env(Environment.PRODUCTION)
        assert config.level == "INFO"
        assert config.json_format is True
        assert config.use_rich is False

    def test_ci_defaults(self):
        """CI environment should have CI-friendly defaults."""
        config = LogConfig._get_defaults_for_env(Environment.CI)
        assert config.use_rich is False
        assert config.json_format is False

    def test_testing_defaults(self):
        """Testing environment should have test-friendly defaults."""
        config = LogConfig._get_defaults_for_env(Environment.TESTING)
        assert config.level == "DEBUG"
        assert config.use_rich is False
