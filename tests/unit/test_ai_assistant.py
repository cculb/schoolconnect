"""Unit tests for AI assistant retry logic and error handling.

Tests validate:
- Error categorization for different HTTP status codes
- Retry logic for retryable errors
- Tool iteration limits (MAX_TOOL_ITERATIONS)
- Boundary conditions for iteration counting
- Happy path scenarios
- Non-retryable error handling
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add streamlit-chat to sys.path for imports
streamlit_chat_dir = Path(__file__).parent.parent.parent / "streamlit-chat"
sys.path.insert(0, str(streamlit_chat_dir))

# Import after path modification  # noqa: E402
from ai_assistant import (  # noqa: E402
    MAX_TOOL_ITERATIONS,
    APIError,
    AuthenticationAPIError,
    NetworkAPIError,
    OverloadedAPIError,
    RateLimitAPIError,
    categorize_error,
    get_ai_response,
    is_retryable_error,
)

pytestmark = pytest.mark.unit


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing."""
    with patch("ai_assistant.Anthropic") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def sample_student_context():
    """Sample student context for testing."""
    return {"student_name": "Test Student"}


@pytest.fixture
def sample_chat_history():
    """Sample chat history for testing."""
    return [
        {"role": "user", "content": "What are my grades?"},
        {"role": "assistant", "content": "Let me check your grades."},
    ]


def create_mock_response(stop_reason="end_turn", content_text="Test response"):
    """Create a mock Anthropic API response.

    Args:
        stop_reason: The stop reason for the response
        content_text: The text content of the response

    Returns:
        Mock response object with expected attributes
    """
    mock_response = Mock()
    mock_response.stop_reason = stop_reason

    # Create mock content blocks
    mock_content_block = Mock()
    mock_content_block.type = "text"
    mock_content_block.text = content_text
    # Add hasattr support for 'text'
    mock_content_block.__dict__["text"] = content_text

    mock_response.content = [mock_content_block]

    return mock_response


def create_tool_use_response(tool_name="get_current_grades", tool_input=None):
    """Create a mock response with tool use.

    Args:
        tool_name: Name of the tool being used
        tool_input: Input parameters for the tool

    Returns:
        Mock response object with tool use
    """
    if tool_input is None:
        tool_input = {}

    mock_response = Mock()
    mock_response.stop_reason = "tool_use"

    # Create tool use block
    tool_use_block = Mock()
    tool_use_block.type = "tool_use"
    tool_use_block.name = tool_name
    tool_use_block.input = tool_input
    tool_use_block.id = "toolu_123"

    mock_response.content = [tool_use_block]

    return mock_response


def create_mock_error(status_code, message="API Error"):
    """Create a mock error with specific status code.

    Args:
        status_code: HTTP status code
        message: Error message

    Returns:
        Exception with status_code attribute
    """

    class MockAPIError(Exception):
        def __init__(self, status_code, message):
            self.status_code = status_code
            super().__init__(message)

    return MockAPIError(status_code, message)


# ============================================================================
# Test Error Categorization
# ============================================================================


class TestErrorCategorization:
    """Test that different HTTP status codes are properly categorized."""

    def test_429_categorized_as_rate_limit(self):
        """429 Rate Limit should be categorized as RateLimitAPIError."""
        error = create_mock_error(429, "Rate limit exceeded")
        result = categorize_error(error)
        assert result == RateLimitAPIError

    def test_529_categorized_as_overloaded(self):
        """529 Overloaded should be categorized as OverloadedAPIError."""
        error = create_mock_error(529, "API overloaded")
        result = categorize_error(error)
        assert result == OverloadedAPIError

    def test_401_categorized_as_authentication(self):
        """401 Unauthorized should be categorized as AuthenticationAPIError."""
        error = create_mock_error(401, "Unauthorized")
        result = categorize_error(error)
        assert result == AuthenticationAPIError

    def test_403_categorized_as_authentication(self):
        """403 Forbidden should be categorized as AuthenticationAPIError."""
        error = create_mock_error(403, "Forbidden")
        result = categorize_error(error)
        assert result == AuthenticationAPIError

    def test_connection_error_categorized_as_network(self):
        """ConnectionError should be categorized as NetworkAPIError."""
        error = ConnectionError("Connection failed")
        result = categorize_error(error)
        assert result == NetworkAPIError

    def test_timeout_error_categorized_as_network(self):
        """TimeoutError should be categorized as NetworkAPIError."""
        error = TimeoutError("Request timed out")
        result = categorize_error(error)
        assert result == NetworkAPIError

    def test_other_errors_categorized_as_generic_api_error(self):
        """Other errors should be categorized as generic APIError."""
        error = create_mock_error(500, "Internal server error")
        result = categorize_error(error)
        assert result == APIError

    def test_error_without_status_code(self):
        """Error without status code should be categorized as generic APIError."""
        error = ValueError("Some error")
        result = categorize_error(error)
        assert result == APIError


# ============================================================================
# Test Retryable Error Detection
# ============================================================================


class TestRetryableErrors:
    """Test that is_retryable_error correctly identifies retryable errors."""

    def test_rate_limit_is_retryable(self):
        """Rate limit errors should be retryable."""
        error = create_mock_error(429, "Rate limit")
        assert is_retryable_error(error) is True

    def test_overloaded_is_retryable(self):
        """Overloaded errors should be retryable."""
        error = create_mock_error(529, "Overloaded")
        assert is_retryable_error(error) is True

    def test_network_error_is_retryable(self):
        """Network errors should be retryable."""
        error = ConnectionError("Network failed")
        assert is_retryable_error(error) is True

    def test_timeout_is_retryable(self):
        """Timeout errors should be retryable."""
        error = TimeoutError("Timed out")
        assert is_retryable_error(error) is True

    def test_authentication_not_retryable(self):
        """Authentication errors should not be retryable."""
        error = create_mock_error(401, "Unauthorized")
        assert is_retryable_error(error) is False

    def test_forbidden_not_retryable(self):
        """Forbidden errors should not be retryable."""
        error = create_mock_error(403, "Forbidden")
        assert is_retryable_error(error) is False

    def test_generic_error_not_retryable(self):
        """Generic API errors should not be retryable."""
        error = create_mock_error(400, "Bad request")
        assert is_retryable_error(error) is False


# ============================================================================
# Test Tool Iteration Limit
# ============================================================================


class TestToolIterationLimit:
    """Test that MAX_TOOL_ITERATIONS properly limits iterations."""

    def test_max_tool_iterations_constant(self):
        """MAX_TOOL_ITERATIONS should be 15."""
        assert MAX_TOOL_ITERATIONS == 15

    @patch("ai_assistant.execute_tool")
    @patch("ai_assistant._make_api_call")
    def test_stops_after_max_iterations(
        self, mock_api_call, mock_execute_tool, sample_student_context, sample_chat_history
    ):
        """Should stop after MAX_TOOL_ITERATIONS (15) iterations."""
        mock_execute_tool.return_value = {"grades": ["A", "B"]}

        # Create 20 tool use responses to test the limit
        tool_responses = [create_tool_use_response() for _ in range(20)]

        mock_api_call.side_effect = tool_responses

        result = get_ai_response(
            "What are my grades?",
            sample_student_context,
            sample_chat_history,
            api_key="test_key",
        )

        # Should stop at iteration limit and return error message
        assert "maximum number of steps" in result.lower()
        # Initial call + MAX_TOOL_ITERATIONS calls = 16 total
        assert mock_api_call.call_count == 16

    @patch("ai_assistant.execute_tool")
    @patch("ai_assistant._make_api_call")
    def test_exactly_15_iterations_triggers_limit(
        self, mock_api_call, mock_execute_tool, sample_student_context, sample_chat_history
    ):
        """Boundary test: exactly 15 iterations should trigger the limit."""
        mock_execute_tool.return_value = {"grades": ["A", "B"]}

        # Create exactly 15 tool use responses, then try to continue
        responses = [create_tool_use_response() for _ in range(16)]

        mock_api_call.side_effect = responses

        result = get_ai_response(
            "What are my grades?",
            sample_student_context,
            sample_chat_history,
            api_key="test_key",
        )

        # Should trigger limit after 15 iterations (16 total calls: initial + 15)
        assert "maximum number of steps" in result.lower()
        assert mock_api_call.call_count == 16

    @patch("ai_assistant.execute_tool")
    @patch("ai_assistant._make_api_call")
    def test_14_iterations_does_not_trigger_limit(
        self, mock_api_call, mock_execute_tool, sample_student_context, sample_chat_history
    ):
        """Boundary test: 14 iterations should complete normally."""
        mock_execute_tool.return_value = {"grades": ["A", "B"]}

        # Create 14 tool use responses, then normal end
        responses = [create_tool_use_response() for _ in range(14)]
        responses.append(create_mock_response("end_turn", "Normal completion"))

        mock_api_call.side_effect = responses

        result = get_ai_response(
            "What are my grades?",
            sample_student_context,
            sample_chat_history,
            api_key="test_key",
        )

        # Should complete normally without hitting limit
        assert "Normal completion" in result
        assert "maximum number of steps" not in result.lower()
        assert mock_api_call.call_count == 15  # Initial + 14 iterations


# ============================================================================
# Test Happy Path
# ============================================================================


class TestHappyPath:
    """Test successful scenarios without errors."""

    @patch("ai_assistant.execute_tool")
    @patch("ai_assistant._make_api_call")
    def test_successful_first_attempt_no_tools(
        self, mock_api_call, mock_execute_tool, sample_student_context, sample_chat_history
    ):
        """Should succeed on first attempt when no tools are needed."""
        mock_api_call.return_value = create_mock_response(
            "end_turn", "Hello! How can I help you today?"
        )

        result = get_ai_response(
            "Hello",
            sample_student_context,
            sample_chat_history,
            api_key="test_key",
        )

        assert result == "Hello! How can I help you today?"
        assert mock_api_call.call_count == 1
        mock_execute_tool.assert_not_called()

    @patch("ai_assistant.execute_tool")
    @patch("ai_assistant._make_api_call")
    def test_successful_with_single_tool_use(
        self, mock_api_call, mock_execute_tool, sample_student_context, sample_chat_history
    ):
        """Should succeed with single tool use."""
        mock_execute_tool.return_value = [
            {"course": "Math", "grade": "A"},
            {"course": "Science", "grade": "B"},
        ]

        # First response requests tool, second response returns final answer
        mock_api_call.side_effect = [
            create_tool_use_response("get_current_grades"),
            create_mock_response("end_turn", "Your grades are: Math (A), Science (B)"),
        ]

        result = get_ai_response(
            "What are my grades?",
            sample_student_context,
            sample_chat_history,
            api_key="test_key",
        )

        assert "Math" in result and "Science" in result
        assert mock_api_call.call_count == 2
        mock_execute_tool.assert_called_once()

    @patch("ai_assistant.execute_tool")
    @patch("ai_assistant._make_api_call")
    def test_successful_with_multiple_tool_uses(
        self, mock_api_call, mock_execute_tool, sample_student_context, sample_chat_history
    ):
        """Should succeed with multiple sequential tool uses."""
        mock_execute_tool.side_effect = [
            [{"course": "Math", "grade": "A"}],  # First tool call
            [{"assignment": "Homework 5", "status": "Missing"}],  # Second tool call
        ]

        # Three responses: tool1 -> tool2 -> final answer
        mock_api_call.side_effect = [
            create_tool_use_response("get_current_grades"),
            create_tool_use_response("get_missing_assignments"),
            create_mock_response("end_turn", "You have good grades but one missing assignment."),
        ]

        result = get_ai_response(
            "How am I doing?",
            sample_student_context,
            sample_chat_history,
            api_key="test_key",
        )

        assert "good grades" in result.lower() and "missing" in result.lower()
        assert mock_api_call.call_count == 3
        assert mock_execute_tool.call_count == 2


# ============================================================================
# Test Retry Logic via _make_api_call
# ============================================================================


class TestRetryLogic:
    """Test that retryable errors trigger retries in _make_api_call."""

    @patch("ai_assistant._make_api_call")
    @patch("ai_assistant.execute_tool")
    def test_rate_limit_handled_gracefully(
        self, mock_execute_tool, mock_api_call, sample_student_context, sample_chat_history
    ):
        """Rate limit error should be caught and return user-friendly message."""
        # Simulate rate limit error that exhausts retries
        mock_api_call.side_effect = RateLimitAPIError("Rate limit exceeded")

        result = get_ai_response(
            "What are my grades?",
            sample_student_context,
            sample_chat_history,
            api_key="test_key",
        )

        # Should return user-friendly rate limit message
        assert "temporarily unavailable" in result.lower() or "high demand" in result.lower()

    @patch("ai_assistant._make_api_call")
    @patch("ai_assistant.execute_tool")
    def test_overloaded_error_handled_gracefully(
        self, mock_execute_tool, mock_api_call, sample_student_context, sample_chat_history
    ):
        """Overloaded error should be caught and return user-friendly message."""
        mock_api_call.side_effect = OverloadedAPIError("Service overloaded")

        result = get_ai_response(
            "What are my grades?",
            sample_student_context,
            sample_chat_history,
            api_key="test_key",
        )

        # Should return user-friendly overload message
        assert "high load" in result.lower() or "try again" in result.lower()

    @patch("ai_assistant._make_api_call")
    @patch("ai_assistant.execute_tool")
    def test_network_error_handled_gracefully(
        self, mock_execute_tool, mock_api_call, sample_student_context, sample_chat_history
    ):
        """Network error should be caught and return user-friendly message."""
        mock_api_call.side_effect = NetworkAPIError("Network connection failed")

        result = get_ai_response(
            "What are my grades?",
            sample_student_context,
            sample_chat_history,
            api_key="test_key",
        )

        # Should return user-friendly network error message
        assert "connect" in result.lower() or "internet" in result.lower()


# ============================================================================
# Test Non-Retryable Errors
# ============================================================================


class TestNonRetryableErrors:
    """Test that non-retryable errors don't trigger retries and are handled properly."""

    @patch("ai_assistant._make_api_call")
    @patch("ai_assistant.execute_tool")
    def test_authentication_error_no_retry(
        self, mock_execute_tool, mock_api_call, sample_student_context, sample_chat_history
    ):
        """Authentication error should not be retried and return appropriate message."""
        mock_api_call.side_effect = AuthenticationAPIError("Invalid API key")

        result = get_ai_response(
            "What are my grades?",
            sample_student_context,
            sample_chat_history,
            api_key="test_key",
        )

        # Should return authentication error message
        assert "authenticate" in result.lower() or "api key" in result.lower()
        # Should only call once (no retries for auth errors)
        assert mock_api_call.call_count == 1

    @patch("ai_assistant._make_api_call")
    @patch("ai_assistant.execute_tool")
    def test_generic_api_error_handled(
        self, mock_execute_tool, mock_api_call, sample_student_context, sample_chat_history
    ):
        """Generic API error should be handled with appropriate message."""
        mock_api_call.side_effect = APIError("Something went wrong")

        result = get_ai_response(
            "What are my grades?",
            sample_student_context,
            sample_chat_history,
            api_key="test_key",
        )

        # Should return generic error message
        assert "unable to process" in result.lower() or "try again" in result.lower()


# ============================================================================
# Test Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_missing_api_key(self, sample_student_context, sample_chat_history):
        """Should return error message when API key is missing."""
        with patch.dict("os.environ", {}, clear=True):
            result = get_ai_response(
                "What are my grades?",
                sample_student_context,
                sample_chat_history,
                api_key=None,
            )

            assert "ANTHROPIC_API_KEY" in result or "API key" in result

    @patch("ai_assistant.execute_tool")
    @patch("ai_assistant._make_api_call")
    def test_empty_response_content(
        self, mock_api_call, mock_execute_tool, sample_student_context, sample_chat_history
    ):
        """Should handle empty response content gracefully."""
        mock_response = Mock()
        mock_response.stop_reason = "end_turn"
        mock_response.content = []

        mock_api_call.return_value = mock_response

        result = get_ai_response(
            "What are my grades?",
            sample_student_context,
            sample_chat_history,
            api_key="test_key",
        )

        assert "couldn't generate" in result.lower()

    @patch("ai_assistant._make_api_call")
    @patch("ai_assistant.execute_tool")
    def test_tool_execution_error(
        self, mock_execute_tool, mock_api_call, sample_student_context, sample_chat_history
    ):
        """Should handle tool execution errors gracefully."""
        mock_execute_tool.side_effect = Exception("Database connection failed")

        mock_api_call.side_effect = [
            create_tool_use_response("get_current_grades"),
            create_mock_response("end_turn", "I encountered an error accessing the data."),
        ]

        result = get_ai_response(
            "What are my grades?",
            sample_student_context,
            sample_chat_history,
            api_key="test_key",
        )

        # Should complete despite tool error
        assert isinstance(result, str)
        assert len(result) > 0

    @patch("ai_assistant.execute_tool")
    @patch("ai_assistant._make_api_call")
    def test_default_model_selection(
        self, mock_api_call, mock_execute_tool, sample_student_context, sample_chat_history
    ):
        """Should use default model when none specified."""
        mock_api_call.return_value = create_mock_response()

        get_ai_response(
            "Hello",
            sample_student_context,
            sample_chat_history,
            api_key="test_key",
            model=None,  # No model specified
        )

        # Should have called _make_api_call with default model
        call_args = mock_api_call.call_args
        assert call_args is not None
        assert "model" in call_args.kwargs
        # Default model from ai_assistant.py
        assert "claude-sonnet-4" in call_args.kwargs["model"]

    @patch("ai_assistant.execute_tool")
    @patch("ai_assistant._make_api_call")
    def test_chat_history_limit(self, mock_api_call, mock_execute_tool, sample_student_context):
        """Should only use last 10 messages from chat history."""
        # Create 15 messages in history
        long_history = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
            for i in range(15)
        ]

        mock_api_call.return_value = create_mock_response()

        get_ai_response(
            "What are my grades?",
            sample_student_context,
            long_history,
            api_key="test_key",
        )

        # Should have called _make_api_call
        call_args = mock_api_call.call_args
        assert call_args is not None

        # Messages should include only last 10 from history + current message
        messages = call_args.kwargs["messages"]
        # Should be 11 total: 10 from history + 1 new message
        assert len(messages) == 11

    @patch("ai_assistant._make_api_call")
    def test_unexpected_exception_handled(
        self, mock_api_call, sample_student_context, sample_chat_history
    ):
        """Unexpected exceptions should be caught and return user-friendly message."""
        mock_api_call.side_effect = ValueError("Unexpected error")

        result = get_ai_response(
            "What are my grades?",
            sample_student_context,
            sample_chat_history,
            api_key="test_key",
        )

        # Should return generic error message
        assert "unexpected error" in result.lower() or "try again" in result.lower()
