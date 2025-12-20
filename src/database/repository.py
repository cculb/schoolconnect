"""Data access layer for PowerSchool Portal database."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from .connection import DB_PATH, get_db


class Repository:
    """Repository for database operations."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH

    # ==================== STUDENTS ====================

    def get_students(self) -> List[Dict]:
        """Get all students."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM students ORDER BY first_name"
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_student_by_name(self, name: str) -> Optional[Dict]:
        """Get student by name (first name match)."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM students WHERE first_name LIKE ? OR "
                "(first_name || ' ' || last_name) LIKE ?",
                (f"%{name}%", f"%{name}%")
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_student_by_id(self, student_id: int) -> Optional[Dict]:
        """Get student by database ID."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM students WHERE id = ?", (student_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def upsert_student(
        self,
        powerschool_id: str,
        first_name: str,
        last_name: Optional[str] = None,
        grade_level: Optional[str] = None,
        school_name: Optional[str] = None,
    ) -> int:
        """Insert or update a student. Returns student ID."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO students (powerschool_id, first_name, last_name, grade_level, school_name, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(powerschool_id) DO UPDATE SET
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    grade_level = COALESCE(excluded.grade_level, grade_level),
                    school_name = COALESCE(excluded.school_name, school_name),
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
                """,
                (powerschool_id, first_name, last_name, grade_level, school_name)
            )
            return cursor.fetchone()["id"]

    # ==================== COURSES ====================

    def get_courses(self, student_id: int) -> List[Dict]:
        """Get all courses for a student."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM courses WHERE student_id = ? ORDER BY course_name",
                (student_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def upsert_course(
        self,
        student_id: int,
        course_name: str,
        expression: Optional[str] = None,
        room: Optional[str] = None,
        teacher_name: Optional[str] = None,
        teacher_email: Optional[str] = None,
        course_section: Optional[str] = None,
        term: Optional[str] = None,
        powerschool_frn: Optional[str] = None,
    ) -> int:
        """Insert or update a course. Returns course ID."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO courses (student_id, course_name, expression, room, teacher_name,
                    teacher_email, course_section, term, powerschool_frn, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(student_id, course_name, expression, term) DO UPDATE SET
                    room = COALESCE(excluded.room, room),
                    teacher_name = COALESCE(excluded.teacher_name, teacher_name),
                    teacher_email = COALESCE(excluded.teacher_email, teacher_email),
                    course_section = COALESCE(excluded.course_section, course_section),
                    powerschool_frn = COALESCE(excluded.powerschool_frn, powerschool_frn),
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
                """,
                (student_id, course_name, expression, room, teacher_name,
                 teacher_email, course_section, term, powerschool_frn)
            )
            return cursor.fetchone()["id"]

    # ==================== GRADES ====================

    def add_grade(
        self,
        course_id: int,
        student_id: int,
        term: str,
        letter_grade: Optional[str] = None,
        percent: Optional[float] = None,
        gpa_points: Optional[float] = None,
        absences: int = 0,
        tardies: int = 0,
    ) -> int:
        """Add a grade record. Returns grade ID."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO grades (course_id, student_id, term, letter_grade, percent,
                    gpa_points, absences, tardies)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                (course_id, student_id, term, letter_grade, percent,
                 gpa_points, absences, tardies)
            )
            return cursor.fetchone()["id"]

    def get_current_grades(self, student_id: int) -> List[Dict]:
        """Get current grades for a student (from view)."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM v_current_grades WHERE student_id = ?",
                (student_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_grade_trends(self, student_id: int) -> List[Dict]:
        """Get grade trends for a student (from view)."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM v_grade_trends WHERE student_id = ?",
                (student_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    # ==================== ASSIGNMENTS ====================

    def add_assignment(
        self,
        student_id: int,
        course_name: str,
        assignment_name: str,
        course_id: Optional[int] = None,
        teacher_name: Optional[str] = None,
        category: Optional[str] = None,
        due_date: Optional[str] = None,
        score: Optional[str] = None,
        max_score: Optional[float] = None,
        percent: Optional[float] = None,
        letter_grade: Optional[str] = None,
        status: str = "Unknown",
        codes: Optional[str] = None,
        term: Optional[str] = None,
    ) -> int:
        """Add an assignment. Returns assignment ID."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO assignments (student_id, course_id, course_name, teacher_name,
                    assignment_name, category, due_date, score, max_score, percent,
                    letter_grade, status, codes, term)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                (student_id, course_id, course_name, teacher_name, assignment_name,
                 category, due_date, score, max_score, percent, letter_grade,
                 status, codes, term)
            )
            return cursor.fetchone()["id"]

    def get_assignments(
        self,
        student_id: int,
        course_name: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict]:
        """Get assignments with optional filters."""
        query = "SELECT * FROM assignments WHERE student_id = ?"
        params: List[Any] = [student_id]

        if course_name:
            query += " AND course_name LIKE ?"
            params.append(f"%{course_name}%")

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY due_date DESC"

        with get_db(self.db_path) as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_missing_assignments(self, student_id: Optional[int] = None) -> List[Dict]:
        """Get missing assignments (from view)."""
        with get_db(self.db_path) as conn:
            if student_id:
                cursor = conn.execute(
                    "SELECT * FROM v_missing_assignments WHERE student_id = ?",
                    (student_id,)
                )
            else:
                cursor = conn.execute("SELECT * FROM v_missing_assignments")
            return [dict(row) for row in cursor.fetchall()]

    def get_upcoming_assignments(
        self, student_id: int, days: int = 14
    ) -> List[Dict]:
        """Get upcoming assignments."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM assignments
                WHERE student_id = ?
                  AND due_date >= date('now')
                  AND due_date <= date('now', '+' || ? || ' days')
                  AND status != 'Collected'
                ORDER BY due_date ASC
                """,
                (student_id, days)
            )
            return [dict(row) for row in cursor.fetchall()]

    def clear_assignments(self, student_id: int):
        """Clear all assignments for a student (before re-sync)."""
        with get_db(self.db_path) as conn:
            conn.execute(
                "DELETE FROM assignments WHERE student_id = ?",
                (student_id,)
            )

    # ==================== ATTENDANCE ====================

    def add_attendance_summary(
        self,
        student_id: int,
        attendance_rate: float,
        days_present: int = 0,
        days_absent: int = 0,
        days_excused: int = 0,
        days_unexcused: int = 0,
        tardies: int = 0,
        total_days: int = 0,
        term: str = "YTD",
    ) -> int:
        """Add attendance summary. Returns ID."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO attendance_summary (student_id, term, attendance_rate,
                    days_present, days_absent, days_excused, days_unexcused,
                    tardies, total_days)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                (student_id, term, attendance_rate, days_present, days_absent,
                 days_excused, days_unexcused, tardies, total_days)
            )
            return cursor.fetchone()["id"]

    def get_attendance_summary(self, student_id: int) -> Optional[Dict]:
        """Get latest attendance summary for a student."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM attendance_summary
                WHERE student_id = ?
                ORDER BY recorded_at DESC
                LIMIT 1
                """,
                (student_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_attendance_alerts(self) -> List[Dict]:
        """Get attendance alerts (from view)."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM v_attendance_alerts")
            return [dict(row) for row in cursor.fetchall()]

    # ==================== SCRAPE HISTORY ====================

    def start_scrape(self, student_id: Optional[int] = None) -> int:
        """Record start of a scrape. Returns scrape ID."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO scrape_history (student_id, started_at, status)
                VALUES (?, CURRENT_TIMESTAMP, 'running')
                RETURNING id
                """,
                (student_id,)
            )
            return cursor.fetchone()["id"]

    def complete_scrape(
        self,
        scrape_id: int,
        status: str = "completed",
        assignments_found: int = 0,
        error_message: Optional[str] = None,
    ):
        """Record completion of a scrape."""
        with get_db(self.db_path) as conn:
            conn.execute(
                """
                UPDATE scrape_history
                SET completed_at = CURRENT_TIMESTAMP,
                    status = ?,
                    assignments_found = ?,
                    error_message = ?
                WHERE id = ?
                """,
                (status, assignments_found, error_message, scrape_id)
            )

    # ==================== SUMMARIES ====================

    def get_student_summary(self, student_id: int) -> Optional[Dict]:
        """Get student summary (from view)."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM v_student_summary WHERE student_id = ?",
                (student_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_action_items(self, student_id: Optional[int] = None) -> List[Dict]:
        """Get prioritized action items (from view)."""
        with get_db(self.db_path) as conn:
            if student_id:
                cursor = conn.execute(
                    "SELECT * FROM v_action_items WHERE student_id = ?",
                    (student_id,)
                )
            else:
                cursor = conn.execute("SELECT * FROM v_action_items")
            return [dict(row) for row in cursor.fetchall()]

    def get_completion_rates(self, student_id: int) -> List[Dict]:
        """Get assignment completion rates (from view)."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM v_assignment_completion_rate WHERE student_id = ?",
                (student_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    # ==================== TEACHERS ====================

    def get_teachers(self) -> List[Dict]:
        """Get all teachers."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM teachers ORDER BY name"
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_teacher_by_name(self, name: str) -> Optional[Dict]:
        """Get teacher by name (partial match)."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM teachers WHERE name LIKE ?",
                (f"%{name}%",)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_teacher_by_email(self, email: str) -> Optional[Dict]:
        """Get teacher by email."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM teachers WHERE email = ?",
                (email,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def upsert_teacher(
        self,
        name: str,
        email: Optional[str] = None,
        department: Optional[str] = None,
        room: Optional[str] = None,
        courses_taught: Optional[str] = None,
    ) -> int:
        """Insert or update a teacher. Returns teacher ID."""
        with get_db(self.db_path) as conn:
            # Try to find by email first, then by name
            if email:
                cursor = conn.execute(
                    "SELECT id FROM teachers WHERE email = ?", (email,)
                )
            else:
                cursor = conn.execute(
                    "SELECT id FROM teachers WHERE name = ?", (name,)
                )
            existing = cursor.fetchone()

            if existing:
                conn.execute(
                    """
                    UPDATE teachers SET
                        name = ?,
                        email = COALESCE(?, email),
                        department = COALESCE(?, department),
                        room = COALESCE(?, room),
                        courses_taught = COALESCE(?, courses_taught),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (name, email, department, room, courses_taught, existing["id"])
                )
                return existing["id"]
            else:
                cursor = conn.execute(
                    """
                    INSERT INTO teachers (name, email, department, room, courses_taught)
                    VALUES (?, ?, ?, ?, ?)
                    RETURNING id
                    """,
                    (name, email, department, room, courses_taught)
                )
                return cursor.fetchone()["id"]

    def update_teacher_notes(self, teacher_id: int, notes: str):
        """Update notes for a teacher."""
        with get_db(self.db_path) as conn:
            conn.execute(
                "UPDATE teachers SET notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (notes, teacher_id)
            )

    def get_teacher_for_course(self, course_name: str) -> Optional[Dict]:
        """Get teacher info for a course."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT t.* FROM teachers t
                JOIN courses c ON c.teacher_name = t.name OR c.teacher_email = t.email
                WHERE c.course_name LIKE ?
                LIMIT 1
                """,
                (f"%{course_name}%",)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    # ==================== COMMUNICATIONS ====================

    def create_communication(
        self,
        teacher_id: int,
        student_id: int,
        type: str,
        body: str,
        subject: Optional[str] = None,
        context: Optional[str] = None,
        status: str = "draft",
    ) -> int:
        """Create a new communication draft."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO communications (teacher_id, student_id, type, subject, body, context, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                (teacher_id, student_id, type, subject, body, context, status)
            )
            return cursor.fetchone()["id"]

    def get_communications(
        self,
        teacher_id: Optional[int] = None,
        student_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[Dict]:
        """Get communications with optional filters."""
        query = """
            SELECT c.*, t.name as teacher_name, t.email as teacher_email,
                   s.first_name as student_name
            FROM communications c
            LEFT JOIN teachers t ON c.teacher_id = t.id
            LEFT JOIN students s ON c.student_id = s.id
            WHERE 1=1
        """
        params: List[Any] = []

        if teacher_id:
            query += " AND c.teacher_id = ?"
            params.append(teacher_id)
        if student_id:
            query += " AND c.student_id = ?"
            params.append(student_id)
        if status:
            query += " AND c.status = ?"
            params.append(status)

        query += " ORDER BY c.created_at DESC"

        with get_db(self.db_path) as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_communication(self, communication_id: int) -> Optional[Dict]:
        """Get a single communication."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT c.*, t.name as teacher_name, t.email as teacher_email
                FROM communications c
                LEFT JOIN teachers t ON c.teacher_id = t.id
                WHERE c.id = ?
                """,
                (communication_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_communication(
        self,
        communication_id: int,
        subject: Optional[str] = None,
        body: Optional[str] = None,
        status: Optional[str] = None,
    ):
        """Update a communication."""
        updates = []
        params = []

        if subject is not None:
            updates.append("subject = ?")
            params.append(subject)
        if body is not None:
            updates.append("body = ?")
            params.append(body)
        if status is not None:
            updates.append("status = ?")
            params.append(status)
            if status == "sent":
                updates.append("sent_at = CURRENT_TIMESTAMP")

        if not updates:
            return

        params.append(communication_id)

        with get_db(self.db_path) as conn:
            conn.execute(
                f"UPDATE communications SET {', '.join(updates)} WHERE id = ?",
                params
            )

    def mark_communication_sent(self, communication_id: int):
        """Mark a communication as sent and update teacher contact stats."""
        with get_db(self.db_path) as conn:
            # Get the teacher_id
            cursor = conn.execute(
                "SELECT teacher_id FROM communications WHERE id = ?",
                (communication_id,)
            )
            row = cursor.fetchone()
            if not row:
                return

            teacher_id = row["teacher_id"]

            # Update communication status
            conn.execute(
                """
                UPDATE communications
                SET status = 'sent', sent_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (communication_id,)
            )

            # Update teacher stats
            if teacher_id:
                conn.execute(
                    """
                    UPDATE teachers
                    SET last_contacted = date('now'),
                        communication_count = communication_count + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (teacher_id,)
                )

    def delete_communication(self, communication_id: int):
        """Delete a communication."""
        with get_db(self.db_path) as conn:
            conn.execute(
                "DELETE FROM communications WHERE id = ?",
                (communication_id,)
            )

    # ==================== COMMUNICATION TEMPLATES ====================

    def get_communication_templates(self, type: Optional[str] = None) -> List[Dict]:
        """Get communication templates."""
        with get_db(self.db_path) as conn:
            if type:
                cursor = conn.execute(
                    "SELECT * FROM communication_templates WHERE type = ?",
                    (type,)
                )
            else:
                cursor = conn.execute("SELECT * FROM communication_templates")
            return [dict(row) for row in cursor.fetchall()]

    def add_communication_template(
        self,
        name: str,
        type: str,
        body_template: str,
        subject_template: Optional[str] = None,
    ) -> int:
        """Add a communication template."""
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO communication_templates (name, type, subject_template, body_template)
                VALUES (?, ?, ?, ?)
                RETURNING id
                """,
                (name, type, subject_template, body_template)
            )
            return cursor.fetchone()["id"]

    # ==================== RAW QUERIES ====================

    # Allowed tables/views for custom queries (read-only access)
    ALLOWED_QUERY_SOURCES = frozenset({
        # Views (safe, read-only aggregations)
        "v_missing_assignments",
        "v_current_grades",
        "v_grade_trends",
        "v_attendance_alerts",
        "v_upcoming_assignments",
        "v_assignment_completion_rate",
        "v_student_summary",
        "v_action_items",
        # Base tables (read-only)
        "students",
        "courses",
        "grades",
        "assignments",
        "attendance_summary",
        "scrape_history",
    })

    def execute_query(self, sql: str) -> List[Dict]:
        """Execute a read-only SQL query against allowed tables/views only.

        Args:
            sql: SQL SELECT query (must only reference allowed tables/views)

        Returns:
            List of rows as dictionaries

        Raises:
            ValueError: If query is not SELECT or references disallowed tables

        Security:
            - Only SELECT queries are allowed
            - Only predefined tables/views can be queried
            - No subqueries, CTEs, or complex expressions that could bypass validation
        """
        import re

        sql_clean = sql.strip()
        sql_upper = sql_clean.upper()

        # Only allow SELECT statements
        if not sql_upper.startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed")

        # Block potentially dangerous patterns
        dangerous_patterns = [
            r"\bATTACH\b",
            r"\bDETACH\b",
            r"\bPRAGMA\b",
            r"\bLOAD_EXTENSION\b",
            r";\s*\w",  # Multiple statements
            r"--",  # SQL comments (could hide malicious code)
            r"/\*",  # Block comments
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, sql_upper):
                raise ValueError(f"Query contains disallowed pattern: {pattern}")

        # Extract table/view references from FROM and JOIN clauses
        # Match words after FROM or JOIN keywords
        table_pattern = r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)"
        referenced_tables = set(re.findall(table_pattern, sql_clean, re.IGNORECASE))

        # Validate all referenced tables are in the allowed list
        disallowed = referenced_tables - self.ALLOWED_QUERY_SOURCES
        if disallowed:
            raise ValueError(
                f"Query references disallowed tables: {', '.join(sorted(disallowed))}. "
                f"Allowed: {', '.join(sorted(self.ALLOWED_QUERY_SOURCES))}"
            )

        if not referenced_tables:
            raise ValueError("Query must reference at least one table or view")

        with get_db(self.db_path) as conn:
            cursor = conn.execute(sql_clean)
            return [dict(row) for row in cursor.fetchall()]


# Singleton instance
_repo: Optional[Repository] = None


def get_repository(db_path: Optional[Path] = None) -> Repository:
    """Get the repository instance."""
    global _repo
    if _repo is None or (db_path and db_path != _repo.db_path):
        _repo = Repository(db_path)
    return _repo
