"""SchoolPulse - Parent Chat Interface for PowerSchool Data."""

import os

import streamlit as st
from ai_assistant import (
    AVAILABLE_MODELS,
    DEFAULT_MODEL,
    get_ai_response,
    get_db_path,
    get_quick_response,
)
from data_queries import get_student_summary


def get_contextual_starters(summary: dict) -> list[dict]:
    """Generate conversation starters based on student data."""
    starters = []

    # Always include general starters
    starters.append({"icon": "🎯", "text": "What should we prioritize this week?"})
    starters.append({"icon": "📊", "text": "How is my child doing overall?"})

    # Context-based starters
    missing = summary.get("missing_assignments", 0)
    if missing > 0:
        starters.append({
            "icon": "📋",
            "text": f"How can we address the {missing} missing assignment{'s' if missing > 1 else ''}?"
        })

    attendance = summary.get("attendance_rate", 100)
    if attendance < 90:
        starters.append({
            "icon": "🏫",
            "text": f"Attendance is at {attendance}%. Should I be concerned?"
        })
    elif attendance >= 95:
        starters.append({
            "icon": "🏫",
            "text": "Great attendance! How can we maintain it?"
        })

    days_absent = summary.get("days_absent", 0)
    if days_absent > 3:
        starters.append({
            "icon": "📅",
            "text": f"My child has been absent {days_absent} days. What should I know?"
        })

    # Add helpful general starters
    starters.append({"icon": "✉️", "text": "Help me write an email to a teacher"})
    starters.append({"icon": "💡", "text": "Suggest study strategies for middle school"})

    return starters[:6]  # Limit to 6 starters


# Page configuration - mobile friendly
st.set_page_config(
    page_title="SchoolPulse",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Dark theme CSS with mobile-friendly styling
st.markdown("""
<style>
    /* === Base Layout === */
    .stApp { max-width: 100%; }

    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 800px;
    }

    /* === Typography === */
    h1 {
        font-size: 1.5rem !important;
        color: #E4E6EB !important;
    }
    h3 {
        font-size: 1rem !important;
        color: #A8ABB0 !important;
    }

    /* === Chat Messages === */
    .stChatMessage {
        padding: 0.5rem;
        border-radius: 12px;
    }

    /* === Buttons === */
    .stButton > button {
        width: 100%;
        margin: 0.25rem 0;
        border-radius: 20px;
        background-color: #323844 !important;
        border: 1px solid #454B58 !important;
        color: #E4E6EB !important;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        background-color: #3D4450 !important;
        border-color: #5B8DEF !important;
        box-shadow: 0 2px 8px rgba(91, 141, 239, 0.25);
    }

    .stButton > button:active {
        background-color: #5B8DEF !important;
        color: #FFFFFF !important;
    }

    /* Quick action button styling */
    div[data-testid="column"] > div > div > div > button {
        font-size: 0.9rem;
        padding: 0.5rem;
    }

    /* === Chat Input === */
    .stChatInputContainer {
        position: sticky;
        bottom: 0;
        background: #1E2128;
        padding: 0.5rem 0;
        border-top: 1px solid #323844;
    }

    [data-testid="stChatInput"] textarea {
        background-color: #282C35 !important;
        border: 1px solid #454B58 !important;
        border-radius: 24px !important;
        color: #E4E6EB !important;
    }

    [data-testid="stChatInput"] textarea:focus {
        border-color: #5B8DEF !important;
        box-shadow: 0 0 0 2px rgba(91, 141, 239, 0.25) !important;
    }

    [data-testid="stChatInput"] textarea::placeholder {
        color: #72767D !important;
    }

    /* === Sidebar === */
    [data-testid="stSidebar"] {
        background-color: #1A1D23 !important;
        border-right: 1px solid #323844;
    }

    /* === Text Inputs === */
    .stTextInput > div > div > input {
        background-color: #282C35 !important;
        border: 1px solid #454B58 !important;
        border-radius: 8px !important;
        color: #E4E6EB !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: #5B8DEF !important;
        box-shadow: 0 0 0 2px rgba(91, 141, 239, 0.25) !important;
    }

    /* === Select Boxes === */
    .stSelectbox > div > div {
        background-color: #282C35 !important;
        border: 1px solid #454B58 !important;
        border-radius: 8px !important;
    }

    /* === Info Box (Welcome message) === */
    [data-testid="stAlert"] {
        background-color: rgba(91, 141, 239, 0.1) !important;
        border: 1px solid rgba(91, 141, 239, 0.3) !important;
        border-radius: 12px;
    }

    /* === Dividers === */
    hr {
        border-color: #323844 !important;
    }

    /* === Caption text === */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #72767D !important;
    }

    /* === Conversation Starter Pills === */
    .starter-btn button {
        background-color: #282C35 !important;
        border: 1px solid #454B58 !important;
        font-size: 0.85rem !important;
        padding: 0.4rem 0.8rem !important;
    }

    .starter-btn button:hover {
        background-color: #323844 !important;
        border-color: #5B8DEF !important;
    }

    /* === Scrollbar styling === */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #1E2128;
    }

    ::-webkit-scrollbar-thumb {
        background: #454B58;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #5B8DEF;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("📚 SchoolPulse")
st.caption("Your child's academic progress at a glance")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "student_name" not in st.session_state:
    st.session_state.student_name = "Delilah"

if "api_key" not in st.session_state:
    # Try to get from environment or secrets
    st.session_state.api_key = os.environ.get("ANTHROPIC_API_KEY", "")

if "model" not in st.session_state:
    st.session_state.model = DEFAULT_MODEL

# Sidebar for settings
with st.sidebar:
    st.header("⚙️ Settings")

    # API Key input
    api_key_input = st.text_input(
        "Anthropic API Key",
        value=st.session_state.api_key,
        type="password",
        help="Enter your Anthropic API key"
    )
    if api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input

    st.divider()

    # Model selection
    model_options = list(AVAILABLE_MODELS.keys())
    current_index = model_options.index(st.session_state.model) if st.session_state.model in model_options else 0

    selected_model = st.selectbox(
        "AI Model",
        options=model_options,
        format_func=lambda x: AVAILABLE_MODELS[x],
        index=current_index,
        help="Select the Claude model to use"
    )
    if selected_model != st.session_state.model:
        st.session_state.model = selected_model

    st.divider()

    # Student name (for demo purposes)
    student_input = st.text_input(
        "Student Name",
        value=st.session_state.student_name,
        help="Enter the student's first name"
    )
    if student_input != st.session_state.student_name:
        st.session_state.student_name = student_input

    st.divider()

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


def format_quick_response(result: dict) -> str:
    """Format a quick response result as markdown."""
    if "error" in result:
        return f"❌ {result['error']}"

    title = result.get("title", "Results")
    data = result.get("data", [])

    output = f"**{title}**\n\n"

    if title == "Missing Assignments":
        if not data:
            output += "✅ No missing assignments! Great job!"
        else:
            output += f"Found {len(data)} missing assignment(s):\n\n"
            for item in data:
                output += f"- **{item['assignment_name']}**\n"
                output += f"  - Course: {item['course_name']}\n"
                output += f"  - Teacher: {item.get('teacher_name', 'N/A')}\n"
                output += f"  - Due: {item.get('due_date', 'N/A')}\n\n"

    elif title == "Current Grades":
        if not data:
            output += "No grade data available."
        else:
            for item in data:
                grade = item.get('letter_grade') or item.get('percent') or 'N/A'
                percent = f" ({item['percent']}%)" if item.get('percent') else ""
                output += f"- **{item['course_name']}**: {grade}{percent}\n"

    elif title == "Attendance Summary":
        if isinstance(data, dict) and "error" not in data:
            rate = data.get('rate', 0)
            status = "⚠️" if rate < 90 else "✅"
            output += f"{status} **Attendance Rate**: {rate}%\n\n"
            output += f"- Days Absent: {data.get('days_absent', 0)}\n"
            output += f"- Tardies: {data.get('tardies', 0)}\n"
            output += f"- Total School Days: {data.get('total_days', 0)}\n"

            if rate < 90:
                output += "\n⚠️ *Attendance is below 90%. Consider reviewing attendance records.*"
        else:
            output += "No attendance data available."

    elif title == "Due This Week":
        if not data:
            output += "📅 No assignments due this week!"
        else:
            output += f"Found {len(data)} assignment(s) due soon:\n\n"
            for item in data:
                output += f"- **{item['assignment_name']}**\n"
                output += f"  - Course: {item['course_name']}\n"
                output += f"  - Due: {item.get('due_date', 'N/A')}\n\n"

    elif title == "Student Summary":
        if isinstance(data, dict) and "error" not in data:
            output += f"**{data.get('name', 'Student')}** - Grade {data.get('grade_level', 'N/A')}\n\n"
            output += f"- 📚 Enrolled in {data.get('course_count', 0)} courses\n"
            output += f"- 📝 Missing assignments: {data.get('missing_assignments', 0)}\n"
            output += f"- 🏫 Attendance: {data.get('attendance_rate', 0)}%\n"
            output += f"- 📅 Days absent: {data.get('days_absent', 0)}\n"
        else:
            output += "Unable to retrieve student summary."

    return output


# Quick action buttons
st.subheader("Quick Actions")
col1, col2 = st.columns(2)

with col1:
    if st.button("📝 Missing Work", use_container_width=True, key="btn_missing"):
        result = get_quick_response("missing", st.session_state.student_name)
        response_text = format_quick_response(result)
        st.session_state.messages.append({"role": "user", "content": "What are the missing assignments?"})
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        st.rerun()

    if st.button("📊 Current Grades", use_container_width=True, key="btn_grades"):
        result = get_quick_response("grades", st.session_state.student_name)
        response_text = format_quick_response(result)
        st.session_state.messages.append({"role": "user", "content": "What are the current grades?"})
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        st.rerun()

with col2:
    if st.button("📅 Due This Week", use_container_width=True, key="btn_upcoming"):
        result = get_quick_response("upcoming", st.session_state.student_name)
        response_text = format_quick_response(result)
        st.session_state.messages.append({"role": "user", "content": "What's due this week?"})
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        st.rerun()

    if st.button("🏫 Attendance", use_container_width=True, key="btn_attendance"):
        result = get_quick_response("attendance", st.session_state.student_name)
        response_text = format_quick_response(result)
        st.session_state.messages.append({"role": "user", "content": "How's the attendance?"})
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        st.rerun()

st.divider()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about your child's progress..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Looking up..."):
            if not st.session_state.api_key:
                response = "⚠️ Please enter your Anthropic API key in the sidebar settings."
            else:
                response = get_ai_response(
                    prompt,
                    {"student_name": st.session_state.student_name},
                    st.session_state.messages[:-1],  # Exclude the message we just added
                    st.session_state.api_key,
                    st.session_state.model
                )
        st.markdown(response)

    # Add assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Show student summary and conversation starters when chat is empty
if not st.session_state.messages:
    try:
        db_path = get_db_path()
        summary = get_student_summary(db_path, st.session_state.student_name)

        if "error" not in summary:
            st.info(f"""
**Welcome!** Here's a quick overview for **{summary.get('name', 'your student')}**:

- 📚 **Courses**: {summary.get('course_count', 0)}
- 📝 **Missing Assignments**: {summary.get('missing_assignments', 0)}
- 🏫 **Attendance**: {summary.get('attendance_rate', 0)}%
            """)

            # Show context-based conversation starters
            st.markdown("**Try asking:**")
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
                                key=f"starter_{i+j}",
                                use_container_width=True
                            ):
                                # Add user message
                                st.session_state.messages.append({
                                    "role": "user",
                                    "content": starter['text']
                                })
                                # Get AI response
                                if st.session_state.api_key:
                                    response = get_ai_response(
                                        starter['text'],
                                        {"student_name": st.session_state.student_name},
                                        [],
                                        st.session_state.api_key,
                                        st.session_state.model
                                    )
                                else:
                                    response = "Please enter your Anthropic API key in the sidebar settings."
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": response
                                })
                                st.rerun()
        else:
            st.info("Welcome to SchoolPulse! Use the quick action buttons or ask me about your child's progress.")
    except Exception:
        st.info("Welcome to SchoolPulse! Use the quick action buttons or ask me about your child's progress.")
