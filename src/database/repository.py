"""Repository for database CRUD operations."""

import uuid
from datetime import datetime
from typing import Any

from .connection import Database
from .models import (
    Assignment,
    AttendanceRecord,
    AttendanceSummary,
    Course,
    Grade,
    ScrapeHistory,
    Student,
    TeacherComment,
)


def generate_id() -> str:
    """Generate a unique ID."""
    return str(uuid.uuid4())


class Repository:
    """Repository for all database operations."""

    def __init__(self, db: Database):
        self.db = db

    # ==================== STUDENTS ====================

    async def insert_student(self, student: Student) -> str:
        """Insert a new student."""
        await self.db.execute(
            """
            INSERT INTO students (student_id, first_name, last_name, grade_level, school_name, district_code)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                student.student_id,
                student.first_name,
                student.last_name,
                student.grade_level,
                student.school_name,
                student.district_code,
            ),
        )
        await self.db.commit()
        return student.student_id

    async def get_student(self, student_id: str) -> dict[str, Any] | None:
        """Get a student by ID."""
        return await self.db.fetch_one(
            "SELECT * FROM students WHERE student_id = ?", (student_id,)
        )

    async def get_student_by_name(self, name: str) -> dict[str, Any] | None:
        """Get a student by name (partial match)."""
        return await self.db.fetch_one(
            """
            SELECT * FROM students 
            WHERE first_name || ' ' || last_name LIKE ? 
            OR first_name LIKE ? 
            OR last_name LIKE ?
            LIMIT 1
            """,
            (f"%{name}%", f"%{name}%", f"%{name}%"),
        )

    async def list_students(self) -> list[dict[str, Any]]:
        """List all students."""
        return await self.db.fetch_all(
            "SELECT * FROM students ORDER BY last_name, first_name"
        )

    async def get_student_summary(self, student_id: str) -> dict[str, Any] | None:
        """Get student summary from view."""
        return await self.db.fetch_one(
            "SELECT * FROM v_student_summary WHERE student_id = ?", (student_id,)
        )

    # ==================== COURSES ====================

    async def insert_course(self, course: Course) -> str:
        """Insert a new course."""
        await self.db.execute(
            """
            INSERT INTO courses (course_id, course_section, course_name, expression, room, 
                               term, teacher_name, teacher_email, enroll_date, leave_date, student_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                course.course_id,
                course.course_section,
                course.course_name,
                course.expression,
                course.room,
                course.term,
                course.teacher_name,
                course.teacher_email,
                course.enroll_date.isoformat() if course.enroll_date else None,
                course.leave_date.isoformat() if course.leave_date else None,
                course.student_id,
            ),
        )
        await self.db.commit()
        return course.course_id

    async def get_course(self, course_id: str) -> dict[str, Any] | None:
        """Get a course by ID."""
        return await self.db.fetch_one(
            "SELECT * FROM courses WHERE course_id = ?", (course_id,)
        )

    async def get_courses_for_student(self, student_id: str) -> list[dict[str, Any]]:
        """Get all courses for a student."""
        return await self.db.fetch_all(
            "SELECT * FROM courses WHERE student_id = ? ORDER BY course_name",
            (student_id,),
        )

    async def get_course_by_name(
        self, student_id: str, course_name: str
    ) -> dict[str, Any] | None:
        """Get a course by name for a student."""
        return await self.db.fetch_one(
            """
            SELECT * FROM courses 
            WHERE student_id = ? AND course_name LIKE ?
            LIMIT 1
            """,
            (student_id, f"%{course_name}%"),
        )

    # ==================== GRADES ====================

    async def insert_grade(self, grade: Grade) -> str:
        """Insert a new grade."""
        await self.db.execute(
            """
            INSERT INTO grades (grade_id, course_id, student_id, term, letter_grade, percent, gpa_points)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                grade.grade_id,
                grade.course_id,
                grade.student_id,
                grade.term,
                grade.letter_grade,
                grade.percent,
                grade.gpa_points,
            ),
        )
        await self.db.commit()
        return grade.grade_id

    async def get_current_grades(self, student_id: str) -> list[dict[str, Any]]:
        """Get current grades for a student."""
        return await self.db.fetch_all(
            "SELECT * FROM v_current_grades WHERE student_id = ?", (student_id,)
        )

    async def get_grade_trends(self, student_id: str) -> list[dict[str, Any]]:
        """Get grade trends for a student."""
        return await self.db.fetch_all(
            "SELECT * FROM v_grade_trends WHERE student_id = ?", (student_id,)
        )

    async def get_grade_history(
        self, student_id: str, course_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Get grade history for a student, optionally filtered by course."""
        if course_id:
            return await self.db.fetch_all(
                """
                SELECT g.*, c.course_name 
                FROM grades g 
                JOIN courses c ON g.course_id = c.course_id
                WHERE g.student_id = ? AND g.course_id = ?
                ORDER BY g.term, g.recorded_at
                """,
                (student_id, course_id),
            )
        return await self.db.fetch_all(
            """
            SELECT g.*, c.course_name 
            FROM grades g 
            JOIN courses c ON g.course_id = c.course_id
            WHERE g.student_id = ?
            ORDER BY c.course_name, g.term, g.recorded_at
            """,
            (student_id,),
        )

    async def calculate_gpa(
        self, student_id: str, term: str | None = None
    ) -> dict[str, Any]:
        """Calculate GPA for a student."""
        if term:
            result = await self.db.fetch_one(
                """
                SELECT 
                    AVG(gpa_points) as gpa,
                    COUNT(*) as course_count,
                    ? as term
                FROM grades 
                WHERE student_id = ? AND term = ? AND gpa_points IS NOT NULL
                """,
                (term, student_id, term),
            )
        else:
            result = await self.db.fetch_one(
                """
                SELECT 
                    AVG(gpa_points) as gpa,
                    COUNT(*) as course_count,
                    'Overall' as term
                FROM grades 
                WHERE student_id = ? AND gpa_points IS NOT NULL
                """,
                (student_id,),
            )
        return result or {"gpa": None, "course_count": 0, "term": term or "Overall"}

    # ==================== ASSIGNMENTS ====================

    async def insert_assignment(self, assignment: Assignment) -> str:
        """Insert a new assignment."""
        await self.db.execute(
            """
            INSERT INTO assignments (assignment_id, course_id, student_id, assignment_name, 
                                   category, due_date, score, max_score, percent, letter_grade, 
                                   status, has_comment, has_description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                assignment.assignment_id,
                assignment.course_id,
                assignment.student_id,
                assignment.assignment_name,
                assignment.category,
                assignment.due_date.isoformat() if assignment.due_date else None,
                assignment.score,
                assignment.max_score,
                assignment.percent,
                assignment.letter_grade,
                assignment.status,
                1 if assignment.has_comment else 0,
                1 if assignment.has_description else 0,
            ),
        )
        await self.db.commit()
        return assignment.assignment_id

    async def get_missing_assignments(
        self, student_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Get missing assignments, optionally filtered by student."""
        if student_id:
            return await self.db.fetch_all(
                "SELECT * FROM v_missing_assignments WHERE student_id = ?",
                (student_id,),
            )
        return await self.db.fetch_all("SELECT * FROM v_missing_assignments")

    async def get_upcoming_assignments(
        self, student_id: str, days: int = 14
    ) -> list[dict[str, Any]]:
        """Get upcoming assignments for a student."""
        return await self.db.fetch_all(
            """
            SELECT * FROM v_upcoming_assignments 
            WHERE student_id = ? AND days_until_due <= ?
            """,
            (student_id, days),
        )

    async def get_assignment_completion_rates(
        self, student_id: str
    ) -> list[dict[str, Any]]:
        """Get assignment completion rates by course."""
        return await self.db.fetch_all(
            "SELECT * FROM v_assignment_completion WHERE student_id = ?", (student_id,)
        )

    async def get_recent_scores(
        self, student_id: str, days: int = 7
    ) -> list[dict[str, Any]]:
        """Get recently scored assignments."""
        return await self.db.fetch_all(
            """
            SELECT * FROM assignments a
            JOIN courses c ON a.course_id = c.course_id
            WHERE a.student_id = ? 
            AND a.recorded_at >= datetime('now', ?)
            AND a.score IS NOT NULL
            ORDER BY a.recorded_at DESC
            """,
            (student_id, f"-{days} days"),
        )

    # ==================== ATTENDANCE ====================

    async def insert_attendance_record(self, record: AttendanceRecord) -> str:
        """Insert an attendance record."""
        await self.db.execute(
            """
            INSERT INTO attendance_records (attendance_id, student_id, course_id, date, 
                                           period, status, code)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.attendance_id,
                record.student_id,
                record.course_id,
                record.date.isoformat(),
                record.period,
                record.status,
                record.code,
            ),
        )
        await self.db.commit()
        return record.attendance_id

    async def insert_attendance_summary(self, summary: AttendanceSummary) -> str:
        """Insert an attendance summary."""
        await self.db.execute(
            """
            INSERT INTO attendance_summary (summary_id, student_id, term, days_enrolled,
                                           days_present, days_absent, days_absent_excused,
                                           days_absent_unexcused, tardies, tardies_excused,
                                           tardies_unexcused, attendance_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                summary.summary_id,
                summary.student_id,
                summary.term,
                summary.days_enrolled,
                summary.days_present,
                summary.days_absent,
                summary.days_absent_excused,
                summary.days_absent_unexcused,
                summary.tardies,
                summary.tardies_excused,
                summary.tardies_unexcused,
                summary.attendance_rate,
            ),
        )
        await self.db.commit()
        return summary.summary_id

    async def get_attendance_summary(self, student_id: str) -> dict[str, Any] | None:
        """Get attendance summary for a student."""
        return await self.db.fetch_one(
            """
            SELECT * FROM attendance_summary 
            WHERE student_id = ? AND term = 'YTD'
            """,
            (student_id,),
        )

    async def get_attendance_alerts(self) -> list[dict[str, Any]]:
        """Get all attendance alerts."""
        return await self.db.fetch_all("SELECT * FROM v_attendance_alerts")

    # ==================== TEACHER COMMENTS ====================

    async def insert_teacher_comment(self, comment: TeacherComment) -> str:
        """Insert a teacher comment."""
        await self.db.execute(
            """
            INSERT INTO teacher_comments (comment_id, student_id, course_id, teacher_name, 
                                         term, comment_text)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                comment.comment_id,
                comment.student_id,
                comment.course_id,
                comment.teacher_name,
                comment.term,
                comment.comment_text,
            ),
        )
        await self.db.commit()
        return comment.comment_id

    async def get_teacher_comments(
        self, student_id: str, term: str | None = None
    ) -> list[dict[str, Any]]:
        """Get teacher comments for a student."""
        if term:
            return await self.db.fetch_all(
                """
                SELECT tc.*, c.course_name 
                FROM teacher_comments tc
                JOIN courses c ON tc.course_id = c.course_id
                WHERE tc.student_id = ? AND tc.term = ?
                ORDER BY tc.recorded_at DESC
                """,
                (student_id, term),
            )
        return await self.db.fetch_all(
            """
            SELECT tc.*, c.course_name 
            FROM teacher_comments tc
            JOIN courses c ON tc.course_id = c.course_id
            WHERE tc.student_id = ?
            ORDER BY tc.recorded_at DESC
            """,
            (student_id,),
        )

    # ==================== SCRAPE HISTORY ====================

    async def insert_scrape_history(self, history: ScrapeHistory) -> str:
        """Insert a scrape history record."""
        await self.db.execute(
            """
            INSERT INTO scrape_history (scrape_id, student_id, started_at, completed_at, 
                                       status, pages_scraped, errors)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                history.scrape_id,
                history.student_id,
                history.started_at.isoformat(),
                history.completed_at.isoformat() if history.completed_at else None,
                history.status,
                history.pages_scraped,
                history.errors,
            ),
        )
        await self.db.commit()
        return history.scrape_id

    async def get_last_sync_time(self, student_id: str | None = None) -> dict[str, Any]:
        """Get the last successful sync time."""
        if student_id:
            result = await self.db.fetch_one(
                """
                SELECT completed_at, student_id 
                FROM scrape_history 
                WHERE student_id = ? AND status = 'success'
                ORDER BY completed_at DESC LIMIT 1
                """,
                (student_id,),
            )
        else:
            result = await self.db.fetch_one(
                """
                SELECT completed_at, student_id 
                FROM scrape_history 
                WHERE status = 'success'
                ORDER BY completed_at DESC LIMIT 1
                """
            )
        return result or {"completed_at": None, "student_id": None}

    # ==================== CUSTOM QUERIES ====================

    async def run_custom_query(self, sql: str) -> list[dict[str, Any]]:
        """Run a custom read-only query."""
        # Basic safety check - only allow SELECT statements
        sql_lower = sql.strip().lower()
        if not sql_lower.startswith("select"):
            raise ValueError("Only SELECT queries are allowed")

        # Block dangerous operations
        forbidden = ["insert", "update", "delete", "drop", "alter", "create", "pragma"]
        for word in forbidden:
            if word in sql_lower:
                raise ValueError(f"Query contains forbidden operation: {word}")

        return await self.db.fetch_all(sql)
