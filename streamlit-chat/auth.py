"""Authentication and authorization module for SchoolPulse.

FERPA Compliance:
- CRIT-1: Parent authentication before accessing student data
- CRIT-2: API keys retrieved only from st.secrets or os.environ
- Authorization ensures parents can only access their assigned students

Phase 1: Simple password-based authentication
Future: Integrate with PowerSchool SSO / OAuth
"""

import hashlib
import os
from functools import wraps
from typing import Callable, Optional

try:
    import streamlit as st
except ImportError:
    st = None  # Allow testing without streamlit


# Minimum password length requirement
MIN_PASSWORD_LENGTH = 6


# Parent-to-student mapping
# In production, this would come from a database or PowerSchool integration
PARENT_STUDENT_MAPPING: dict[str, list[str]] = {
    "demo_parent": ["Delilah"],
    "parent_delilah": ["Delilah"],
    "parent_demo": ["Delilah"],
}

# User credentials (password hashes)
# In production, this would be in a secure database
# Passwords: demo -> demo123
USER_CREDENTIALS: dict[str, dict] = {
    "demo": {
        "password_hash": hashlib.sha256(b"demo123").hexdigest(),
        "parent_id": "demo_parent",
        "display_name": "Demo Parent",
    },
}


def hash_password(password: str) -> str:
    """Hash a password using SHA-256.

    Args:
        password: Plain text password

    Returns:
        Hexadecimal hash string
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash.

    Args:
        password: Plain text password to verify
        password_hash: Expected hash to compare against

    Returns:
        True if password matches, False otherwise
    """
    return hash_password(password) == password_hash


def validate_password_strength(password: str) -> bool:
    """Validate password meets minimum requirements.

    Args:
        password: Password to validate

    Returns:
        True if password meets requirements, False otherwise
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return False
    return True


def get_allowed_students(parent_id: str) -> list[str]:
    """Get list of students a parent is allowed to access.

    Args:
        parent_id: The parent's identifier

    Returns:
        List of student names the parent can access
    """
    return PARENT_STUDENT_MAPPING.get(parent_id, [])


def can_access_student(parent_id: str, student_name: str) -> bool:
    """Check if a parent can access a specific student's data.

    Args:
        parent_id: The parent's identifier
        student_name: Name of the student to access

    Returns:
        True if access is allowed, False otherwise
    """
    allowed_students = get_allowed_students(parent_id)
    # Case-insensitive comparison
    return any(
        student.lower() == student_name.lower() for student in allowed_students
    )


def authenticate(username: str, password: str) -> Optional[dict]:
    """Authenticate a user with username and password.

    Args:
        username: The username to authenticate
        password: The password to verify

    Returns:
        Dict with user info if successful, None if authentication fails
    """
    if not username or not password:
        return None

    user = USER_CREDENTIALS.get(username.lower())
    if not user:
        return None

    if not verify_password(password, user["password_hash"]):
        return None

    parent_id = user["parent_id"]
    return {
        "user_id": parent_id,
        "username": username,
        "display_name": user.get("display_name", username),
        "allowed_students": get_allowed_students(parent_id),
    }


def get_login_error_message(error_type: str) -> str:
    """Get user-friendly error message for login failures.

    Note: Messages are intentionally generic to prevent username enumeration.

    Args:
        error_type: Type of error that occurred

    Returns:
        User-friendly error message
    """
    # Generic message to prevent user enumeration attacks
    generic_message = "Invalid username or password. Please try again."

    error_messages = {
        "invalid_credentials": generic_message,
        "user_not_found": generic_message,  # Same message to prevent enumeration
        "account_locked": "Account locked. Please contact your administrator.",
        "session_expired": "Your session has expired. Please log in again.",
    }

    return error_messages.get(error_type, generic_message)


def get_api_key() -> Optional[str]:
    """Get API key from st.secrets or environment.

    CRIT-2 Compliance: Never store API key in session_state.
    Only retrieve from secure sources: st.secrets or os.environ.

    Returns:
        API key string or None if not configured
    """
    # Try st.secrets first (preferred)
    if st is not None:
        try:
            key = st.secrets.get("ANTHROPIC_API_KEY")
            if key:
                return key
        except Exception:
            pass  # Secrets not configured

    # Fall back to environment variable
    return os.environ.get("ANTHROPIC_API_KEY")


def require_auth(func: Callable) -> Callable:
    """Decorator to require authentication for a function.

    Usage:
        @require_auth
        def protected_function(session):
            return session["user_id"]

    Args:
        func: Function that requires a valid session as first argument

    Returns:
        Wrapped function that validates session before execution
    """

    @wraps(func)
    def wrapper(session, *args, **kwargs):
        if session is None:
            return {"error": "Authentication required"}

        if not isinstance(session, dict):
            return {"error": "Invalid session"}

        if "user_id" not in session:
            return {"error": "Invalid session - no user_id"}

        return func(session, *args, **kwargs)

    return wrapper


def render_login_page() -> Optional[dict]:
    """Render the login page and handle authentication.

    Returns:
        User info dict if login successful, None otherwise
    """
    if st is None:
        return None

    st.markdown(
        """
        <div style="max-width: 400px; margin: 2rem auto; padding: 2rem;
                    background: white; border-radius: 15px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);">
            <h2 style="color: #667eea; text-align: center; margin-bottom: 1.5rem;">
                Login to SchoolPulse
            </h2>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.form("login_form"):
            username = st.text_input(
                "Username", placeholder="Enter your username", key="login_username"
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password",
            )

            submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password.")
                    return None

                result = authenticate(username, password)

                if result:
                    return result
                else:
                    st.error(get_login_error_message("invalid_credentials"))
                    return None

        st.markdown(
            """
            <div style="text-align: center; margin-top: 1rem; color: #666;">
                <small>Demo credentials: demo / demo123</small>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return None


def get_current_user_students(session: dict) -> list[str]:
    """Get the list of students the current user can access.

    Args:
        session: Current session dict

    Returns:
        List of student names
    """
    if not session:
        return []
    return session.get("allowed_students", [])


def get_default_student(session: dict) -> Optional[str]:
    """Get the default student for the current session.

    Args:
        session: Current session dict

    Returns:
        First allowed student name or None
    """
    students = get_current_user_students(session)
    return students[0] if students else None
