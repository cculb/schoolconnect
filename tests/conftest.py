"""Pytest fixtures for PowerSchool tests."""

import asyncio
from datetime import date, datetime
from pathlib import Path

import pytest

from src.database.connection import Database
from src.database.models import Assignment, AttendanceSummary, Course, Grade, Student
from src.database.repository import Repository, generate_id


@pytest.fixture
def sample_assignments_html() -> str:
    """Sample HTML for assignments page testing."""
    return """
    <html>
    <body>
    <table class="linkDescList">
        <tr>
            <th>Teacher</th>
            <th>Course</th>
            <th>Term</th>
            <th>Due Date</th>
            <th>Category</th>
            <th>Assignment Name</th>
            <th>Score</th>
            <th>Percent</th>
            <th>Letter Grade</th>
            <th>Codes</th>
        </tr>
        <tr>
            <td>Ms. McElduff</td>
            <td>Science (grade 6)</td>
            <td>S1</td>
            <td>11/03/2025</td>
            <td>Formative</td>
            <td>Atomic Structure Knowledge Check</td>
            <td></td>
            <td></td>
            <td></td>
            <td><img alt="Missing"></td>
        </tr>
        <tr>
            <td>Mr. Miller</td>
            <td>Social Studies (grade 6)</td>
            <td>S1</td>
            <td>12/15/2025</td>
            <td>Formative</td>
            <td>FORMATIVE - Edpuzzle on Autocracies</td>
            <td></td>
            <td></td>
            <td></td>
            <td><img alt="Missing"></td>
        </tr>
        <tr>
            <td>Ms. Koskinen</td>
            <td>Mathematics (grade 6)</td>
            <td>S1</td>
            <td>12/10/2025</td>
            <td>Evidence</td>
            <td>Chapter 5 Test - Fractions</td>
            <td>42/50</td>
            <td>84%</td>
            <td>B</td>
            <td><img alt="Collected"></td>
        </tr>
    </table>
    </body>
    </html>
    """


@pytest.fixture
def sample_grades_html() -> str:
    """Sample HTML for grades page testing."""
    return """
    <html>
    <body>
    <table id="quickLookup">
        <tr>
            <th>Course</th>
            <th>Teacher</th>
            <th>Q1</th>
            <th>Q2</th>
            <th>S1</th>
            <th>Abs</th>
            <th>Tar</th>
        </tr>
        <tr>
            <td><a href="home.html?frn=123">Social Studies (grade 6)</a></td>
            <td>Mr. Miller</td>
            <td>2</td>
            <td></td>
            <td>2</td>
            <td>2</td>
            <td>0</td>
        </tr>
        <tr>
            <td><a href="home.html?frn=124">Mathematics (grade 6)</a></td>
            <td>Ms. Koskinen</td>
            <td>3</td>
            <td></td>
            <td>3</td>
            <td>1</td>
            <td>1</td>
        </tr>
        <tr>
            <td><a href="home.html?frn=125">Science (grade 6)</a></td>
            <td>Ms. McElduff</td>
            <td>3</td>
            <td></td>
            <td>3</td>
            <td>3</td>
            <td>0</td>
        </tr>
    </table>
    </body>
    </html>
    """


@pytest.fixture
def sample_attendance_html() -> str:
    """Sample HTML for attendance dashboard testing."""
    return """
    <html>
    <body>
    <div class="attendance-rate">
        <span class="value">88.60%</span>
    </div>
    <table class="summary">
        <tr>
            <td>Days Enrolled</td>
            <td>79</td>
        </tr>
        <tr>
            <td>Days Present</td>
            <td>70</td>
        </tr>
        <tr>
            <td>Days Absent</td>
            <td>9</td>
        </tr>
        <tr>
            <td>Excused Absent</td>
            <td>9</td>
        </tr>
        <tr>
            <td>Unexcused Absent</td>
            <td>0</td>
        </tr>
        <tr>
            <td>Tardies</td>
            <td>2</td>
        </tr>
    </table>
    </body>
    </html>
    """


@pytest.fixture
async def empty_db(tmp_path):
    """Create an empty database with schema initialized."""
    db_path = tmp_path / "test.db"
    async with Database(db_path) as db:
        await db.init_schema()
    return db_path


@pytest.fixture
async def populated_db(tmp_path):
    """Create a database with test data."""
    db_path = tmp_path / "test.db"

    async with Database(db_path) as db:
        await db.init_schema()
        repo = Repository(db)

        # Create test student
        student = Student(
            student_id="STU001",
            first_name="Delilah",
            last_name="Culbreth",
            grade_level=6,
            school_name="Eagle Schools",
            district_code="WSWG",
        )
        await repo.insert_student(student)

        # Create test courses
        courses = [
            Course(
                course_id="CRS001",
                course_name="Social Studies (grade 6)",
                expression="1/6(A-B)",
                room="201",
                term="S1",
                teacher_name="Mr. Miller",
                teacher_email="miller@eagleschools.org",
                student_id="STU001",
            ),
            Course(
                course_id="CRS002",
                course_name="Mathematics (grade 6)",
                expression="3/8(A-B)",
                room="202",
                term="S1",
                teacher_name="Ms. Koskinen",
                teacher_email="koskinen@eagleschools.org",
                student_id="STU001",
            ),
            Course(
                course_id="CRS003",
                course_name="Science (grade 6)",
                expression="7/3(A-B)",
                room="206",
                term="S1",
                teacher_name="Ms. McElduff",
                teacher_email="mcelduff@eagleschools.org",
                student_id="STU001",
            ),
        ]
        for course in courses:
            await repo.insert_course(course)

        # Create test grades
        grades = [
            Grade(
                grade_id=generate_id(),
                course_id="CRS001",
                student_id="STU001",
                term="Q1",
                letter_grade="2",
                gpa_points=2.0,
            ),
            Grade(
                grade_id=generate_id(),
                course_id="CRS002",
                student_id="STU001",
                term="Q1",
                letter_grade="3",
                gpa_points=3.0,
            ),
            Grade(
                grade_id=generate_id(),
                course_id="CRS003",
                student_id="STU001",
                term="Q1",
                letter_grade="3",
                gpa_points=3.0,
            ),
        ]
        for grade in grades:
            await repo.insert_grade(grade)

        # Create test assignments
        today = date.today()
        assignments = [
            Assignment(
                assignment_id=generate_id(),
                course_id="CRS003",
                student_id="STU001",
                assignment_name="Atomic Structure Knowledge Check",
                category="Formative",
                due_date=date(2025, 11, 3),
                status="Missing",
            ),
            Assignment(
                assignment_id=generate_id(),
                course_id="CRS001",
                student_id="STU001",
                assignment_name="FORMATIVE - Edpuzzle on Autocracies",
                category="Formative",
                due_date=date(2025, 12, 15),
                status="Missing",
            ),
            Assignment(
                assignment_id=generate_id(),
                course_id="CRS002",
                student_id="STU001",
                assignment_name="Chapter 5 Test - Fractions",
                category="Evidence",
                due_date=today,
                score=42,
                max_score=50,
                percent=84,
                status="Collected",
            ),
        ]
        for assignment in assignments:
            await repo.insert_assignment(assignment)

        # Create attendance summary
        attendance = AttendanceSummary(
            summary_id=generate_id(),
            student_id="STU001",
            term="YTD",
            days_enrolled=79,
            days_present=70,
            days_absent=9,
            days_absent_excused=9,
            days_absent_unexcused=0,
            tardies=2,
            tardies_excused=1,
            tardies_unexcused=1,
            attendance_rate=88.60,
        )
        await repo.insert_attendance_summary(attendance)

    return db_path


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
