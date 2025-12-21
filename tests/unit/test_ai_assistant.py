"""Tests for AI assistant retry logic and error handling."""

from unittest.mock import MagicMock, patch

import pytest
from ai_assistant import (
    MAX_TOOL_ITERATIONS,
    ClientAPIError,
    RateLimitAPIError,
    ServerAPIError,
    categorize_error,
    get_ai_response,
)
from anthropic import (
    APIStatusError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    RateLimitError,
)
from httpx import Request, Response

pytestmark = pytest.mark.unit


class TestRetryOnRateLimit:
    """Test retry behavior on 429 rate limit errors."""

    @patch("ai_assistant.Anthropic")
    def test_retries_on_rate_limit_429(self, mock_anthropic_class):
        """Should retry on 429 rate limit and eventually succeed."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Create mock request for the error
        mock_request = Request(method="POST", url="https://api.anthropic.com/v1/messages")

        # First two calls raise rate limit, third succeeds
        rate_limit_error = RateLimitError(
            message="Rate limit exceeded",
            response=Response(status_code=429, request=mock_request),
            body={"error": {"message": "Rate limit exceeded"}},
        )

        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text="Success response", type="text")]
        mock_response.content[0].text = "Success response"

        mock_client.messages.create.side_effect = [
            rate_limit_error,
            rate_limit_error,
            mock_response,
        ]

        result = get_ai_response(
            user_message="Hello",
            student_context={"student_name": "Test"},
            chat_history=[],
            api_key="test-key",
        )

        assert "Success response" in result
        assert mock_client.messages.create.call_count == 3


class TestRetryOnServerErrors:
    """Test retry behavior on 5xx server errors."""

    @patch("ai_assistant.Anthropic")
    def test_retries_on_500_internal_server_error(self, mock_anthropic_class):
        """Should retry on 500 internal server error."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_request = Request(method="POST", url="https://api.anthropic.com/v1/messages")

        server_error = InternalServerError(
            message="Internal server error",
            response=Response(status_code=500, request=mock_request),
            body={"error": {"message": "Internal server error"}},
        )

        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text="Success after retry", type="text")]
        mock_response.content[0].text = "Success after retry"

        mock_client.messages.create.side_effect = [
            server_error,
            mock_response,
        ]

        result = get_ai_response(
            user_message="Hello",
            student_context={"student_name": "Test"},
            chat_history=[],
            api_key="test-key",
        )

        assert "Success after retry" in result
        assert mock_client.messages.create.call_count == 2

    @patch("ai_assistant.Anthropic")
    def test_retries_on_503_service_unavailable(self, mock_anthropic_class):
        """Should retry on 503 service unavailable."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_request = Request(method="POST", url="https://api.anthropic.com/v1/messages")

        # 503 is typically handled as InternalServerError or APIStatusError
        server_error = APIStatusError(
            message="Service unavailable",
            response=Response(status_code=503, request=mock_request),
            body={"error": {"message": "Service unavailable"}},
        )

        mock_response = MagicMock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = [MagicMock(text="Success after 503", type="text")]
        mock_response.content[0].text = "Success after 503"

        mock_client.messages.create.side_effect = [
            server_error,
            mock_response,
        ]

        result = get_ai_response(
            user_message="Hello",
            student_context={"student_name": "Test"},
            chat_history=[],
            api_key="test-key",
        )

        assert "Success after 503" in result
        assert mock_client.messages.create.call_count == 2


class TestNoRetryOnClientErrors:
    """Test that client errors (4xx except 429) are NOT retried."""

    @patch("ai_assistant.Anthropic")
    def test_no_retry_on_400_bad_request(self, mock_anthropic_class):
        """Should NOT retry on 400 bad request."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_request = Request(method="POST", url="https://api.anthropic.com/v1/messages")

        bad_request_error = BadRequestError(
            message="Invalid request",
            response=Response(status_code=400, request=mock_request),
            body={"error": {"message": "Invalid request format"}},
        )

        mock_client.messages.create.side_effect = bad_request_error

        result = get_ai_response(
            user_message="Hello",
            student_context={"student_name": "Test"},
            chat_history=[],
            api_key="test-key",
        )

        # Should only be called once - no retries
        assert mock_client.messages.create.call_count == 1
        assert "Error" in result or "error" in result.lower()

    @patch("ai_assistant.Anthropic")
    def test_no_retry_on_401_authentication_error(self, mock_anthropic_class):
        """Should NOT retry on 401 authentication error."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_request = Request(method="POST", url="https://api.anthropic.com/v1/messages")

        auth_error = AuthenticationError(
            message="Invalid API key",
            response=Response(status_code=401, request=mock_request),
            body={"error": {"message": "Invalid API key"}},
        )

        mock_client.messages.create.side_effect = auth_error

        result = get_ai_response(
            user_message="Hello",
            student_context={"student_name": "Test"},
            chat_history=[],
            api_key="invalid-key",
        )

        # Should only be called once - no retries
        assert mock_client.messages.create.call_count == 1
        assert "Error" in result or "error" in result.lower()


class TestMaxRetryLimit:
    """Test that max retry limit is enforced."""

    @patch("ai_assistant.Anthropic")
    def test_max_3_retries_then_fails(self, mock_anthropic_class):
        """Should fail after 3 retries (4 total attempts)."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_request = Request(method="POST", url="https://api.anthropic.com/v1/messages")

        rate_limit_error = RateLimitError(
            message="Rate limit exceeded",
            response=Response(status_code=429, request=mock_request),
            body={"error": {"message": "Rate limit exceeded"}},
        )

        # Always raise rate limit error
        mock_client.messages.create.side_effect = rate_limit_error

        result = get_ai_response(
            user_message="Hello",
            student_context={"student_name": "Test"},
            chat_history=[],
            api_key="test-key",
        )

        # Initial attempt + 3 retries = 4 total attempts
        assert mock_client.messages.create.call_count == 4
        assert "Error" in result or "error" in result.lower()


class TestErrorCategorization:
    """Test error categorization for user-friendly messages."""

    def test_categorize_rate_limit_error(self):
        """Rate limit errors should be categorized correctly."""
        mock_request = Request(method="POST", url="https://api.anthropic.com/v1/messages")
        error = RateLimitError(
            message="Rate limit exceeded",
            response=Response(status_code=429, request=mock_request),
            body={"error": {"message": "Rate limit exceeded"}},
        )

        result = categorize_error(error)
        assert isinstance(result, RateLimitAPIError)
        assert "demand" in result.user_message.lower() or "retry" in result.user_message.lower()

    def test_categorize_server_error(self):
        """Server errors should be categorized correctly."""
        mock_request = Request(method="POST", url="https://api.anthropic.com/v1/messages")
        error = InternalServerError(
            message="Internal server error",
            response=Response(status_code=500, request=mock_request),
            body={"error": {"message": "Internal server error"}},
        )

        result = categorize_error(error)
        assert isinstance(result, ServerAPIError)
        assert (
            "unavailable" in result.user_message.lower() or "service" in result.user_message.lower()
        )

    def test_categorize_client_error(self):
        """Client errors should be categorized correctly."""
        mock_request = Request(method="POST", url="https://api.anthropic.com/v1/messages")
        error = BadRequestError(
            message="Bad request",
            response=Response(status_code=400, request=mock_request),
            body={"error": {"message": "Invalid parameters"}},
        )

        result = categorize_error(error)
        assert isinstance(result, ClientAPIError)


class TestUserFriendlyErrorMessages:
    """Test that users see friendly error messages."""

    @patch("ai_assistant.Anthropic")
    def test_rate_limit_shows_friendly_message(self, mock_anthropic_class):
        """Rate limit should show user-friendly message after max retries."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_request = Request(method="POST", url="https://api.anthropic.com/v1/messages")

        rate_limit_error = RateLimitError(
            message="Rate limit exceeded",
            response=Response(status_code=429, request=mock_request),
            body={"error": {"message": "Rate limit exceeded"}},
        )

        mock_client.messages.create.side_effect = rate_limit_error

        result = get_ai_response(
            user_message="Hello",
            student_context={"student_name": "Test"},
            chat_history=[],
            api_key="test-key",
        )

        # Should contain user-friendly message
        assert (
            "demand" in result.lower() or "busy" in result.lower() or "try again" in result.lower()
        )

    @patch("ai_assistant.Anthropic")
    def test_server_error_shows_friendly_message(self, mock_anthropic_class):
        """Server error should show user-friendly message."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_request = Request(method="POST", url="https://api.anthropic.com/v1/messages")

        server_error = InternalServerError(
            message="Internal server error",
            response=Response(status_code=500, request=mock_request),
            body={"error": {"message": "Internal server error"}},
        )

        mock_client.messages.create.side_effect = server_error

        result = get_ai_response(
            user_message="Hello",
            student_context={"student_name": "Test"},
            chat_history=[],
            api_key="test-key",
        )

        # Should contain user-friendly message about service
        assert (
            "unavailable" in result.lower()
            or "service" in result.lower()
            or "temporarily" in result.lower()
        )


class TestToolIterationLimit:
    """Test that tool use loop has iteration protection."""

    @patch("ai_assistant.execute_tool")
    @patch("ai_assistant.Anthropic")
    def test_tool_loop_stops_after_max_iterations(self, mock_anthropic_class, mock_execute_tool):
        """Should stop tool loop after MAX_TOOL_ITERATIONS to prevent infinite loops."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Mock execute_tool to return valid data
        mock_execute_tool.return_value = {"name": "Test Student", "grade": "A"}

        # Create a mock response that always wants to use a tool
        def create_tool_use_response():
            response = MagicMock()
            response.stop_reason = "tool_use"
            tool_block = MagicMock()
            tool_block.type = "tool_use"
            tool_block.name = "get_student_summary"
            tool_block.input = {}
            tool_block.id = "test-id"
            response.content = [tool_block]
            return response

        # Always return tool_use responses to simulate infinite loop
        mock_client.messages.create.return_value = create_tool_use_response()

        result = get_ai_response(
            user_message="Hello",
            student_context={"student_name": "Test"},
            chat_history=[],
            api_key="test-key",
        )

        # Should stop after MAX_TOOL_ITERATIONS + 1 calls (initial + max iterations)
        assert mock_client.messages.create.call_count == MAX_TOOL_ITERATIONS + 1
        # Should return user-friendly message about taking too long
        assert "taking longer" in result.lower() or "rephrasing" in result.lower()


class TestGenericErrorHandling:
    """Test that generic errors don't leak sensitive information."""

    @patch("ai_assistant.Anthropic")
    def test_generic_error_does_not_leak_details(self, mock_anthropic_class):
        """Generic exceptions should not expose internal error details to users."""
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # Simulate an unexpected error with sensitive info in the message
        sensitive_error = Exception(
            "Connection failed: api_key=sk-ant-12345 at /internal/path/to/file.py"
        )
        mock_client.messages.create.side_effect = sensitive_error

        result = get_ai_response(
            user_message="Hello",
            student_context={"student_name": "Test"},
            chat_history=[],
            api_key="test-key",
        )

        # Should NOT contain sensitive information
        assert "sk-ant" not in result
        assert "/internal/path" not in result
        # Should contain generic error message
        assert "unexpected error" in result.lower() or "try again" in result.lower()
