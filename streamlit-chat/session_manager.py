"""Session management module for SchoolPulse.

FERPA Compliance:
- HIGH-1: 30-minute session timeout for inactivity
- Logout functionality to invalidate sessions
- Session token validation

Session tokens are stored in memory for Phase 1.
Future: Use Redis or database-backed session storage.
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional

# Session timeout configuration (FERPA requirement: 30 minutes)
SESSION_TIMEOUT_MINUTES = 30

# Warning threshold - show warning when this many minutes remain
WARNING_THRESHOLD_MINUTES = 5

# In-memory session storage
# In production, use Redis or database-backed storage
_sessions: dict[str, dict] = {}


def create_session(user_id: str, allowed_students: list[str]) -> str:
    """Create a new session for an authenticated user.

    Args:
        user_id: The authenticated user's identifier
        allowed_students: List of students the user can access

    Returns:
        Session token string
    """
    # Generate cryptographically secure random token
    token = secrets.token_hex(32)  # 64 character hex string

    # Store session data
    _sessions[token] = {
        "user_id": user_id,
        "allowed_students": allowed_students,
        "created_at": datetime.now(),
        "last_activity": datetime.now(),
    }

    return token


def validate_session(token: str) -> Optional[dict]:
    """Validate a session token and return session info if valid.

    Args:
        token: Session token to validate

    Returns:
        Session dict if valid, None if invalid or expired
    """
    if not token:
        return None

    session = _sessions.get(token)
    if not session:
        return None

    # Check for expiration
    last_activity = session["last_activity"]
    timeout_delta = timedelta(minutes=SESSION_TIMEOUT_MINUTES)

    if datetime.now() - last_activity > timeout_delta:
        # Session expired - remove it
        del _sessions[token]
        return None

    return {
        "user_id": session["user_id"],
        "allowed_students": session["allowed_students"],
        "created_at": session["created_at"],
        "last_activity": session["last_activity"],
    }


def refresh_session(token: str) -> bool:
    """Refresh a session's last activity timestamp.

    Args:
        token: Session token to refresh

    Returns:
        True if session was refreshed, False if token invalid
    """
    if not token:
        return False

    session = _sessions.get(token)
    if not session:
        return False

    # Check if already expired before refreshing
    last_activity = session["last_activity"]
    timeout_delta = timedelta(minutes=SESSION_TIMEOUT_MINUTES)

    if datetime.now() - last_activity > timeout_delta:
        # Already expired
        del _sessions[token]
        return False

    # Refresh the timestamp
    session["last_activity"] = datetime.now()
    return True


def logout(token: str) -> bool:
    """Logout by invalidating a session.

    Args:
        token: Session token to invalidate

    Returns:
        True if session was found and removed, False otherwise
    """
    if not token:
        return False

    if token in _sessions:
        del _sessions[token]
        return True

    return False


def get_session_remaining_time(token: str) -> Optional[int]:
    """Get the remaining time in minutes before session expires.

    Args:
        token: Session token to check

    Returns:
        Minutes remaining, or None if session invalid
    """
    if not token:
        return None

    session = _sessions.get(token)
    if not session:
        return None

    last_activity = session["last_activity"]
    timeout_delta = timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    expiry_time = last_activity + timeout_delta

    remaining = expiry_time - datetime.now()

    if remaining.total_seconds() <= 0:
        return 0

    return int(remaining.total_seconds() / 60)


def should_show_timeout_warning(token: str) -> bool:
    """Check if a timeout warning should be shown.

    Args:
        token: Session token to check

    Returns:
        True if warning should be shown, False otherwise
    """
    remaining = get_session_remaining_time(token)

    if remaining is None:
        return False

    return remaining <= WARNING_THRESHOLD_MINUTES


def get_all_sessions_count() -> int:
    """Get count of active sessions (for admin/monitoring).

    Returns:
        Number of active sessions
    """
    # Clean up expired sessions first
    _cleanup_expired_sessions()
    return len(_sessions)


def _cleanup_expired_sessions() -> int:
    """Remove all expired sessions from storage.

    Returns:
        Number of sessions removed
    """
    timeout_delta = timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    now = datetime.now()
    expired_tokens = []

    for token, session in _sessions.items():
        if now - session["last_activity"] > timeout_delta:
            expired_tokens.append(token)

    for token in expired_tokens:
        del _sessions[token]

    return len(expired_tokens)


def render_session_warning(token: str) -> None:
    """Render a session timeout warning in the Streamlit UI.

    Args:
        token: Current session token
    """
    try:
        import streamlit as st
    except ImportError:
        return

    if not should_show_timeout_warning(token):
        return

    remaining = get_session_remaining_time(token)

    if remaining is not None and remaining > 0:
        st.warning(
            f"Your session will expire in {remaining} minute(s). "
            "Any activity will extend your session."
        )
    elif remaining == 0:
        st.error("Your session has expired. Please log in again.")


def render_logout_button(token: str) -> bool:
    """Render a logout button in the Streamlit UI.

    Args:
        token: Current session token

    Returns:
        True if logout was clicked, False otherwise
    """
    try:
        import streamlit as st
    except ImportError:
        return False

    if st.button("Logout", key="logout_button", use_container_width=True):
        logout(token)
        return True

    return False


def get_session_info_display(token: str) -> Optional[dict]:
    """Get session info formatted for display.

    Args:
        token: Session token

    Returns:
        Dict with display-friendly session info
    """
    session = validate_session(token)
    if not session:
        return None

    remaining = get_session_remaining_time(token)

    return {
        "user_id": session["user_id"],
        "students": ", ".join(session["allowed_students"]),
        "session_started": session["created_at"].strftime("%H:%M"),
        "time_remaining": f"{remaining} min" if remaining else "Expired",
    }
