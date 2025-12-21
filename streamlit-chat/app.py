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

# Page configuration - mobile friendly
st.set_page_config(
    page_title="SchoolPulse",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Mobile-friendly CSS
st.markdown("""
<style>
    .stApp { max-width: 100%; }
    .stChatMessage { padding: 0.5rem; }
    .stButton > button {
        width: 100%;
        margin: 0.25rem 0;
        border-radius: 20px;
    }
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 800px;
    }
    /* Make chat input sticky at bottom on mobile */
    .stChatInputContainer {
        position: sticky;
        bottom: 0;
        background: white;
        padding: 0.5rem 0;
    }
    /* Quick action button styling */
    div[data-testid="column"] > div > div > div > button {
        font-size: 0.9rem;
        padding: 0.5rem;
    }
    /* Reduce header size on mobile */
    h1 { font-size: 1.5rem !important; }
    h3 { font-size: 1rem !important; }
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

# Show student summary at start if no messages
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

Use the quick action buttons above or ask me anything!
            """)
    except Exception:
        st.info("Welcome to SchoolPulse! Use the quick action buttons or ask me about your child's progress.")
