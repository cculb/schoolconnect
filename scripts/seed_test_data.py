#!/usr/bin/env python3
"""Seed the database with realistic test data based on actual PowerSchool data.

This script creates sample data for testing without needing to scrape real PowerSchool.
Based on the sample data from the project specification (Delilah Rae Culbreth).
"""

import asyncio
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import Database
from src.database.models import (
    Assignment,
    AttendanceSummary,
    Course,
    Grade,
    Student,
)
from src.database.repository import Repository, generate_id


async def seed_database(db_path: str = "data/powerschool.db") -> None:
    """Seed the database with test data."""
    print(f"Seeding database at {db_path}...")

    async with Database(db_path) as db:
        # Initialize schema first
        await db.init_schema()
        print("✓ Schema initialized")

        repo = Repository(db)

        # ==================== STUDENT ====================
        student = Student(
            student_id="STU001",
            first_name="Delilah",
            last_name="Culbreth",
            grade_level=6,
            school_name="Eagle Schools",
            district_code="WSWG",
        )
        await repo.insert_student(student)
        print(f"✓ Created student: {student.full_name}")

        # ==================== COURSES ====================
        courses_data = [
            {
                "course_id": "CRS001",
                "course_name": "Social Studies (grade 6)",
                "expression": "1/6(A-B)",
                "room": "201",
                "term": "S1",
                "teacher_name": "Mr. Miller",
                "teacher_email": "miller@eagleschools.org",
            },
            {
                "course_id": "CRS002",
                "course_name": "Exploratory",
                "expression": "2/7(A-B)",
                "room": "206",
                "term": "S1",
                "teacher_name": "Ms. McElduff",
                "teacher_email": "mcelduff@eagleschools.org",
            },
            {
                "course_id": "CRS003",
                "course_name": "Mathematics (grade 6)",
                "expression": "3/8(A-B)",
                "room": "202",
                "term": "S1",
                "teacher_name": "Ms. Koskinen",
                "teacher_email": "koskinen@eagleschools.org",
            },
            {
                "course_id": "CRS004",
                "course_name": "General Band",
                "expression": "4(A-B)",
                "room": "BAND",
                "term": "S1",
                "teacher_name": "Ms. Peto",
                "teacher_email": "peto@eagleschools.org",
            },
            {
                "course_id": "CRS005",
                "course_name": "Language Arts (grade 6)",
                "expression": "5/1(A-B)",
                "room": "206",
                "term": "S1",
                "teacher_name": "Ms. McElduff",
                "teacher_email": "mcelduff@eagleschools.org",
            },
            {
                "course_id": "CRS006",
                "course_name": "Physical Education (grade 6)",
                "expression": "6/2(A-B)",
                "room": "GYM",
                "term": "S1",
                "teacher_name": "Mr. Robertson",
                "teacher_email": "robertson@eagleschools.org",
            },
            {
                "course_id": "CRS007",
                "course_name": "Science (grade 6)",
                "expression": "7/3(A-B)",
                "room": "206",
                "term": "S1",
                "teacher_name": "Ms. McElduff",
                "teacher_email": "mcelduff@eagleschools.org",
            },
            {
                "course_id": "CRS008",
                "course_name": "Entrepreneurship",
                "expression": "8/4(A-B)",
                "room": "ART",
                "term": "S1",
                "teacher_name": "Ms. Erickson",
                "teacher_email": "erickson@eagleschools.org",
            },
            {
                "course_id": "CRS009",
                "course_name": "Seminar",
                "expression": "Advisory",
                "room": "varies",
                "term": "S1",
                "teacher_name": "Ms. Vanwel",
                "teacher_email": "vanwel@eagleschools.org",
            },
        ]

        for course_data in courses_data:
            course = Course(
                student_id=student.student_id,
                enroll_date=date(2025, 8, 25),
                **course_data,
            )
            await repo.insert_course(course)
        print(f"✓ Created {len(courses_data)} courses")

        # ==================== GRADES ====================
        # Using numeric grades (1-4 scale, common for middle schools)
        # 4=A, 3=B, 2=C, 1=D
        grades_data = [
            # Q1 grades
            ("CRS001", "Q1", "2", None, 2.0),  # Social Studies - needs work
            ("CRS003", "Q1", "3", None, 3.0),  # Mathematics
            ("CRS004", "Q1", "3", None, 3.0),  # General Band
            ("CRS005", "Q1", "3", None, 3.0),  # Language Arts
            ("CRS006", "Q1", "3", None, 3.0),  # Physical Education
            ("CRS007", "Q1", "3", None, 3.0),  # Science
            ("CRS008", "Q1", "3", None, 3.0),  # Entrepreneurship
            ("CRS009", "Q1", "3", None, 3.0),  # Seminar
            # S1 grades (semester 1)
            ("CRS001", "S1", "2", None, 2.0),
            ("CRS003", "S1", "3", None, 3.0),
            ("CRS004", "S1", "3", None, 3.0),
            ("CRS005", "S1", "3", None, 3.0),
            ("CRS006", "S1", "3", None, 3.0),
            ("CRS007", "S1", "3", None, 3.0),
            ("CRS008", "S1", "3", None, 3.0),
            ("CRS009", "S1", "3", None, 3.0),
        ]

        for course_id, term, letter_grade, percent, gpa_points in grades_data:
            grade = Grade(
                grade_id=generate_id(),
                course_id=course_id,
                student_id=student.student_id,
                term=term,
                letter_grade=letter_grade,
                percent=percent,
                gpa_points=gpa_points,
            )
            await repo.insert_grade(grade)
        print(f"✓ Created {len(grades_data)} grades")

        # ==================== ASSIGNMENTS ====================
        today = date.today()
        assignments_data = [
            # Missing assignments
            {
                "course_id": "CRS007",  # Science
                "assignment_name": "Atomic Structure Knowledge Check",
                "category": "Formative",
                "due_date": date(2025, 11, 3),
                "score": None,
                "max_score": 10,
                "status": "Missing",
            },
            {
                "course_id": "CRS001",  # Social Studies
                "assignment_name": "FORMATIVE - Edpuzzle on Autocracies",
                "category": "Formative",
                "due_date": date(2025, 12, 15),
                "score": None,
                "max_score": 10,
                "status": "Missing",
            },
            # Completed assignments - Science
            {
                "course_id": "CRS007",
                "assignment_name": "Cell Structure Lab Report",
                "category": "Evidence",
                "due_date": today - timedelta(days=14),
                "score": 8,
                "max_score": 10,
                "percent": 80,
                "status": "Collected",
            },
            {
                "course_id": "CRS007",
                "assignment_name": "Periodic Table Quiz",
                "category": "Formative",
                "due_date": today - timedelta(days=10),
                "score": 9,
                "max_score": 10,
                "percent": 90,
                "status": "Collected",
            },
            # Completed assignments - Math
            {
                "course_id": "CRS003",
                "assignment_name": "Chapter 5 Test - Fractions",
                "category": "Evidence",
                "due_date": today - timedelta(days=7),
                "score": 42,
                "max_score": 50,
                "percent": 84,
                "status": "Collected",
            },
            {
                "course_id": "CRS003",
                "assignment_name": "Decimal Operations Worksheet",
                "category": "Formative",
                "due_date": today - timedelta(days=5),
                "score": 18,
                "max_score": 20,
                "percent": 90,
                "status": "Collected",
            },
            # Completed assignments - Language Arts
            {
                "course_id": "CRS005",
                "assignment_name": "The Grinch: Compare and Contrast Analysis",
                "category": "Evidence",
                "due_date": today - timedelta(days=3),
                "score": 85,
                "max_score": 100,
                "percent": 85,
                "status": "Collected",
            },
            {
                "course_id": "CRS005",
                "assignment_name": "Vocabulary Unit 8",
                "category": "Formative",
                "due_date": today - timedelta(days=2),
                "score": 9,
                "max_score": 10,
                "percent": 90,
                "status": "Collected",
            },
            # Completed assignments - Social Studies
            {
                "course_id": "CRS001",
                "assignment_name": "Geography of Europe Map Quiz",
                "category": "Formative",
                "due_date": today - timedelta(days=8),
                "score": 7,
                "max_score": 10,
                "percent": 70,
                "status": "Collected",
            },
            # PE - Always collected
            {
                "course_id": "CRS006",
                "assignment_name": "Participation - Week 12",
                "category": "Participation",
                "due_date": today - timedelta(days=1),
                "score": 10,
                "max_score": 10,
                "percent": 100,
                "status": "Collected",
            },
            # Band
            {
                "course_id": "CRS004",
                "assignment_name": "Scale Performance Assessment",
                "category": "Performance",
                "due_date": today - timedelta(days=4),
                "score": 45,
                "max_score": 50,
                "percent": 90,
                "status": "Collected",
            },
            # Entrepreneurship
            {
                "course_id": "CRS008",
                "assignment_name": "Business Plan Draft",
                "category": "Evidence",
                "due_date": today - timedelta(days=6),
                "score": 88,
                "max_score": 100,
                "percent": 88,
                "status": "Collected",
            },
            # Upcoming assignments (not yet due)
            {
                "course_id": "CRS003",
                "assignment_name": "Chapter 6 Homework",
                "category": "Formative",
                "due_date": today + timedelta(days=3),
                "score": None,
                "max_score": 20,
                "status": "Pending",
            },
            {
                "course_id": "CRS005",
                "assignment_name": "Book Report: Wonder",
                "category": "Evidence",
                "due_date": today + timedelta(days=7),
                "score": None,
                "max_score": 100,
                "status": "Pending",
            },
            {
                "course_id": "CRS007",
                "assignment_name": "Chemical Reactions Lab",
                "category": "Evidence",
                "due_date": today + timedelta(days=10),
                "score": None,
                "max_score": 50,
                "status": "Pending",
            },
        ]

        for assignment_data in assignments_data:
            # Set defaults for optional fields
            assignment_data.setdefault("percent", None)
            assignment_data.setdefault("letter_grade", None)
            assignment_data.setdefault("has_comment", False)
            assignment_data.setdefault("has_description", True)

            assignment = Assignment(
                assignment_id=generate_id(),
                student_id=student.student_id,
                **assignment_data,
            )
            await repo.insert_assignment(assignment)
        print(f"✓ Created {len(assignments_data)} assignments")

        # ==================== ATTENDANCE SUMMARY ====================
        attendance = AttendanceSummary(
            summary_id=generate_id(),
            student_id=student.student_id,
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
        print("✓ Created attendance summary")

        # Add another student for testing multi-student queries
        student2 = Student(
            student_id="STU002",
            first_name="Marcus",
            last_name="Johnson",
            grade_level=8,
            school_name="Eagle Schools",
            district_code="WSWG",
        )
        await repo.insert_student(student2)
        print(f"✓ Created student: {student2.full_name}")

        # Add a couple courses and grades for second student
        course2 = Course(
            course_id="CRS010",
            course_name="Algebra I",
            expression="1(A)",
            room="301",
            term="S1",
            teacher_name="Mr. Thompson",
            teacher_email="thompson@eagleschools.org",
            student_id=student2.student_id,
            enroll_date=date(2025, 8, 25),
        )
        await repo.insert_course(course2)

        grade2 = Grade(
            grade_id=generate_id(),
            course_id="CRS010",
            student_id=student2.student_id,
            term="Q1",
            letter_grade="A",
            percent=95,
            gpa_points=4.0,
        )
        await repo.insert_grade(grade2)

        # Add attendance for second student
        attendance2 = AttendanceSummary(
            summary_id=generate_id(),
            student_id=student2.student_id,
            term="YTD",
            days_enrolled=79,
            days_present=77,
            days_absent=2,
            days_absent_excused=2,
            days_absent_unexcused=0,
            tardies=1,
            tardies_excused=1,
            tardies_unexcused=0,
            attendance_rate=97.47,
        )
        await repo.insert_attendance_summary(attendance2)

        print("\n✅ Database seeded successfully!")
        print("\nSummary:")
        print(f"  - Students: 2")
        print(f"  - Courses: {len(courses_data) + 1}")
        print(f"  - Grades: {len(grades_data) + 1}")
        print(f"  - Assignments: {len(assignments_data)}")
        print(f"  - Attendance Summaries: 2")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Seed the PowerSchool database with test data")
    parser.add_argument(
        "--db",
        default="data/powerschool.db",
        help="Path to database file (default: data/powerschool.db)",
    )
    args = parser.parse_args()

    asyncio.run(seed_database(args.db))


if __name__ == "__main__":
    main()
