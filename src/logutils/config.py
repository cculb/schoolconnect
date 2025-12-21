"""Logging configuration for SchoolConnect.

This module provides environment-aware logging configuration with
sensible defaults for development, testing, and production environments.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class Environment(Enum):
    """Application environment enumeration."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"
    CI = "ci"


class LogOutput(Enum):
    """Log output destination enumeration."""

    CONSOLE = "console"
    FILE = "file"
    BOTH = "both"
    JSON = "json"


@dataclass
class LogConfig:
    """Logging configuration container."""

    # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    level: str = "INFO"

    # Output destination
    output: LogOutput = LogOutput.CONSOLE

    # Use structured JSON format
    json_format: bool = False

    # Use Rich console output (if available)
    use_rich: bool = True

    # Mask sensitive data
    mask_sensitive: bool = True

    # Include correlation ID in logs
    include_correlation_id: bool = True

    # Log file path (for file output)
    log_file: Path | None = None

    # Max log file size in bytes (default 10MB)
    max_file_size: int = 10 * 1024 * 1024

    # Number of backup files to keep
    backup_count: int = 5

    # Per-module log levels
    module_levels: dict[str, str] = field(default_factory=dict)

    # Extra fields to include in all logs
    extra_fields: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> LogConfig:
        """Create configuration from environment variables.

        Environment variables:
            LOG_LEVEL: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            LOG_OUTPUT: Output destination (console, file, both, json)
            LOG_JSON: Use JSON format (true/false)
            LOG_RICH: Use Rich console (true/false)
            LOG_MASK_SENSITIVE: Mask sensitive data (true/false)
            LOG_FILE: Log file path
            LOG_MAX_SIZE: Max file size in bytes
            LOG_BACKUP_COUNT: Number of backup files

        Returns:
            LogConfig instance configured from environment
        """
        env = cls._detect_environment()

        # Start with environment-appropriate defaults
        config = cls._get_defaults_for_env(env)

        # Override with environment variables
        if level := os.getenv("LOG_LEVEL"):
            config.level = level.upper()

        if output := os.getenv("LOG_OUTPUT"):
            try:
                config.output = LogOutput(output.lower())
            except ValueError:
                pass

        if json_format := os.getenv("LOG_JSON"):
            config.json_format = json_format.lower() in ("true", "1", "yes")

        if use_rich := os.getenv("LOG_RICH"):
            config.use_rich = use_rich.lower() in ("true", "1", "yes")

        if mask_sensitive := os.getenv("LOG_MASK_SENSITIVE"):
            config.mask_sensitive = mask_sensitive.lower() in ("true", "1", "yes")

        if log_file := os.getenv("LOG_FILE"):
            config.log_file = Path(log_file)

        if max_size := os.getenv("LOG_MAX_SIZE"):
            try:
                config.max_file_size = int(max_size)
            except ValueError:
                pass

        if backup_count := os.getenv("LOG_BACKUP_COUNT"):
            try:
                config.backup_count = int(backup_count)
            except ValueError:
                pass

        return config

    @staticmethod
    def _detect_environment() -> Environment:
        """Detect the current runtime environment.

        Returns:
            Detected environment
        """
        # Check for CI environment
        if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
            return Environment.CI

        # Check for explicit environment setting
        env_name = os.getenv("ENVIRONMENT", os.getenv("ENV", "")).lower()
        if env_name in ("prod", "production"):
            return Environment.PRODUCTION
        if env_name in ("test", "testing"):
            return Environment.TESTING

        # Check for pytest
        if os.getenv("PYTEST_CURRENT_TEST"):
            return Environment.TESTING

        return Environment.DEVELOPMENT

    @classmethod
    def _get_defaults_for_env(cls, env: Environment) -> LogConfig:
        """Get default configuration for an environment.

        Args:
            env: The environment

        Returns:
            LogConfig with environment-appropriate defaults
        """
        if env == Environment.PRODUCTION:
            return cls(
                level="INFO",
                output=LogOutput.BOTH,
                json_format=True,
                use_rich=False,
                mask_sensitive=True,
                include_correlation_id=True,
            )

        if env == Environment.CI:
            return cls(
                level="INFO",
                output=LogOutput.CONSOLE,
                json_format=False,
                use_rich=False,
                mask_sensitive=True,
                include_correlation_id=True,
            )

        if env == Environment.TESTING:
            return cls(
                level="DEBUG",
                output=LogOutput.CONSOLE,
                json_format=False,
                use_rich=False,
                mask_sensitive=True,
                include_correlation_id=True,
            )

        # Development
        return cls(
            level="DEBUG",
            output=LogOutput.CONSOLE,
            json_format=False,
            use_rich=True,
            mask_sensitive=True,
            include_correlation_id=True,
        )


# Global configuration instance
_config: LogConfig | None = None


def get_config() -> LogConfig:
    """Get the current logging configuration.

    Returns:
        Current LogConfig instance
    """
    global _config
    if _config is None:
        _config = LogConfig.from_env()
    return _config


def set_config(config: LogConfig) -> None:
    """Set the logging configuration.

    Args:
        config: New LogConfig to use
    """
    global _config
    _config = config


def reset_config() -> None:
    """Reset to default configuration from environment."""
    global _config
    _config = None
