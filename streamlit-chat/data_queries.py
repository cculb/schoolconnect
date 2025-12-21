"""Database query functions for SchoolPulse."""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def get_student_id(db_path: str, student_name: str) -> Optional[int]:
    """Get student ID from name (partial match on first name)."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Try to match by first name (case-insensitive)
    cursor.execute("""
        SELECT id FROM students
        WHERE LOWER(first_name) LIKE LOWER(?)
        OR LOWER(first_name || ' ' || COALESCE(last_name, '')) LIKE LOWER(?)
        LIMIT 1
    """, (f"%{student_name}%", f"%{student_name}%"))

    result = cursor.fetchone()
    conn.close()

    return result["id"] if result else None


def get_student_summary(db_path: str, student_name: str) -> dict:
    """Get overall summary for a student."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    student_id = get_student_id(db_path, student_name)
    if not student_id:
        conn.close()
        return {"error": f"Student '{student_name}' not found"}

    # Get student info
    cursor.execute("""
        SELECT first_name, last_name, grade_level, school_name
        FROM students WHERE id = ?
    """, (student_id,))
    student = cursor.fetchone()

    # Get missing assignment count
    cursor.execute("""
        SELECT COUNT(*) as count FROM assignments
        WHERE student_id = ? AND status = 'Missing'
    """, (student_id,))
    missing_count = cursor.fetchone()["count"]

    # Get attendance
    cursor.execute("""
        SELECT attendance_rate, days_absent, tardies, total_days
        FROM attendance_summary WHERE student_id = ?
        ORDER BY recorded_at DESC LIMIT 1
    """, (student_id,))
    attendance = cursor.fetchone()

    # Get course count
    cursor.execute("""
        SELECT COUNT(DISTINCT course_name) as count FROM courses WHERE student_id = ?
    """, (student_id,))
    course_count = cursor.fetchone()["count"]

    conn.close()

    return {
        "student_id": student_id,
        "name": f"{student['first_name']} {student['last_name'] or ''}".strip(),
        "grade_level": student["grade_level"],
        "school_name": student["school_name"],
        "missing_assignments": missing_count,
        "attendance_rate": attendance["attendance_rate"] if attendance else None,
        "days_absent": attendance["days_absent"] if attendance else 0,
        "tardies": attendance["tardies"] if attendance else 0,
        "total_days": attendance["total_days"] if attendance else 0,
        "course_count": course_count,
    }


def get_missing_assignments(db_path: str, student_name: str) -> list[dict]:
    """Get list of missing assignments for a student."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    student_id = get_student_id(db_path, student_name)
    if not student_id:
        conn.close()
        return []

    cursor.execute("""
        SELECT
            assignment_name,
            course_name,
            teacher_name,
            category,
            due_date,
            term
        FROM assignments
        WHERE student_id = ? AND status = 'Missing'
        ORDER BY due_date DESC
    """, (student_id,))

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_current_grades(db_path: str, student_name: str) -> list[dict]:
    """Get current grades for all courses."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    student_id = get_student_id(db_path, student_name)
    if not student_id:
        conn.close()
        return []

    cursor.execute("""
        SELECT
            c.course_name,
            c.teacher_name,
            c.room,
            g.term,
            g.letter_grade,
            g.percent
        FROM courses c
        LEFT JOIN grades g ON g.course_id = c.id AND g.student_id = c.student_id
        WHERE c.student_id = ?
        ORDER BY c.course_name
    """, (student_id,))

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_attendance_summary(db_path: str, student_name: str) -> dict:
    """Get attendance summary for a student."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    student_id = get_student_id(db_path, student_name)
    if not student_id:
        conn.close()
        return {"error": f"Student '{student_name}' not found"}

    cursor.execute("""
        SELECT
            term,
            attendance_rate as rate,
            days_present,
            days_absent,
            tardies,
            total_days
        FROM attendance_summary
        WHERE student_id = ?
        ORDER BY recorded_at DESC
        LIMIT 1
    """, (student_id,))

    result = cursor.fetchone()
    conn.close()

    if result:
        return dict(result)
    return {"error": "No attendance data found"}


def get_upcoming_assignments(db_path: str, student_name: str, days: int = 7) -> list[dict]:
    """Get assignments due in the next N days."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    student_id = get_student_id(db_path, student_name)
    if not student_id:
        conn.close()
        return []

    today = datetime.now().date()
    end_date = today + timedelta(days=days)

    cursor.execute("""
        SELECT
            assignment_name,
            course_name,
            teacher_name,
            category,
            due_date,
            status
        FROM assignments
        WHERE student_id = ?
          AND due_date >= ?
          AND due_date <= ?
          AND status != 'Collected'
        ORDER BY due_date ASC
    """, (student_id, today.isoformat(), end_date.isoformat()))

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_course_details(db_path: str, student_name: str, course_name: str) -> dict:
    """Get detailed information about a specific course."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    student_id = get_student_id(db_path, student_name)
    if not student_id:
        conn.close()
        return {"error": f"Student '{student_name}' not found"}

    # Get course info
    cursor.execute("""
        SELECT
            c.course_name,
            c.teacher_name,
            c.teacher_email,
            c.room,
            c.term
        FROM courses c
        WHERE c.student_id = ? AND LOWER(c.course_name) LIKE LOWER(?)
        LIMIT 1
    """, (student_id, f"%{course_name}%"))

    course = cursor.fetchone()
    if not course:
        conn.close()
        return {"error": f"Course '{course_name}' not found"}

    course_data = dict(course)

    # Get grade for this course
    cursor.execute("""
        SELECT g.letter_grade, g.percent, g.term
        FROM grades g
        JOIN courses c ON c.id = g.course_id
        WHERE c.student_id = ? AND LOWER(c.course_name) LIKE LOWER(?)
        ORDER BY g.recorded_at DESC
        LIMIT 1
    """, (student_id, f"%{course_name}%"))

    grade = cursor.fetchone()
    if grade:
        course_data["letter_grade"] = grade["letter_grade"]
        course_data["percent"] = grade["percent"]

    # Get missing assignments for this course
    cursor.execute("""
        SELECT assignment_name, due_date, category
        FROM assignments
        WHERE student_id = ?
          AND LOWER(course_name) LIKE LOWER(?)
          AND status = 'Missing'
        ORDER BY due_date DESC
    """, (student_id, f"%{course_name}%"))

    course_data["missing_assignments"] = [dict(row) for row in cursor.fetchall()]

    # Get recent assignments
    cursor.execute("""
        SELECT assignment_name, due_date, score, max_score, status, category
        FROM assignments
        WHERE student_id = ?
          AND LOWER(course_name) LIKE LOWER(?)
        ORDER BY due_date DESC
        LIMIT 5
    """, (student_id, f"%{course_name}%"))

    course_data["recent_assignments"] = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return course_data


def run_custom_query(db_path: str, sql: str) -> list[dict]:
    """Run a custom read-only SQL query."""
    # Basic safety check - only allow SELECT
    sql_lower = sql.strip().lower()
    if not sql_lower.startswith("select"):
        return [{"error": "Only SELECT queries are allowed"}]

    # Block dangerous keywords
    dangerous = ["insert", "update", "delete", "drop", "alter", "create", "truncate"]
    for keyword in dangerous:
        if keyword in sql_lower:
            return [{"error": f"Query contains forbidden keyword: {keyword}"}]

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute(sql)
        results = [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        results = [{"error": str(e)}]

    conn.close()
    return results


def get_all_courses(db_path: str, student_name: str) -> list[dict]:
    """Get list of all courses for a student."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    student_id = get_student_id(db_path, student_name)
    if not student_id:
        conn.close()
        return []

    cursor.execute("""
        SELECT DISTINCT
            course_name,
            teacher_name,
            teacher_email,
            room
        FROM courses
        WHERE student_id = ?
        ORDER BY course_name
    """, (student_id,))

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_assignment_stats(db_path: str, student_name: str) -> dict:
    """Get assignment completion statistics."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    student_id = get_student_id(db_path, student_name)
    if not student_id:
        conn.close()
        return {"error": f"Student '{student_name}' not found"}

    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'Collected' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'Missing' THEN 1 ELSE 0 END) as missing,
            SUM(CASE WHEN status = 'Late' THEN 1 ELSE 0 END) as late
        FROM assignments
        WHERE student_id = ?
    """, (student_id,))

    result = cursor.fetchone()
    conn.close()

    if result:
        total = result["total"] or 0
        completed = result["completed"] or 0
        return {
            "total": total,
            "completed": completed,
            "missing": result["missing"] or 0,
            "late": result["late"] or 0,
            "completion_rate": round(100 * completed / total, 1) if total > 0 else 0
        }
    return {"total": 0, "completed": 0, "missing": 0, "late": 0, "completion_rate": 0}
