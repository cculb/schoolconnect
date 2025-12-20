"""Pydantic models for PowerSchool data."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class Student(BaseModel):
    """Student model."""

    student_id: str
    first_name: str
    last_name: str
    grade_level: int
    school_name: str
    district_code: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Course(BaseModel):
    """Course model."""

    course_id: str
    course_section: Optional[str] = None
    course_name: str
    expression: Optional[str] = None  # Period/block e.g., "1/6(A-B)"
    room: Optional[str] = None
    term: Optional[str] = None
    teacher_name: Optional[str] = None
    teacher_email: Optional[str] = None
    enroll_date: Optional[date] = None
    leave_date: Optional[date] = None
    student_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Grade(BaseModel):
    """Grade model."""

    grade_id: str
    course_id: str
    student_id: str
    term: str
    letter_grade: Optional[str] = None
    percent: Optional[float] = None
    gpa_points: Optional[float] = None
    recorded_at: Optional[datetime] = None


class Assignment(BaseModel):
    """Assignment model."""

    assignment_id: str
    course_id: str
    student_id: str
    assignment_name: str
    category: Optional[str] = None
    due_date: Optional[date] = None
    score: Optional[float] = None
    max_score: Optional[float] = None
    percent: Optional[float] = None
    letter_grade: Optional[str] = None
    status: Optional[str] = None  # "Collected", "Missing", "Late", "Exempt"
    has_comment: bool = False
    has_description: bool = False
    recorded_at: Optional[datetime] = None


class AttendanceRecord(BaseModel):
    """Individual attendance record model."""

    attendance_id: str
    student_id: str
    course_id: Optional[str] = None
    date: date
    period: Optional[str] = None
    status: str
    code: Optional[str] = None
    recorded_at: Optional[datetime] = None


class AttendanceSummary(BaseModel):
    """Attendance summary model."""

    summary_id: str
    student_id: str
    term: str
    days_enrolled: Optional[int] = None
    days_present: Optional[int] = None
    days_absent: Optional[int] = None
    days_absent_excused: Optional[int] = None
    days_absent_unexcused: Optional[int] = None
    tardies: Optional[int] = None
    tardies_excused: Optional[int] = None
    tardies_unexcused: Optional[int] = None
    attendance_rate: Optional[float] = None
    recorded_at: Optional[datetime] = None


class TeacherComment(BaseModel):
    """Teacher comment model."""

    comment_id: str
    student_id: str
    course_id: str
    teacher_name: Optional[str] = None
    term: Optional[str] = None
    comment_text: str
    recorded_at: Optional[datetime] = None


class ScrapeHistory(BaseModel):
    """Scrape history model."""

    scrape_id: str
    student_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str  # "success", "partial", "failed"
    pages_scraped: int = 0
    errors: Optional[str] = None  # JSON array of error messages


# Response models for MCP tools
class StudentSummary(BaseModel):
    """Student summary response model."""

    student_id: str
    student_name: str
    grade_level: int
    school_name: str
    course_count: int
    missing_assignments: int
    attendance_rate: Optional[float] = None
    avg_gpa: Optional[float] = None


class MissingAssignment(BaseModel):
    """Missing assignment response model."""

    student_name: str
    course_name: str
    teacher_name: Optional[str] = None
    teacher_email: Optional[str] = None
    assignment_name: str
    category: Optional[str] = None
    due_date: Optional[date] = None
    days_overdue: int = 0


class GradeInfo(BaseModel):
    """Grade info response model."""

    course_name: str
    teacher_name: Optional[str] = None
    term: str
    letter_grade: Optional[str] = None
    percent: Optional[float] = None
    gpa_points: Optional[float] = None


class AttendanceInfo(BaseModel):
    """Attendance info response model."""

    term: str
    attendance_rate: Optional[float] = None
    days_present: Optional[int] = None
    days_absent: Optional[int] = None
    days_absent_excused: Optional[int] = None
    days_absent_unexcused: Optional[int] = None
    tardies: Optional[int] = None
    alert_level: str = "Good"  # "Good", "Warning", "Critical"


class ActionItem(BaseModel):
    """Action item for parents."""

    priority: int  # 1 = highest
    category: str  # "missing_work", "attendance", "grade_drop", etc.
    title: str
    description: str
    action: str
    contact: Optional[str] = None
