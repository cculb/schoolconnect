"""Claude AI integration for SchoolPulse chat assistant."""

import json
import os
from pathlib import Path
from typing import Any

from anthropic import Anthropic
from data_queries import (
    get_all_courses,
    get_assignment_stats,
    get_attendance_summary,
    get_course_details,
    get_current_grades,
    get_missing_assignments,
    get_student_summary,
    get_upcoming_assignments,
)

SYSTEM_PROMPT = """You are SchoolPulse, a helpful assistant for parents to understand their child's academic progress.

You have access to these tools to query the student database:
- get_missing_assignments: Returns list of missing/late assignments
- get_current_grades: Returns current grades by course
- get_attendance_summary: Returns attendance rate, absences, tardies
- get_upcoming_assignments: Returns assignments due soon (default 7 days)
- get_course_details: Returns detailed info about a specific course
- get_student_summary: Returns overall student summary
- get_all_courses: Returns list of all enrolled courses
- get_assignment_stats: Returns assignment completion statistics

When answering:
1. Always use the tools to get current data - never make assumptions about grades, attendance, or assignments
2. Be supportive and solution-oriented - parents want to help their child succeed
3. Provide specific, actionable advice when issues are found
4. If attendance is below 90% or there are missing assignments, acknowledge the concern constructively
5. Offer to help draft emails to teachers when appropriate
6. Keep responses concise but informative

The student's name is provided in the context. Use it when querying the database."""


# Available models
AVAILABLE_MODELS = {
    "claude-opus-4-5-20250514": "Claude Opus 4.5 (Most Capable)",
    "claude-sonnet-4-20250514": "Claude Sonnet 4 (Balanced)",
    "claude-haiku-3-5-20241022": "Claude Haiku 3.5 (Fastest)",
}

DEFAULT_MODEL = "claude-opus-4-5-20250514"

# Maximum number of tool use iterations to prevent infinite loops
MAX_TOOL_ITERATIONS = 15

TOOLS = [
    {
        "name": "get_missing_assignments",
        "description": "Get all missing or late assignments for the student. Returns assignment name, course, teacher, due date.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_current_grades",
        "description": "Get current grades for all courses. Returns course name, teacher, letter grade, and percentage.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_attendance_summary",
        "description": "Get attendance summary including attendance rate, days absent, and tardies.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_upcoming_assignments",
        "description": "Get assignments due in the next N days (default 7).",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to look ahead (default 7)",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_course_details",
        "description": "Get detailed information about a specific course including grade, teacher contact, and recent assignments.",
        "input_schema": {
            "type": "object",
            "properties": {
                "course_name": {
                    "type": "string",
                    "description": "Name of the course (partial match supported)",
                }
            },
            "required": ["course_name"],
        },
    },
    {
        "name": "get_student_summary",
        "description": "Get an overall summary of the student including grade level, courses, attendance, and missing work count.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_all_courses",
        "description": "Get list of all courses the student is enrolled in.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_assignment_stats",
        "description": "Get assignment completion statistics including total, completed, missing, and completion rate.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


def get_db_path() -> str:
    """Get the database path."""
    # Check environment variable first
    if os.environ.get("DATABASE_PATH"):
        return os.environ["DATABASE_PATH"]

    # Check parent directory
    parent_db = Path(__file__).parent.parent / "powerschool.db"
    if parent_db.exists():
        return str(parent_db)

    # Default to current directory
    return str(Path(__file__).parent / "powerschool.db")


def execute_tool(tool_name: str, tool_input: dict, student_name: str) -> Any:
    """Execute a tool and return the result."""
    db_path = get_db_path()

    if tool_name == "get_missing_assignments":
        return get_missing_assignments(db_path, student_name)
    elif tool_name == "get_current_grades":
        return get_current_grades(db_path, student_name)
    elif tool_name == "get_attendance_summary":
        return get_attendance_summary(db_path, student_name)
    elif tool_name == "get_upcoming_assignments":
        days = tool_input.get("days", 7)
        return get_upcoming_assignments(db_path, student_name, days)
    elif tool_name == "get_course_details":
        course_name = tool_input.get("course_name", "")
        return get_course_details(db_path, student_name, course_name)
    elif tool_name == "get_student_summary":
        return get_student_summary(db_path, student_name)
    elif tool_name == "get_all_courses":
        return get_all_courses(db_path, student_name)
    elif tool_name == "get_assignment_stats":
        return get_assignment_stats(db_path, student_name)
    else:
        return {"error": f"Unknown tool: {tool_name}"}


def get_ai_response(
    user_message: str,
    student_context: dict,
    chat_history: list,
    api_key: str | None = None,
    model: str | None = None,
) -> str:
    """Get AI response using Claude with tool use."""

    # Use default model if not specified
    if not model:
        model = DEFAULT_MODEL

    # Get API key
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        return "Error: ANTHROPIC_API_KEY not set. Please configure your API key."

    client = Anthropic(api_key=api_key)

    student_name = student_context.get("student_name", "Delilah")

    # Build messages with context
    system_with_context = f"""{SYSTEM_PROMPT}

Current student context:
- Student name: {student_name}
- Use this name when calling database query tools."""

    # Convert chat history to API format
    messages = []
    for msg in chat_history[-10:]:  # Keep last 10 messages for context
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Add current user message
    messages.append({"role": "user", "content": user_message})

    try:
        # Initial API call with tools
        response = client.messages.create(
            model=model, max_tokens=1024, system=system_with_context, tools=TOOLS, messages=messages
        )

        # Handle tool use loop with iteration limit
        iteration_count = 0
        while response.stop_reason == "tool_use":
            iteration_count += 1

            # Check for infinite loop protection
            if iteration_count > MAX_TOOL_ITERATIONS:
                return (
                    f"Error: Maximum tool iteration limit ({MAX_TOOL_ITERATIONS}) reached. "
                    "This may indicate an infinite loop. Please try rephrasing your question."
                )

            # Find tool use blocks
            tool_uses = [block for block in response.content if block.type == "tool_use"]

            # Execute each tool and collect results
            tool_results = []
            for tool_use in tool_uses:
                result = execute_tool(tool_use.name, tool_use.input, student_name)
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": json.dumps(result, default=str),
                    }
                )

            # Add assistant's response and tool results to messages
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

            # Continue the conversation
            response = client.messages.create(
                model=model,
                max_tokens=1024,
                system=system_with_context,
                tools=TOOLS,
                messages=messages,
            )

        # Extract text response
        text_blocks = [block.text for block in response.content if hasattr(block, "text")]
        return "\n".join(text_blocks) if text_blocks else "I couldn't generate a response."

    except Exception as e:
        return f"Error communicating with AI: {str(e)}"


def get_quick_response(query_type: str, student_name: str = "Delilah") -> dict:
    """Get a quick response for pre-built queries without AI."""
    db_path = get_db_path()

    if query_type == "missing":
        data = get_missing_assignments(db_path, student_name)
        return {"title": "Missing Assignments", "data": data, "count": len(data)}
    elif query_type == "grades":
        data = get_current_grades(db_path, student_name)
        return {"title": "Current Grades", "data": data, "count": len(data)}
    elif query_type == "attendance":
        data = get_attendance_summary(db_path, student_name)
        return {"title": "Attendance Summary", "data": data}
    elif query_type == "upcoming":
        data = get_upcoming_assignments(db_path, student_name, days=7)
        return {"title": "Due This Week", "data": data, "count": len(data)}
    elif query_type == "summary":
        data = get_student_summary(db_path, student_name)
        return {"title": "Student Summary", "data": data}
    else:
        return {"error": f"Unknown query type: {query_type}"}
