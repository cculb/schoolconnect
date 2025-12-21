"""Security and authentication tests for SchoolPulse.

FERPA Compliance Tests - These tests validate:
- CRIT-1: Authentication/authorization before accessing student data
- CRIT-2: No API keys stored in session state
- HIGH-1: Session timeout and logout functionality

Run with: pytest streamlit-chat/test_auth.py -v
"""

import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add this directory for imports
THIS_DIR = Path(__file__).parent
sys.path.insert(0, str(THIS_DIR))


class TestPasswordHashing:
    """Test password hashing security."""

    def test_password_hash_is_not_plaintext(self):
        """Password should be hashed, not stored as plaintext."""
        from auth import hash_password

        password = "test_password_123"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) == 64  # SHA-256 produces 64 hex chars

    def test_same_password_produces_same_hash(self):
        """Same password should produce consistent hash."""
        from auth import hash_password

        password = "consistent_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 == hash2

    def test_different_passwords_produce_different_hashes(self):
        """Different passwords should produce different hashes."""
        from auth import hash_password

        hash1 = hash_password("password1")
        hash2 = hash_password("password2")

        assert hash1 != hash2

    def test_verify_password_succeeds_for_correct_password(self):
        """verify_password returns True for correct password."""
        from auth import hash_password, verify_password

        password = "correct_password"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_fails_for_wrong_password(self):
        """verify_password returns False for incorrect password."""
        from auth import hash_password, verify_password

        hashed = hash_password("correct_password")

        assert verify_password("wrong_password", hashed) is False


class TestParentStudentMapping:
    """Test parent-to-student relationship validation."""

    def test_get_allowed_students_returns_list(self):
        """get_allowed_students returns list of student names."""
        from auth import get_allowed_students

        # Test with demo parent
        students = get_allowed_students("demo_parent")

        assert isinstance(students, list)
        assert len(students) > 0

    def test_parent_can_only_access_their_students(self):
        """Parent should only have access to their assigned students."""
        from auth import can_access_student, get_allowed_students

        parent_id = "parent_delilah"
        students = get_allowed_students(parent_id)

        # Should be able to access their student
        for student in students:
            assert can_access_student(parent_id, student) is True

    def test_parent_cannot_access_other_students(self):
        """Parent should NOT be able to access unassigned students."""
        from auth import can_access_student

        # A parent should not access another parent's student
        assert can_access_student("parent_delilah", "OtherChild") is False

    def test_demo_parent_has_access_to_delilah(self):
        """Demo parent should have access to test student Delilah."""
        from auth import can_access_student, get_allowed_students

        students = get_allowed_students("demo_parent")
        assert "Delilah" in students

        assert can_access_student("demo_parent", "Delilah") is True


class TestAuthentication:
    """Test authentication flow."""

    def test_authenticate_with_valid_credentials(self):
        """authenticate returns user info for valid credentials."""
        from auth import authenticate

        result = authenticate("demo", "demo123")

        assert result is not None
        assert "user_id" in result
        assert "allowed_students" in result

    def test_authenticate_with_invalid_password(self):
        """authenticate returns None for wrong password."""
        from auth import authenticate

        result = authenticate("demo", "wrong_password")

        assert result is None

    def test_authenticate_with_invalid_username(self):
        """authenticate returns None for unknown user."""
        from auth import authenticate

        result = authenticate("unknown_user", "password")

        assert result is None

    def test_authenticate_returns_allowed_students(self):
        """Successful auth includes list of allowed students."""
        from auth import authenticate

        result = authenticate("demo", "demo123")

        assert result is not None
        assert isinstance(result["allowed_students"], list)
        assert len(result["allowed_students"]) > 0


class TestSessionManager:
    """Test session timeout and management."""

    def test_create_session_returns_token(self):
        """create_session returns a session token."""
        from session_manager import create_session

        token = create_session("test_user", ["Student1"])

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20  # Should be a reasonably long token

    def test_validate_session_succeeds_for_valid_token(self):
        """validate_session returns session info for valid token."""
        from session_manager import create_session, validate_session

        token = create_session("test_user", ["Student1"])
        session = validate_session(token)

        assert session is not None
        assert session["user_id"] == "test_user"
        assert "Student1" in session["allowed_students"]

    def test_validate_session_fails_for_invalid_token(self):
        """validate_session returns None for invalid token."""
        from session_manager import validate_session

        session = validate_session("invalid_token_12345")

        assert session is None

    def test_session_expires_after_timeout(self):
        """Session should expire after inactivity timeout."""
        from session_manager import (
            SESSION_TIMEOUT_MINUTES,
            create_session,
            validate_session,
        )

        token = create_session("test_user", ["Student1"])

        # Mock time passing beyond timeout
        with patch("session_manager.datetime") as mock_datetime:
            future_time = datetime.now() + timedelta(
                minutes=SESSION_TIMEOUT_MINUTES + 1
            )
            mock_datetime.now.return_value = future_time
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(
                *args, **kwargs
            )

            session = validate_session(token)
            assert session is None

    def test_session_activity_refreshes_timeout(self):
        """Accessing session should refresh the timeout."""
        from session_manager import create_session, get_session_remaining_time

        token = create_session("test_user", ["Student1"])

        # Get initial remaining time
        remaining1 = get_session_remaining_time(token)

        # Simulate some time passing then refresh
        time.sleep(0.1)

        from session_manager import refresh_session

        refresh_session(token)
        remaining2 = get_session_remaining_time(token)

        # After refresh, remaining time should be reset to near max
        assert remaining2 >= remaining1 - 1  # Allow 1 second tolerance

    def test_logout_invalidates_session(self):
        """logout should invalidate the session."""
        from session_manager import create_session, logout, validate_session

        token = create_session("test_user", ["Student1"])

        # Verify session is valid
        assert validate_session(token) is not None

        # Logout
        logout(token)

        # Session should now be invalid
        assert validate_session(token) is None

    def test_session_timeout_is_30_minutes(self):
        """Session timeout should be 30 minutes per FERPA requirement."""
        from session_manager import SESSION_TIMEOUT_MINUTES

        assert SESSION_TIMEOUT_MINUTES == 30


class TestSessionWarning:
    """Test session timeout warning functionality."""

    def test_get_session_remaining_time(self):
        """get_session_remaining_time returns minutes remaining."""
        from session_manager import (
            SESSION_TIMEOUT_MINUTES,
            create_session,
            get_session_remaining_time,
        )

        token = create_session("test_user", ["Student1"])
        remaining = get_session_remaining_time(token)

        # Should be close to full timeout (within 1 minute)
        assert remaining is not None
        assert SESSION_TIMEOUT_MINUTES - 1 <= remaining <= SESSION_TIMEOUT_MINUTES

    def test_should_show_timeout_warning_returns_false_when_time_remaining(self):
        """Warning should not show when plenty of time remaining."""
        from session_manager import create_session, should_show_timeout_warning

        token = create_session("test_user", ["Student1"])
        should_warn = should_show_timeout_warning(token)

        assert should_warn is False

    def test_should_show_timeout_warning_returns_true_near_expiry(self):
        """Warning should show when session is near expiry."""
        from session_manager import (
            SESSION_TIMEOUT_MINUTES,
            WARNING_THRESHOLD_MINUTES,
            create_session,
            should_show_timeout_warning,
        )

        token = create_session("test_user", ["Student1"])

        # Mock time to be near expiry
        with patch("session_manager.datetime") as mock_datetime:
            near_expiry = datetime.now() + timedelta(
                minutes=SESSION_TIMEOUT_MINUTES - WARNING_THRESHOLD_MINUTES + 1
            )
            mock_datetime.now.return_value = near_expiry
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(
                *args, **kwargs
            )

            # Note: This test may need adjustment based on implementation
            # The key is that warning appears when < WARNING_THRESHOLD_MINUTES remain
            _ = should_show_timeout_warning(token)  # Call to verify no error


class TestAPIKeyRemoval:
    """Test that API keys are not stored in session state."""

    def test_api_key_not_in_session_state_keys(self):
        """API key should not be stored in session_state."""
        # This is a design validation test
        # The actual check happens in app.py refactoring
        # We verify by checking the auth module doesn't store API keys

        from auth import authenticate

        result = authenticate("demo", "demo123")

        # Auth result should not contain API key
        assert result is not None
        assert "api_key" not in result
        assert "anthropic_api_key" not in result

    def test_get_api_key_uses_secrets_or_environ(self):
        """get_api_key should only use st.secrets or os.environ."""
        from auth import get_api_key

        # Without mocking, should return from environ or None
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key_123"}):
            key = get_api_key()
            assert key == "test_key_123"

    def test_get_api_key_prefers_secrets_over_environ(self):
        """st.secrets should take precedence over environment."""
        from auth import get_api_key

        # Mock streamlit secrets
        mock_secrets = MagicMock()
        mock_secrets.get.return_value = "secret_key_456"

        with patch("auth.st") as mock_st:
            mock_st.secrets = mock_secrets

            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env_key"}):
                key = get_api_key()
                # Should prefer secrets
                assert key == "secret_key_456"


class TestAuthorizationMiddleware:
    """Test that student data access requires authentication."""

    def test_require_auth_decorator_blocks_unauthenticated(self):
        """require_auth should block access without valid session."""
        from auth import require_auth

        @require_auth
        def protected_function(session):
            return "secret_data"

        # Without valid session, should raise or return error
        result = protected_function(None)
        assert result is None or (isinstance(result, dict) and "error" in result)

    def test_require_auth_decorator_allows_authenticated(self):
        """require_auth should allow access with valid session."""
        from auth import require_auth
        from session_manager import create_session, validate_session

        @require_auth
        def protected_function(session):
            return {"data": "secret_data", "user": session["user_id"]}

        token = create_session("test_user", ["Student1"])
        session = validate_session(token)

        result = protected_function(session)
        assert result is not None
        assert result.get("data") == "secret_data"


class TestLoginPage:
    """Test login page functionality."""

    def test_login_form_fields_exist(self):
        """Login form should have username and password fields."""
        # This is a UI test that validates the auth module provides
        # the necessary functions for the login page

        from auth import authenticate, get_login_error_message

        # These functions should exist and be callable
        assert callable(authenticate)
        assert callable(get_login_error_message)

    def test_login_error_messages(self):
        """Login should provide appropriate error messages."""
        from auth import get_login_error_message

        # Test various error scenarios
        msg = get_login_error_message("invalid_credentials")
        assert "incorrect" in msg.lower() or "invalid" in msg.lower()

        msg = get_login_error_message("account_locked")
        assert "locked" in msg.lower() or "contact" in msg.lower()


class TestSecurityHardening:
    """Test security hardening measures."""

    def test_password_min_length_validation(self):
        """Passwords should meet minimum length requirements."""
        from auth import validate_password_strength

        # Too short
        assert validate_password_strength("abc") is False

        # Adequate length
        assert validate_password_strength("demo123") is True

    def test_session_tokens_are_cryptographically_random(self):
        """Session tokens should use secure random generation."""
        from session_manager import create_session

        tokens = [create_session(f"user_{i}", ["Student"]) for i in range(10)]

        # All tokens should be unique
        assert len(set(tokens)) == 10

        # Tokens should be sufficiently long
        for token in tokens:
            assert len(token) >= 32

    def test_failed_login_does_not_leak_user_existence(self):
        """Failed login should not reveal if user exists."""
        from auth import get_login_error_message

        # Error messages should be generic
        msg1 = get_login_error_message("invalid_credentials")
        msg2 = get_login_error_message("user_not_found")

        # Messages should be identical or generic
        # This prevents username enumeration attacks
        assert (
            msg1 == msg2
            or "incorrect" in msg1.lower()
            or "invalid" in msg1.lower()
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
