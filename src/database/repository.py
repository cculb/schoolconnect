"""Data access layer for PowerSchool Portal database.

This module provides the Repository class which handles all database
operations for the PowerSchool Portal application. It uses parameterized
queries to prevent SQL injection and returns data as dictionaries.

Example:
    from src.database.repository import Repository

    repo = Repository()
    students = repo.get_students()
    for student in students:
        grades = repo.get_current_grades(student["id"])
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from .connection import DB_PATH, get_db


class Repository:
    """Repository pattern implementation for PowerSchool database operations.

    Provides CRUD operations for students, courses, grades, assignments,
    attendance, teachers, and communications. All methods return data
    as dictionaries rather than ORM objects.

    Attributes:
        db_path: Path to the SQLite database file.

    Example:
        repo = Repository()
        student = repo.get_student_by_name("John")
        if student:
            missing = repo.get_missing_assignments(student["id"])
    """

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize repository with optional custom database path.

        Args:
            db_path: Path to SQLite database. Uses default if not provided.
        """
        self.db_path = db_path or DB_PATH

    # ==================== STUDENTS ====================

    def get_students(self) -> List[Dict]:
        """Get all students ordered by first name.

        Returns:
            List of student dictionaries with keys: id, powerschool_id,
            first_name, last_name, grade_level, school_name, updated_at.
        """
        with get_db(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM students ORDER BY first_name")
            return [dict(row) for row in cursor.fetchall()]

    def get_student_by_name(self, name: str) -> Optional[Dict]:
        """Find a student by partial name match.

        Searches both first name and full name (first + last).

        Args:
            name: Partial or full name to search for.

        Returns:
            Student dictionary if found, None otherwise.
        """
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM students WHERE first_name LIKE ? OR "
                "(first_name || ' ' || last_name) LIKE ?",
                (f"%{name}%", f"%{name}%"),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_student_by_id(self, student_id: int) -> Optional[Dict]:
        """Get a student by their database ID.

        Args:
            student_id: The database primary key ID.

        Returns:
            Student dictionary if found, None otherwise.
        """
        with get_db(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,))
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
        """Insert or update a student record.

        Uses UPSERT (INSERT ... ON CONFLICT) to create new students or
        update existing ones based on powerschool_id.

        Args:
            powerschool_id: Unique PowerSchool identifier.
            first_name: Student's first name.
            last_name: Student's last name (optional).
            grade_level: Grade level string, e.g., "9" or "12".
            school_name: Name of the school.

        Returns:
            The database ID of the inserted or updated student.
        """
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
                (powerschool_id, first_name, last_name, grade_level, school_name),
            )
            return int(cursor.fetchone()["id"])

    # ==================== COURSES ====================

    def get_courses(self, student_id: int) -> List[Dict]:
        """Get all courses for a student, ordered by course name.

        Args:
            student_id: The student's database ID.

        Returns:
            List of course dictionaries with keys: id, student_id,
            course_name, expression, room, teacher_name, teacher_email,
            course_section, term, powerschool_frn, updated_at.
        """
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM courses WHERE student_id = ? ORDER BY course_name", (student_id,)
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
        """Insert or update a course record.

        Uses UPSERT based on (student_id, course_name, expression, term)
        unique constraint.

        Args:
            student_id: The student's database ID.
            course_name: Name of the course.
            expression: Period/time expression (e.g., "1(A)" or "3(B)").
            room: Room number or name.
            teacher_name: Name of the teacher.
            teacher_email: Teacher's email address.
            course_section: Section identifier.
            term: Academic term (e.g., "Q1", "S1", "Year").
            powerschool_frn: PowerSchool FRN identifier for API access.

        Returns:
            The database ID of the inserted or updated course.
        """
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
                (
                    student_id,
                    course_name,
                    expression,
                    room,
                    teacher_name,
                    teacher_email,
                    course_section,
                    term,
                    powerschool_frn,
                ),
            )
            return int(cursor.fetchone()["id"])

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
        """Add a grade record for a student's course.

        Args:
            course_id: The course's database ID.
            student_id: The student's database ID.
            term: Academic term (e.g., "Q1", "Q2", "S1").
            letter_grade: Letter grade (e.g., "A", "B+", "C-").
            percent: Percentage grade (0.0 to 100.0).
            gpa_points: GPA points (typically 0.0 to 4.0).
            absences: Number of absences for this course.
            tardies: Number of tardies for this course.

        Returns:
            The database ID of the inserted grade record.
        """
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO grades (course_id, student_id, term, letter_grade, percent,
                    gpa_points, absences, tardies)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                (course_id, student_id, term, letter_grade, percent, gpa_points, absences, tardies),
            )
            return int(cursor.fetchone()["id"])

    def get_current_grades(self, student_id: int) -> List[Dict]:
        """Get current grades for a student from the v_current_grades view.

        Args:
            student_id: The student's database ID.

        Returns:
            List of grade dictionaries with course and grade info.
        """
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM v_current_grades WHERE student_id = ?", (student_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_grade_trends(self, student_id: int) -> List[Dict]:
        """Get grade trends for a student from the v_grade_trends view.

        Shows grade changes over time to identify improving or declining
        performance.

        Args:
            student_id: The student's database ID.

        Returns:
            List of trend dictionaries showing grade progression.
        """
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM v_grade_trends WHERE student_id = ?", (student_id,)
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
        """Add an assignment record.

        Args:
            student_id: The student's database ID.
            course_name: Name of the course.
            assignment_name: Name of the assignment.
            course_id: Optional course database ID.
            teacher_name: Teacher's name.
            category: Assignment category (e.g., "Homework", "Test").
            due_date: Due date in YYYY-MM-DD format.
            score: Raw score (may include "/" for fractions).
            max_score: Maximum possible score.
            percent: Percentage grade.
            letter_grade: Letter grade.
            status: Status string ("Missing", "Collected", "Unknown").
            codes: Additional status codes from PowerSchool.
            term: Academic term.

        Returns:
            The database ID of the inserted assignment.
        """
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO assignments (student_id, course_id, course_name, teacher_name,
                    assignment_name, category, due_date, score, max_score, percent,
                    letter_grade, status, codes, term)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                (
                    student_id,
                    course_id,
                    course_name,
                    teacher_name,
                    assignment_name,
                    category,
                    due_date,
                    score,
                    max_score,
                    percent,
                    letter_grade,
                    status,
                    codes,
                    term,
                ),
            )
            return int(cursor.fetchone()["id"])

    def get_assignments(
        self,
        student_id: int,
        course_name: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict]:
        """Get assignments with optional filters.

        Args:
            student_id: The student's database ID.
            course_name: Optional filter by course name (partial match).
            status: Optional filter by status (exact match).

        Returns:
            List of assignment dictionaries, ordered by due date descending.
        """
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
        """Get missing assignments from the v_missing_assignments view.

        Args:
            student_id: Optional filter by student ID. If None, returns
                        missing assignments for all students.

        Returns:
            List of missing assignment dictionaries.
        """
        with get_db(self.db_path) as conn:
            if student_id:
                cursor = conn.execute(
                    "SELECT * FROM v_missing_assignments WHERE student_id = ?", (student_id,)
                )
            else:
                cursor = conn.execute("SELECT * FROM v_missing_assignments")
            return [dict(row) for row in cursor.fetchall()]

    def get_upcoming_assignments(self, student_id: int, days: int = 14) -> List[Dict]:
        """Get assignments due within a specified number of days.

        Excludes assignments already marked as "Collected".

        Args:
            student_id: The student's database ID.
            days: Number of days to look ahead (default 14).

        Returns:
            List of upcoming assignment dictionaries, ordered by due date.
        """
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
                (student_id, days),
            )
            return [dict(row) for row in cursor.fetchall()]

    def clear_assignments(self, student_id: int) -> None:
        """Clear all assignments for a student.

        Typically called before re-syncing assignments from PowerSchool
        to avoid duplicates.

        Args:
            student_id: The student's database ID.
        """
        with get_db(self.db_path) as conn:
            conn.execute("DELETE FROM assignments WHERE student_id = ?", (student_id,))

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
        """Add an attendance summary record for a student.

        Args:
            student_id: The student's database ID.
            attendance_rate: Percentage attendance rate (0.0 to 100.0).
            days_present: Number of days present.
            days_absent: Total days absent.
            days_excused: Days with excused absences.
            days_unexcused: Days with unexcused absences.
            tardies: Number of tardies.
            total_days: Total school days in period.
            term: Term identifier (default "YTD" for year-to-date).

        Returns:
            The database ID of the inserted attendance record.
        """
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO attendance_summary (student_id, term, attendance_rate,
                    days_present, days_absent, days_excused, days_unexcused,
                    tardies, total_days)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                (
                    student_id,
                    term,
                    attendance_rate,
                    days_present,
                    days_absent,
                    days_excused,
                    days_unexcused,
                    tardies,
                    total_days,
                ),
            )
            return int(cursor.fetchone()["id"])

    def get_attendance_summary(self, student_id: int) -> Optional[Dict]:
        """Get the most recent attendance summary for a student.

        Args:
            student_id: The student's database ID.

        Returns:
            Attendance summary dictionary if found, None otherwise.
        """
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM attendance_summary
                WHERE student_id = ?
                ORDER BY recorded_at DESC
                LIMIT 1
                """,
                (student_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_attendance_alerts(self) -> List[Dict]:
        """Get attendance alerts from the v_attendance_alerts view.

        Returns students with attendance rates below threshold or
        excessive absences/tardies.

        Returns:
            List of alert dictionaries for students needing attention.
        """
        with get_db(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM v_attendance_alerts")
            return [dict(row) for row in cursor.fetchall()]

    # ==================== SCRAPE HISTORY ====================

    def start_scrape(self, student_id: Optional[int] = None) -> int:
        """Record the start of a scraping session.

        Creates a scrape_history record with status "running".

        Args:
            student_id: Optional student ID if scraping for specific student.

        Returns:
            The database ID of the scrape history record.
        """
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO scrape_history (student_id, started_at, status)
                VALUES (?, CURRENT_TIMESTAMP, 'running')
                RETURNING id
                """,
                (student_id,),
            )
            return int(cursor.fetchone()["id"])

    def complete_scrape(
        self,
        scrape_id: int,
        status: str = "completed",
        assignments_found: int = 0,
        error_message: Optional[str] = None,
    ) -> None:
        """Record the completion of a scraping session.

        Updates the scrape_history record with completion time and results.

        Args:
            scrape_id: The scrape history record ID from start_scrape().
            status: Final status ("completed", "failed", "partial").
            assignments_found: Number of assignments found during scrape.
            error_message: Error message if scrape failed.
        """
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
                (status, assignments_found, error_message, scrape_id),
            )

    # ==================== SUMMARIES ====================

    def get_student_summary(self, student_id: int) -> Optional[Dict]:
        """Get a comprehensive summary for a student from v_student_summary.

        Includes grade averages, missing assignments count, attendance rate,
        and other key metrics.

        Args:
            student_id: The student's database ID.

        Returns:
            Summary dictionary if found, None otherwise.
        """
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM v_student_summary WHERE student_id = ?", (student_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_action_items(self, student_id: Optional[int] = None) -> List[Dict]:
        """Get prioritized action items from v_action_items view.

        Returns items requiring attention such as missing assignments,
        low grades, and attendance issues.

        Args:
            student_id: Optional filter by student ID.

        Returns:
            List of action item dictionaries, prioritized by urgency.
        """
        with get_db(self.db_path) as conn:
            if student_id:
                cursor = conn.execute(
                    "SELECT * FROM v_action_items WHERE student_id = ?", (student_id,)
                )
            else:
                cursor = conn.execute("SELECT * FROM v_action_items")
            return [dict(row) for row in cursor.fetchall()]

    def get_completion_rates(self, student_id: int) -> List[Dict]:
        """Get assignment completion rates from v_assignment_completion_rate.

        Shows completion percentage by course to identify problem areas.

        Args:
            student_id: The student's database ID.

        Returns:
            List of completion rate dictionaries by course.
        """
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM v_assignment_completion_rate WHERE student_id = ?", (student_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    # ==================== TEACHERS ====================

    def get_teachers(self) -> List[Dict]:
        """Get all teachers, ordered by name.

        Returns:
            List of teacher dictionaries with contact info and notes.
        """
        with get_db(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM teachers ORDER BY name")
            return [dict(row) for row in cursor.fetchall()]

    def get_teacher_by_name(self, name: str) -> Optional[Dict]:
        """Find a teacher by partial name match.

        Args:
            name: Partial or full name to search for.

        Returns:
            Teacher dictionary if found, None otherwise.
        """
        with get_db(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM teachers WHERE name LIKE ?", (f"%{name}%",))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_teacher_by_email(self, email: str) -> Optional[Dict]:
        """Find a teacher by exact email match.

        Args:
            email: Teacher's email address.

        Returns:
            Teacher dictionary if found, None otherwise.
        """
        with get_db(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM teachers WHERE email = ?", (email,))
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
        """Insert or update a teacher record.

        Matches existing teachers by email first, then by name.

        Args:
            name: Teacher's full name.
            email: Email address.
            department: Department name.
            room: Room number or name.
            courses_taught: Comma-separated list of courses.

        Returns:
            The database ID of the inserted or updated teacher.
        """
        with get_db(self.db_path) as conn:
            # Try to find by email first, then by name
            if email:
                cursor = conn.execute("SELECT id FROM teachers WHERE email = ?", (email,))
            else:
                cursor = conn.execute("SELECT id FROM teachers WHERE name = ?", (name,))
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
                    (name, email, department, room, courses_taught, existing["id"]),
                )
                return int(existing["id"])
            else:
                cursor = conn.execute(
                    """
                    INSERT INTO teachers (name, email, department, room, courses_taught)
                    VALUES (?, ?, ?, ?, ?)
                    RETURNING id
                    """,
                    (name, email, department, room, courses_taught),
                )
                return int(cursor.fetchone()["id"])

    def update_teacher_notes(self, teacher_id: int, notes: str) -> None:
        """Update notes for a teacher.

        Args:
            teacher_id: The teacher's database ID.
            notes: Notes text to set.
        """
        with get_db(self.db_path) as conn:
            conn.execute(
                "UPDATE teachers SET notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (notes, teacher_id),
            )

    def get_teacher_for_course(self, course_name: str) -> Optional[Dict]:
        """Find the teacher for a given course.

        Joins teachers with courses by name or email.

        Args:
            course_name: Partial or full course name.

        Returns:
            Teacher dictionary if found, None otherwise.
        """
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT t.* FROM teachers t
                JOIN courses c ON c.teacher_name = t.name OR c.teacher_email = t.email
                WHERE c.course_name LIKE ?
                LIMIT 1
                """,
                (f"%{course_name}%",),
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
        """Create a new communication draft.

        Args:
            teacher_id: The teacher's database ID.
            student_id: The student's database ID.
            type: Communication type ("email", "note", etc.).
            body: Message body text.
            subject: Optional email subject line.
            context: Optional context about why this communication.
            status: Status ("draft", "sent", "archived").

        Returns:
            The database ID of the created communication.
        """
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO communications (teacher_id, student_id, type, subject, body, context, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                (teacher_id, student_id, type, subject, body, context, status),
            )
            return int(cursor.fetchone()["id"])

    def get_communications(
        self,
        teacher_id: Optional[int] = None,
        student_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[Dict]:
        """Get communications with optional filters.

        Args:
            teacher_id: Optional filter by teacher.
            student_id: Optional filter by student.
            status: Optional filter by status.

        Returns:
            List of communication dictionaries with teacher/student info.
        """
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
        """Get a single communication by ID.

        Args:
            communication_id: The communication's database ID.

        Returns:
            Communication dictionary with teacher info, or None.
        """
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT c.*, t.name as teacher_name, t.email as teacher_email
                FROM communications c
                LEFT JOIN teachers t ON c.teacher_id = t.id
                WHERE c.id = ?
                """,
                (communication_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_communication(
        self,
        communication_id: int,
        subject: Optional[str] = None,
        body: Optional[str] = None,
        status: Optional[str] = None,
    ) -> None:
        """Update a communication's subject, body, or status.

        Args:
            communication_id: The communication's database ID.
            subject: New subject line (optional).
            body: New body text (optional).
            status: New status (optional). If "sent", also sets sent_at.
        """
        updates: list[str] = []
        params: list[str | int] = []

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
            conn.execute(f"UPDATE communications SET {', '.join(updates)} WHERE id = ?", params)

    def mark_communication_sent(self, communication_id: int) -> None:
        """Mark a communication as sent and update teacher contact stats.

        Updates the communication status to "sent" and increments the
        teacher's communication_count and last_contacted date.

        Args:
            communication_id: The communication's database ID.
        """
        with get_db(self.db_path) as conn:
            # Get the teacher_id
            cursor = conn.execute(
                "SELECT teacher_id FROM communications WHERE id = ?", (communication_id,)
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
                (communication_id,),
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
                    (teacher_id,),
                )

    def delete_communication(self, communication_id: int) -> None:
        """Delete a communication record.

        Args:
            communication_id: The communication's database ID.
        """
        with get_db(self.db_path) as conn:
            conn.execute("DELETE FROM communications WHERE id = ?", (communication_id,))

    # ==================== COMMUNICATION TEMPLATES ====================

    def get_communication_templates(self, type: Optional[str] = None) -> List[Dict]:
        """Get communication templates.

        Args:
            type: Optional filter by template type (e.g., "email").

        Returns:
            List of template dictionaries.
        """
        with get_db(self.db_path) as conn:
            if type:
                cursor = conn.execute(
                    "SELECT * FROM communication_templates WHERE type = ?", (type,)
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
        """Add a communication template.

        Args:
            name: Template name for identification.
            type: Template type (e.g., "email", "note").
            body_template: Message body with optional placeholders.
            subject_template: Optional subject line template.

        Returns:
            The database ID of the created template.
        """
        with get_db(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO communication_templates (name, type, subject_template, body_template)
                VALUES (?, ?, ?, ?)
                RETURNING id
                """,
                (name, type, subject_template, body_template),
            )
            return int(cursor.fetchone()["id"])

    # ==================== RAW QUERIES ====================

    # Allowed tables/views for custom queries (read-only access)
    ALLOWED_QUERY_SOURCES = frozenset(
        {
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
        }
    )

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
    """Get or create the singleton Repository instance.

    Args:
        db_path: Optional database path. If provided and different from
                 the current instance, creates a new Repository.

    Returns:
        The Repository singleton instance.
    """
    global _repo
    if _repo is None or (db_path and db_path != _repo.db_path):
        _repo = Repository(db_path)
    return _repo
