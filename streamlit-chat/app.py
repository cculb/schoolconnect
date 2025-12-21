"""SchoolPulse - Parent Chat Interface for PowerSchool Data.

FERPA Compliant Implementation:
- CRIT-1: Authentication required before accessing student data
- CRIT-2: API key retrieved only from st.secrets or os.environ (never session_state)
- HIGH-1: 30-minute session timeout with logout functionality
- HIGH-3: Message history circular buffer (max 50 stored, 10 sent to AI)
- HIGH-4: Dynamic student selection from auth context
- MED-1: @st.cache_data for expensive queries
- MED-2: External CSS file (.streamlit/custom.css)
- MED-3: Google-style docstrings on all functions
"""

from pathlib import Path

import streamlit as st
from ai_assistant import (
    AVAILABLE_MODELS,
    DEFAULT_MODEL,
    get_ai_response,
    get_db_path,
    get_quick_response,
)
from auth import (
    can_access_student,
    get_api_key,
    get_current_user_students,
    get_default_student,
    render_login_page,
)
from data_queries import get_student_summary
from session_manager import (
    create_session,
    logout,
    refresh_session,
    render_session_warning,
    should_show_timeout_warning,
    validate_session,
)

# Message buffer constants (HIGH-3)
MAX_MESSAGES_STORED = 50  # Maximum messages to keep in session state
MAX_MESSAGES_TO_AI = 10  # Maximum messages to send to AI for context


def get_contextual_starters(summary: dict) -> list[dict]:
    """Generate conversation starters based on student data.

    Creates dynamic conversation starter suggestions based on the student's
    current academic status, including attendance, missing assignments, etc.

    Args:
        summary: Dictionary containing student summary data with keys like
            'missing_assignments', 'attendance_rate', 'days_absent'.

    Returns:
        List of up to 6 conversation starter dictionaries, each with
        'icon' (emoji) and 'text' (starter question) keys.
    """
    starters = []

    # Always include general starters
    starters.append({"icon": "🎯", "text": "What should we prioritize this week?"})
    starters.append({"icon": "📊", "text": "How is my child doing overall?"})

    # Context-based starters
    missing = summary.get("missing_assignments", 0)
    if missing > 0:
        starters.append(
            {
                "icon": "📋",
                "text": f"How can we address the {missing} missing assignment{'s' if missing > 1 else ''}?",
            }
        )

    attendance = summary.get("attendance_rate", 100)
    if attendance < 90:
        starters.append(
            {"icon": "🏫", "text": f"Attendance is at {attendance}%. Should I be concerned?"}
        )
    elif attendance >= 95:
        starters.append({"icon": "🏫", "text": "Great attendance! How can we maintain it?"})

    days_absent = summary.get("days_absent", 0)
    if days_absent > 3:
        starters.append(
            {
                "icon": "📅",
                "text": f"My child has been absent {days_absent} days. What should I know?",
            }
        )

    # Add helpful general starters
    starters.append({"icon": "✉️", "text": "Help me write an email to a teacher"})
    starters.append({"icon": "💡", "text": "Suggest study strategies for middle school"})

    return starters[:6]  # Limit to 6 starters


def load_css() -> None:
    """Load custom CSS from external file.

    MED-2: Moves ~200 lines of inline CSS to an external file for better
    maintainability. Falls back to minimal inline CSS if file not found.
    """
    css_path = Path(__file__).parent / ".streamlit" / "custom.css"
    try:
        css_content = css_path.read_text()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        # Minimal fallback CSS if external file is missing
        st.markdown(
            """
            <style>
            .app-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 2rem;
                border-radius: 15px;
                margin-bottom: 2rem;
                color: white;
            }
            .app-title { font-size: 2.5rem; font-weight: 700; color: white; }
            .app-subtitle { font-size: 1.1rem; color: white; opacity: 0.95; }
            </style>
            """,
            unsafe_allow_html=True,
        )


@st.cache_data(ttl=60)
def get_cached_student_summary(db_path: str, student_name: str) -> dict:
    """Get student summary with caching.

    MED-1: Caches expensive database queries for 60 seconds to reduce
    load and improve responsiveness.

    Args:
        db_path: Path to the SQLite database.
        student_name: Name of the student to look up.

    Returns:
        Dictionary containing student summary data.
    """
    return get_student_summary(db_path, student_name)


def add_message_to_buffer(
    messages: list[dict[str, str]], role: str, content: str
) -> list[dict[str, str]]:
    """Add a message to the buffer, enforcing maximum size.

    HIGH-3: Implements circular buffer pattern - stores max 50 messages,
    removing oldest when limit is exceeded.

    Args:
        messages: Current list of messages.
        role: Message role ('user' or 'assistant').
        content: Message content text.

    Returns:
        Updated messages list with new message added and oldest
        removed if buffer was at capacity.
    """
    messages.append({"role": role, "content": content})
    # Trim to max size if exceeded
    if len(messages) > MAX_MESSAGES_STORED:
        messages = messages[-MAX_MESSAGES_STORED:]
    return messages


def get_messages_for_ai(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    """Get the most recent messages to send to AI.

    HIGH-3: Only sends the last 10 messages to the AI API to manage
    context window and reduce costs while maintaining conversation flow.

    Args:
        messages: Full message history from session state.

    Returns:
        List of the most recent messages (up to MAX_MESSAGES_TO_AI).
    """
    return messages[-MAX_MESSAGES_TO_AI:] if messages else []


# Page configuration - mobile friendly
st.set_page_config(
    page_title="SchoolPulse", page_icon="📚", layout="wide", initial_sidebar_state="collapsed"
)

# Load CSS from external file (MED-2)
load_css()


def init_session_state() -> None:
    """Initialize session state variables.

    Sets up all required session state keys with default values if they
    don't already exist. This includes authentication state, chat messages,
    AI model selection, and user information.

    Session State Keys:
        messages: List of chat message dicts (role, content)
        model: Selected AI model identifier
        session_token: Authentication session token
        authenticated: Boolean authentication status
        user_info: Dict with user details and allowed students
    """
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "model" not in st.session_state:
        st.session_state.model = DEFAULT_MODEL

    if "session_token" not in st.session_state:
        st.session_state.session_token = None

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "user_info" not in st.session_state:
        st.session_state.user_info = None


def handle_login() -> None:
    """Handle the login flow and authentication.

    Renders the login page header and form. On successful authentication,
    creates a session, sets up user info in session state, and selects
    the default student from the user's allowed students list.

    HIGH-4: Uses dynamic student selection from auth context instead of
    hardcoded values.
    """
    st.markdown(
        """
    <div class="app-header">
        <h1 class="app-title">📚 SchoolPulse</h1>
        <p class="app-subtitle">Your child's academic progress at a glance</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    result = render_login_page()

    if result:
        # Create session
        token = create_session(result["user_id"], result["allowed_students"])
        st.session_state.session_token = token
        st.session_state.authenticated = True
        st.session_state.user_info = result

        # Set default student from allowed students (HIGH-4: dynamic selection)
        default_student = get_default_student(result)
        if default_student:
            st.session_state.student_name = default_student

        st.rerun()


def handle_logout() -> None:
    """Handle logout and session cleanup.

    Invalidates the current session token, clears all authentication
    state from session_state, and triggers a page rerun to return
    to the login screen.
    """
    if st.session_state.session_token:
        logout(st.session_state.session_token)

    st.session_state.session_token = None
    st.session_state.authenticated = False
    st.session_state.user_info = None
    st.session_state.messages = []
    st.rerun()


def validate_current_session() -> bool:
    """Validate the current session and refresh if valid.

    Returns:
        True if session is valid, False otherwise
    """
    token = st.session_state.get("session_token")
    if not token:
        return False

    session = validate_session(token)
    if not session:
        # Session expired
        st.session_state.authenticated = False
        st.session_state.session_token = None
        st.session_state.user_info = None
        return False

    # Refresh session on activity
    refresh_session(token)
    return True


def format_quick_response(result: dict) -> str:
    """Format a quick response result with enhanced visual styling.

    Converts raw data from quick action queries into formatted markdown
    with visual enhancements like colored badges, tables, and status
    indicators.

    Args:
        result: Dictionary containing query results with 'title' and 'data'
            keys, or an 'error' key if the query failed.

    Returns:
        Formatted markdown string ready for display in the chat interface.
    """
    if "error" in result:
        return f"❌ **Error:** {result['error']}"

    title = result.get("title", "Results")
    data = result.get("data", [])

    output = f"### 📋 {title}\n\n"

    if title == "Missing Assignments":
        if not data:
            output += """
<div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            font-size: 1.1rem;
            font-weight: 600;
            box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);">
    ✅ No missing assignments! Excellent work!
</div>
"""
        else:
            output += "<div style='background: #fef3c7; padding: 1rem; border-radius: 10px; border-left: 4px solid #f59e0b; margin-bottom: 1rem;'>"
            output += f"<strong>⚠️ Found {len(data)} missing assignment(s)</strong></div>\n\n"
            for i, item in enumerate(data, 1):
                output += f"**{i}. {item['assignment_name']}**\n"
                output += f"- 📚 Course: `{item['course_name']}`\n"
                output += f"- 👨‍🏫 Teacher: {item.get('teacher_name', 'N/A')}\n"
                output += f"- 📅 Due: {item.get('due_date', 'N/A')}\n\n"

    elif title == "Current Grades":
        if not data:
            output += "📊 No grade data available."
        else:
            output += "| Course | Teacher | Grade |\n"
            output += "|--------|---------|-------|\n"
            for item in data:
                grade = item.get("letter_grade") or item.get("percent") or "N/A"
                percent = f" ({item['percent']}%)" if item.get("percent") else ""
                teacher = item.get("teacher_name", "N/A")
                output += f"| {item['course_name']} | {teacher} | **{grade}**{percent} |\n"

    elif title == "Attendance Summary":
        if isinstance(data, dict) and "error" not in data:
            rate = data.get("rate", 0)

            if rate >= 95:
                bg_color = "#10b981"
                status_emoji = "✅"
                status_text = "Excellent"
            elif rate >= 90:
                bg_color = "#f59e0b"
                status_emoji = "⚠️"
                status_text = "Good"
            else:
                bg_color = "#ef4444"
                status_emoji = "🔴"
                status_text = "Needs Attention"

            output += f"""
<div style="background: linear-gradient(135deg, {bg_color} 0%, {bg_color}dd 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 1rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
    <div style="font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;">
        {status_emoji} {rate}% Attendance Rate
    </div>
    <div style="font-size: 1rem; opacity: 0.95;">
        Status: {status_text}
    </div>
</div>
"""
            output += "\n**📊 Details:**\n"
            output += f"- Days Absent: `{data.get('days_absent', 0)}`\n"
            output += f"- Tardies: `{data.get('tardies', 0)}`\n"
            output += f"- Total School Days: `{data.get('total_days', 0)}`\n"

            if rate < 90:
                output += "\n> ⚠️ **Note:** Attendance is below 90%. Consider reviewing attendance records."
        else:
            output += "No attendance data available."

    elif title == "Due This Week":
        if not data:
            output += """
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            font-size: 1.1rem;
            font-weight: 600;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);">
    📅 No assignments due this week! Enjoy your free time!
</div>
"""
        else:
            output += "<div style='background: #dbeafe; padding: 1rem; border-radius: 10px; border-left: 4px solid #3b82f6; margin-bottom: 1rem;'>"
            output += f"<strong>📌 {len(data)} assignment(s) coming up</strong></div>\n\n"
            for i, item in enumerate(data, 1):
                output += f"**{i}. {item['assignment_name']}**\n"
                output += f"- 📚 Course: `{item['course_name']}`\n"
                output += f"- 📅 Due: {item.get('due_date', 'N/A')}\n\n"

    elif title == "Student Summary":
        if isinstance(data, dict) and "error" not in data:
            output += f"### 👨‍🎓 {data.get('name', 'Student')} - Grade {data.get('grade_level', 'N/A')}\n\n"

            missing = data.get("missing_assignments", 0)
            attendance = data.get("attendance_rate", 0)

            output += "| Metric | Value |\n"
            output += "|--------|-------|\n"
            output += f"| 📚 Courses | {data.get('course_count', 0)} |\n"
            output += f"| 📝 Missing Work | {missing} |\n"
            output += f"| 🏫 Attendance | {attendance}% |\n"
            output += f"| 📅 Days Absent | {data.get('days_absent', 0)} |\n"
        else:
            output += "Unable to retrieve student summary."

    return output


def render_main_app() -> None:
    """Render the main application after authentication.

    Displays the full application interface including:
    - Header with app branding
    - Sidebar with settings, model selection, and student switcher
    - Dashboard metrics overview
    - Quick action buttons
    - Chat interface with AI assistant

    HIGH-3: Uses message buffer for efficient message history management.
    HIGH-4: Uses dynamic student selection from authenticated user context.
    MED-1: Uses cached student summary queries.
    """
    # Get current user info
    user_info = st.session_state.user_info
    token = st.session_state.session_token

    # Initialize student_name from auth context (HIGH-4: no hardcoded fallback)
    if "student_name" not in st.session_state:
        default_student = get_default_student(user_info)
        if default_student:
            st.session_state.student_name = default_student
        else:
            st.error("No students associated with your account.")
            return

    # Get API key securely (CRIT-2 compliance)
    api_key = get_api_key()

    # Header
    st.markdown(
        """
    <div class="app-header">
        <h1 class="app-title">📚 SchoolPulse</h1>
        <p class="app-subtitle">Your child's academic progress at a glance</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Sidebar for settings
    with st.sidebar:
        st.header("⚙️ Settings")

        # Show logged in user
        st.markdown(f"**Logged in as:** {user_info.get('display_name', 'User')}")

        st.divider()

        # Session timeout warning
        if should_show_timeout_warning(token):
            render_session_warning(token)

        # Logout button
        if st.button("🚪 Logout", use_container_width=True, key="sidebar_logout"):
            handle_logout()

        st.divider()

        # Model selection
        model_options = list(AVAILABLE_MODELS.keys())
        current_index = (
            model_options.index(st.session_state.model)
            if st.session_state.model in model_options
            else 0
        )

        selected_model = st.selectbox(
            "AI Model",
            options=model_options,
            format_func=lambda x: AVAILABLE_MODELS[x],
            index=current_index,
            help="Select the Claude model to use",
        )
        if selected_model != st.session_state.model:
            st.session_state.model = selected_model

        st.divider()

        # Student selection (only show students the user has access to)
        allowed_students = get_current_user_students(user_info)
        if len(allowed_students) > 1:
            student_input = st.selectbox(
                "Select Student",
                options=allowed_students,
                index=allowed_students.index(st.session_state.student_name)
                if st.session_state.student_name in allowed_students
                else 0,
                help="Select which student to view",
            )
            if student_input != st.session_state.student_name:
                # Verify access (FERPA authorization)
                if can_access_student(user_info["user_id"], student_input):
                    st.session_state.student_name = student_input
                    st.session_state.messages = []  # Clear chat for new student
                else:
                    st.error("Access denied to this student.")
        else:
            st.markdown(f"**Student:** {st.session_state.student_name}")

        st.divider()

        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # Check API key
    if not api_key:
        st.warning(
            "⚠️ API key not configured. Please set ANTHROPIC_API_KEY in secrets or environment."
        )

    # Dashboard metrics (MED-1: using cached query)
    try:
        db_path = get_db_path()

        # Verify authorization before accessing student data
        if not can_access_student(user_info["user_id"], st.session_state.student_name):
            st.error("You are not authorized to view this student's data.")
            return

        # Show loading indicator for first data load
        with st.spinner("Loading student data..."):
            summary = get_cached_student_summary(db_path, st.session_state.student_name)

        if "error" not in summary:
            st.markdown("### 📊 Dashboard Overview")

            # Create metric cards
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown(
                    f"""
                <div class="metric-card">
                    <div class="metric-label">📚 Courses</div>
                    <div class="metric-value">{summary.get("course_count", 0)}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with col2:
                missing = summary.get("missing_assignments", 0)
                badge_class = (
                    "badge-success"
                    if missing == 0
                    else "badge-warning"
                    if missing < 3
                    else "badge-danger"
                )
                st.markdown(
                    f"""
                <div class="metric-card">
                    <div class="metric-label">📝 Missing Work</div>
                    <div class="metric-value"><span class="badge {badge_class}">{missing}</span></div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with col3:
                attendance_rate = summary.get("attendance_rate", 0)
                badge_class = (
                    "badge-success"
                    if attendance_rate >= 95
                    else "badge-warning"
                    if attendance_rate >= 90
                    else "badge-danger"
                )
                st.markdown(
                    f"""
                <div class="metric-card">
                    <div class="metric-label">🏫 Attendance</div>
                    <div class="metric-value"><span class="badge {badge_class}">{attendance_rate}%</span></div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            with col4:
                days_absent = summary.get("days_absent", 0)
                st.markdown(
                    f"""
                <div class="metric-card">
                    <div class="metric-label">📅 Days Absent</div>
                    <div class="metric-value">{days_absent}</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

            st.markdown("<br>", unsafe_allow_html=True)
    except Exception:
        pass

    # Quick action buttons
    st.markdown("### ⚡ Quick Actions")
    col1, col2 = st.columns(2)

    # Quick action handlers use message buffer (HIGH-3)
    with col1:
        if st.button("📝 Missing Work", use_container_width=True, key="btn_missing"):
            result = get_quick_response("missing", st.session_state.student_name)
            response_text = format_quick_response(result)
            st.session_state.messages = add_message_to_buffer(
                st.session_state.messages, "user", "What are the missing assignments?"
            )
            st.session_state.messages = add_message_to_buffer(
                st.session_state.messages, "assistant", response_text
            )
            st.rerun()

        if st.button("📊 Current Grades", use_container_width=True, key="btn_grades"):
            result = get_quick_response("grades", st.session_state.student_name)
            response_text = format_quick_response(result)
            st.session_state.messages = add_message_to_buffer(
                st.session_state.messages, "user", "What are the current grades?"
            )
            st.session_state.messages = add_message_to_buffer(
                st.session_state.messages, "assistant", response_text
            )
            st.rerun()

    with col2:
        if st.button("📅 Due This Week", use_container_width=True, key="btn_upcoming"):
            result = get_quick_response("upcoming", st.session_state.student_name)
            response_text = format_quick_response(result)
            st.session_state.messages = add_message_to_buffer(
                st.session_state.messages, "user", "What's due this week?"
            )
            st.session_state.messages = add_message_to_buffer(
                st.session_state.messages, "assistant", response_text
            )
            st.rerun()

        if st.button("🏫 Attendance", use_container_width=True, key="btn_attendance"):
            result = get_quick_response("attendance", st.session_state.student_name)
            response_text = format_quick_response(result)
            st.session_state.messages = add_message_to_buffer(
                st.session_state.messages, "user", "How's the attendance?"
            )
            st.session_state.messages = add_message_to_buffer(
                st.session_state.messages, "assistant", response_text
            )
            st.rerun()

    st.divider()

    # Chat section header
    st.markdown("### 💬 Chat with SchoolPulse")

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)

    # Chat input (HIGH-3: uses message buffer)
    if prompt := st.chat_input("💭 Ask about your child's progress..."):
        # Add user message to buffer
        st.session_state.messages = add_message_to_buffer(st.session_state.messages, "user", prompt)

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response (HIGH-3: only send last 10 messages to AI)
        with st.chat_message("assistant"):
            with st.spinner("🔍 Looking up..."):
                if not api_key:
                    response = (
                        "⚠️ Please configure your Anthropic API key in secrets or environment."
                    )
                else:
                    # Get limited message history for AI context
                    messages_for_ai = get_messages_for_ai(
                        st.session_state.messages[:-1]  # Exclude the message we just added
                    )
                    response = get_ai_response(
                        prompt,
                        {"student_name": st.session_state.student_name},
                        messages_for_ai,
                        api_key,
                        st.session_state.model,
                    )
            st.markdown(response)

        # Add assistant response to buffer
        st.session_state.messages = add_message_to_buffer(
            st.session_state.messages, "assistant", response
        )

    # Show student summary and conversation starters when chat is empty
    if not st.session_state.messages:
        # Get summary with error handling - keep try/except narrow to avoid
        # catching st.rerun() exceptions from button handlers
        summary = None
        try:
            db_path = get_db_path()
            # MED-1: Use cached student summary
            summary = get_cached_student_summary(db_path, st.session_state.student_name)
        except Exception:
            pass  # summary remains None, will show fallback

        if summary and "error" not in summary:
            attendance_rate = summary.get("attendance_rate", 0)
            missing = summary.get("missing_assignments", 0)

            # Status emojis
            attendance_emoji = (
                "✅" if attendance_rate >= 95 else "⚠️" if attendance_rate >= 90 else "🔴"
            )
            missing_emoji = "✅" if missing == 0 else "⚠️" if missing < 3 else "🔴"

            st.markdown(
                f"""
            <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                        padding: 2rem;
                        border-radius: 15px;
                        border-left: 5px solid #667eea;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                <h3 style="color: #667eea; margin-top: 0;">👋 Welcome to SchoolPulse!</h3>
                <p style="font-size: 1.1rem; margin-bottom: 1.5rem;">
                    Here's a quick overview for <strong>{summary.get("name", "your student")}</strong>:
                </p>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                    <div style="background: white; padding: 1rem; border-radius: 10px; text-align: center;">
                        <div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;">📚 Courses</div>
                        <div style="font-size: 1.8rem; font-weight: 700; color: #667eea;">{summary.get("course_count", 0)}</div>
                    </div>
                    <div style="background: white; padding: 1rem; border-radius: 10px; text-align: center;">
                        <div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;">📝 Missing Work</div>
                        <div style="font-size: 1.8rem; font-weight: 700; color: #667eea;">{missing_emoji} {missing}</div>
                    </div>
                    <div style="background: white; padding: 1rem; border-radius: 10px; text-align: center;">
                        <div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;">🏫 Attendance</div>
                        <div style="font-size: 1.8rem; font-weight: 700; color: #667eea;">{attendance_emoji} {attendance_rate}%</div>
                    </div>
                </div>
                <p style="margin-top: 1.5rem; margin-bottom: 0; font-size: 1rem; color: #555;">
                    💡 <strong>Tip:</strong> Use the quick action buttons above or try the conversation starters below!
                </p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Show context-based conversation starters
            st.markdown("**💭 Try asking:**")
            starters = get_contextual_starters(summary)

            # Render starters in rows of 2
            for i in range(0, len(starters), 2):
                cols = st.columns(2)
                for j, col in enumerate(cols):
                    if i + j < len(starters):
                        starter = starters[i + j]
                        with col:
                            if st.button(
                                f"{starter['icon']} {starter['text']}",
                                key=f"starter_{i + j}",
                                use_container_width=True,
                            ):
                                # Add user message to buffer (HIGH-3)
                                st.session_state.messages = add_message_to_buffer(
                                    st.session_state.messages, "user", starter["text"]
                                )
                                # Get AI response
                                if api_key:
                                    response = get_ai_response(
                                        starter["text"],
                                        {"student_name": st.session_state.student_name},
                                        [],  # No history for first message
                                        api_key,
                                        st.session_state.model,
                                    )
                                else:
                                    response = "Please configure your Anthropic API key in secrets or environment."
                                # Add response to buffer (HIGH-3)
                                st.session_state.messages = add_message_to_buffer(
                                    st.session_state.messages, "assistant", response
                                )
                                st.rerun()
        else:
            st.markdown(
                """
            <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                        padding: 2rem;
                        border-radius: 15px;
                        border-left: 5px solid #667eea;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                <h3 style="color: #667eea; margin-top: 0;">👋 Welcome to SchoolPulse!</h3>
                <p style="font-size: 1.1rem;">
                    Your intelligent assistant for tracking your child's academic progress.
                </p>
                <p style="margin-bottom: 0;">
                    💡 Use the quick action buttons above or ask me about your child's progress!
                </p>
            </div>
            """,
                unsafe_allow_html=True,
            )


# Main entry point
def main() -> None:
    """Main application entry point.

    Orchestrates the application flow:
    1. Initialize session state
    2. Check authentication status
    3. Validate session (check for timeout)
    4. Render login page or main application

    FERPA Compliance:
        - Authentication required before accessing any student data
        - Session validation on every request
        - Automatic logout on session timeout
    """
    init_session_state()

    # Check if user is authenticated
    if not st.session_state.authenticated:
        handle_login()
        return

    # Validate session (may have expired)
    if not validate_current_session():
        st.warning("Your session has expired. Please log in again.")
        handle_login()
        return

    # Render main application
    render_main_app()


if __name__ == "__main__":
    main()
