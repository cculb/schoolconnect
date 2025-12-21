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
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Professional CSS styling
st.markdown("""
<style>
    /* Import modern font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global styles */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
        background: white;
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        margin: 2rem auto;
    }

    /* Header styling */
    .app-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }

    .app-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        padding: 0;
        color: white;
    }

    .app-subtitle {
        font-size: 1.1rem;
        font-weight: 400;
        margin-top: 0.5rem;
        opacity: 0.95;
        color: white;
    }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.12);
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
        margin: 0;
    }

    .metric-label {
        font-size: 0.9rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 500;
    }

    /* Quick action buttons */
    .stButton > button {
        width: 100%;
        margin: 0.25rem 0;
        border-radius: 12px;
        padding: 1rem;
        font-weight: 600;
        font-size: 1rem;
        border: none;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }

    /* Chat messages */
    .stChatMessage {
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    /* Chat input */
    .stChatInputContainer {
        border-top: 1px solid #e0e0e0;
        padding-top: 1rem;
        margin-top: 1rem;
    }

    /* Dividers */
    hr {
        margin: 2rem 0;
        border: none;
        border-top: 2px solid #f0f0f0;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        color: white;
    }

    section[data-testid="stSidebar"] .stTextInput > label,
    section[data-testid="stSidebar"] .stSelectbox > label {
        color: white !important;
        font-weight: 500;
    }

    /* Info box */
    .stAlert {
        border-radius: 12px;
        border-left: 4px solid #667eea;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
    }

    /* Progress bars */
    .progress-bar {
        width: 100%;
        height: 8px;
        background: #e0e0e0;
        border-radius: 10px;
        overflow: hidden;
        margin-top: 0.5rem;
    }

    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        transition: width 0.3s ease;
    }

    /* Badge styling */
    .badge {
        display: inline-block;
        padding: 0.35rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.25rem;
    }

    .badge-success {
        background: #10b981;
        color: white;
    }

    .badge-warning {
        background: #f59e0b;
        color: white;
    }

    .badge-danger {
        background: #ef4444;
        color: white;
    }

    .badge-info {
        background: #667eea;
        color: white;
    }

    /* Mobile responsive */
    @media (max-width: 768px) {
        .main .block-container {
            margin: 1rem;
            padding: 1rem;
        }

        .app-title {
            font-size: 1.8rem;
        }

        .app-subtitle {
            font-size: 0.95rem;
        }

        .metric-value {
            font-size: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="app-header">
    <h1 class="app-title">📚 SchoolPulse</h1>
    <p class="app-subtitle">Your child's academic progress at a glance</p>
</div>
""", unsafe_allow_html=True)

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
    """Format a quick response result with enhanced visual styling."""
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
            output += f"<div style='background: #fef3c7; padding: 1rem; border-radius: 10px; border-left: 4px solid #f59e0b; margin-bottom: 1rem;'>"
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
                grade = item.get('letter_grade') or item.get('percent') or 'N/A'
                percent = f" ({item['percent']}%)" if item.get('percent') else ""
                teacher = item.get('teacher_name', 'N/A')
                output += f"| {item['course_name']} | {teacher} | **{grade}**{percent} |\n"

    elif title == "Attendance Summary":
        if isinstance(data, dict) and "error" not in data:
            rate = data.get('rate', 0)

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
            output += f"\n**📊 Details:**\n"
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
            output += f"<div style='background: #dbeafe; padding: 1rem; border-radius: 10px; border-left: 4px solid #3b82f6; margin-bottom: 1rem;'>"
            output += f"<strong>📌 {len(data)} assignment(s) coming up</strong></div>\n\n"
            for i, item in enumerate(data, 1):
                output += f"**{i}. {item['assignment_name']}**\n"
                output += f"- 📚 Course: `{item['course_name']}`\n"
                output += f"- 📅 Due: {item.get('due_date', 'N/A')}\n\n"

    elif title == "Student Summary":
        if isinstance(data, dict) and "error" not in data:
            output += f"### 👨‍🎓 {data.get('name', 'Student')} - Grade {data.get('grade_level', 'N/A')}\n\n"

            missing = data.get('missing_assignments', 0)
            attendance = data.get('attendance_rate', 0)

            output += f"| Metric | Value |\n"
            output += f"|--------|-------|\n"
            output += f"| 📚 Courses | {data.get('course_count', 0)} |\n"
            output += f"| 📝 Missing Work | {missing} |\n"
            output += f"| 🏫 Attendance | {attendance}% |\n"
            output += f"| 📅 Days Absent | {data.get('days_absent', 0)} |\n"
        else:
            output += "Unable to retrieve student summary."

    return output


# Dashboard metrics
try:
    db_path = get_db_path()
    summary = get_student_summary(db_path, st.session_state.student_name)

    if "error" not in summary:
        st.markdown("### 📊 Dashboard Overview")

        # Create metric cards
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">📚 Courses</div>
                <div class="metric-value">{summary.get('course_count', 0)}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            missing = summary.get('missing_assignments', 0)
            badge_class = "badge-success" if missing == 0 else "badge-warning" if missing < 3 else "badge-danger"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">📝 Missing Work</div>
                <div class="metric-value"><span class="badge {badge_class}">{missing}</span></div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            attendance_rate = summary.get('attendance_rate', 0)
            badge_class = "badge-success" if attendance_rate >= 95 else "badge-warning" if attendance_rate >= 90 else "badge-danger"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">🏫 Attendance</div>
                <div class="metric-value"><span class="badge {badge_class}">{attendance_rate}%</span></div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            days_absent = summary.get('days_absent', 0)
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">📅 Days Absent</div>
                <div class="metric-value">{days_absent}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
except Exception:
    pass

# Quick action buttons
st.markdown("### ⚡ Quick Actions")
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

# Chat section header
st.markdown("### 💬 Chat with SchoolPulse")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("💭 Ask about your child's progress..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("🔍 Looking up..."):
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

# Show welcome message if no chat history
if not st.session_state.messages:
    try:
        db_path = get_db_path()
        summary = get_student_summary(db_path, st.session_state.student_name)

        if "error" not in summary:
            attendance_rate = summary.get('attendance_rate', 0)
            missing = summary.get('missing_assignments', 0)

            # Status emojis
            attendance_emoji = "✅" if attendance_rate >= 95 else "⚠️" if attendance_rate >= 90 else "🔴"
            missing_emoji = "✅" if missing == 0 else "⚠️" if missing < 3 else "🔴"

            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                        padding: 2rem;
                        border-radius: 15px;
                        border-left: 5px solid #667eea;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                <h3 style="color: #667eea; margin-top: 0;">👋 Welcome to SchoolPulse!</h3>
                <p style="font-size: 1.1rem; margin-bottom: 1.5rem;">
                    Here's a quick overview for <strong>{summary.get('name', 'your student')}</strong>:
                </p>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                    <div style="background: white; padding: 1rem; border-radius: 10px; text-align: center;">
                        <div style="font-size: 0.9rem; color: #666; margin-bottom: 0.5rem;">📚 Courses</div>
                        <div style="font-size: 1.8rem; font-weight: 700; color: #667eea;">{summary.get('course_count', 0)}</div>
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
                    💡 <strong>Tip:</strong> Use the quick action buttons above or ask me anything about your child's progress!
                </p>
            </div>
            """, unsafe_allow_html=True)
    except Exception:
        st.markdown("""
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
        """, unsafe_allow_html=True)
