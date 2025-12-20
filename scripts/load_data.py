#!/usr/bin/env python3
"""Load scraped data into the database."""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import init_database, verify_database
from src.database.repository import Repository


def load_scraped_data():
    """Load data from full_data.json into the database."""
    # Initialize database
    print("Initializing database...")
    init_database(force=True)

    # Verify
    info = verify_database()
    print(f"Tables: {info.get('tables', [])}")
    print(f"Views: {info.get('views', [])}")

    # Load scraped data
    data_file = Path(__file__).parent.parent / "raw_html" / "full_data.json"
    if not data_file.exists():
        print(f"ERROR: Data file not found: {data_file}")
        print("Run scripts/scrape_full.py first")
        sys.exit(1)

    with open(data_file) as f:
        data = json.load(f)

    repo = Repository()

    # Insert students
    print("\n=== LOADING STUDENTS ===")
    student_ids = {}
    for student in data.get("students", []):
        student_id = repo.upsert_student(
            powerschool_id=student["id"],
            first_name=student["name"],
        )
        student_ids[student["name"]] = student_id
        print(f"  Added student: {student['name']} (DB ID: {student_id})")

    # Get current student
    current_student = data.get("current_student", {})
    current_student_name = current_student.get(
        "name", list(student_ids.keys())[0] if student_ids else "Unknown"
    )
    current_student_id = student_ids.get(current_student_name, 1)
    print(f"\nCurrent student: {current_student_name} (DB ID: {current_student_id})")

    # Insert courses and grades
    print("\n=== LOADING COURSES & GRADES ===")
    course_ids = {}
    seen_courses = set()

    for course in data.get("courses", []):
        course_key = (course["course_name"], course.get("expression", ""))

        # Skip duplicates
        if course_key in seen_courses:
            continue
        seen_courses.add(course_key)

        course_id = repo.upsert_course(
            student_id=current_student_id,
            course_name=course["course_name"],
            expression=course.get("expression"),
            room=course.get("room"),
            teacher_name=course.get("teacher_name"),
            term="S1",  # Default to S1
        )
        course_ids[course["course_name"]] = course_id
        print(f"  Added course: {course['course_name']} (ID: {course_id})")

        # Add grades for Q1 and Q2 only (these are the actual grades)
        # The q3, q4, s2 in our scraped data are actually absences/tardies columns
        for term in ["q1", "q2", "s1"]:
            grade = course.get(term)
            # Valid grades are: numbers (1-4, 3.5), letters (A-F), P (pass)
            if grade and grade not in ["", "Not available", "[ i ]", "-"]:
                # Check if it looks like a grade (not a number > 10 which would be absences)
                try:
                    if grade.replace(".", "").isdigit():
                        num = float(grade)
                        if num > 10:  # This is probably absences, not a grade
                            continue
                except ValueError:
                    pass

                repo.add_grade(
                    course_id=course_id,
                    student_id=current_student_id,
                    term=term.upper(),
                    letter_grade=grade,
                    absences=int(course.get("absences", 0))
                    if str(course.get("absences", "")).isdigit()
                    else 0,
                    tardies=int(course.get("tardies", 0))
                    if str(course.get("tardies", "")).isdigit()
                    else 0,
                )
                print(f"    Grade {term.upper()}: {grade}")

    # Insert assignments
    print("\n=== LOADING ASSIGNMENTS ===")
    assignments = data.get("assignments", [])
    missing_count = 0
    for assignment in assignments:
        # Skip empty/invalid assignments
        name = (
            assignment.get("assignment_name")
            or assignment.get("assignment")
            or assignment.get("name")
        )
        if not name or len(name) < 2:
            continue

        course_name = assignment.get("course", "Unknown")
        status = assignment.get("status", "Unknown")

        # Parse due date
        due_date = assignment.get("due_date")
        if due_date:
            try:
                # Try MM/DD/YYYY format
                dt = datetime.strptime(due_date, "%m/%d/%Y")
                due_date = dt.strftime("%Y-%m-%d")
            except ValueError:
                due_date = None

        repo.add_assignment(
            student_id=current_student_id,
            course_name=course_name,
            assignment_name=name,
            teacher_name=assignment.get("teacher"),
            category=assignment.get("category"),
            due_date=due_date,
            score=assignment.get("score"),
            percent=float(assignment.get("percent", 0))
            if assignment.get("percent", "").replace(".", "").isdigit()
            else None,
            letter_grade=assignment.get("letter_grade"),
            status=status,
            codes=assignment.get("codes"),
            term=assignment.get("term"),
        )

        if status == "Missing":
            missing_count += 1
            print(f"  [MISSING] {name} ({course_name})")
        else:
            print(f"  {name} ({course_name}) - {status}")

    print(f"\nLoaded {len(assignments)} assignments, {missing_count} missing")

    # Insert attendance summary (use data from home page if available)
    print("\n=== LOADING ATTENDANCE ===")
    attendance = data.get("attendance", {})
    if attendance.get("rate"):
        repo.add_attendance_summary(
            student_id=current_student_id,
            attendance_rate=attendance.get("rate", 0),
            days_present=attendance.get("days_present", 0),
            days_absent=attendance.get("days_absent", 0),
            tardies=attendance.get("tardies", 0),
            total_days=attendance.get("total_days", 0),
        )
        print(f"  Attendance rate: {attendance.get('rate')}%")
    else:
        # Calculate from course data
        total_absences = sum(
            int(c.get("absences", 0)) if str(c.get("absences", "")).isdigit() else 0
            for c in data.get("courses", [])
        )
        total_tardies = sum(
            int(c.get("tardies", 0)) if str(c.get("tardies", "")).isdigit() else 0
            for c in data.get("courses", [])
        )
        # Estimate based on typical school year
        # Assuming roughly 80 school days so far
        estimated_days = 80
        num_courses = max(len(data.get("courses", [])), 1)
        estimated_rate = ((estimated_days - (total_absences / num_courses)) / estimated_days) * 100
        repo.add_attendance_summary(
            student_id=current_student_id,
            attendance_rate=round(estimated_rate, 1),
            days_absent=int(total_absences / max(len(data.get("courses", [1])), 1)),
            tardies=int(total_tardies / max(len(data.get("courses", [1])), 1)),
            total_days=estimated_days,
        )
        print("  Estimated attendance from course data")
        print(f"  Total absences across courses: {total_absences}")
        print(f"  Total tardies across courses: {total_tardies}")

    # Extract and insert teachers from course data
    print("\n=== LOADING TEACHERS ===")

    # First, try to extract emails from the HTML file if they're not in the JSON
    from bs4 import BeautifulSoup

    teacher_emails = {}
    home_html = Path(__file__).parent.parent / "raw_html" / "home.html"
    if home_html.exists():
        soup = BeautifulSoup(home_html.read_text(), "lxml")
        for link in soup.select("a[href^='mailto:']"):
            email = link.get("href", "").replace("mailto:", "")
            parent_td = link.find_parent("td")
            if parent_td:
                parent_text = parent_td.get_text(strip=True)
                if "Email" in parent_text:
                    parts = parent_text.split("Email")
                    if len(parts) > 1:
                        teacher_info = parts[1].strip()
                        name_parts = teacher_info.split("-")
                        teacher_name = name_parts[0].strip()
                        if teacher_name and email:
                            teacher_emails[teacher_name] = email

    teacher_data = {}
    for course in data.get("courses", []):
        teacher_name = course.get("teacher_name")
        teacher_email = course.get("teacher_email")

        # Try to get email from HTML extraction if not in JSON
        if not teacher_email and teacher_name:
            teacher_email = teacher_emails.get(teacher_name)

        if teacher_name:
            if teacher_name not in teacher_data:
                teacher_data[teacher_name] = {
                    "name": teacher_name,
                    "email": teacher_email,
                    "room": course.get("room"),
                    "courses": [],
                }
            teacher_data[teacher_name]["courses"].append(course["course_name"])
            # Update email if we didn't have it
            if teacher_email and not teacher_data[teacher_name]["email"]:
                teacher_data[teacher_name]["email"] = teacher_email

    for name, info in teacher_data.items():
        courses_json = json.dumps(list(set(info["courses"])))
        repo.upsert_teacher(
            name=info["name"],
            email=info["email"],
            room=info["room"],
            courses_taught=courses_json,
        )
        print(f"  Added teacher: {info['name']} ({info.get('email', 'no email')})")

    print(f"\nLoaded {len(teacher_data)} teachers")

    # Final verification
    print("\n=== VERIFICATION ===")
    info = verify_database()
    print(f"Row counts: {info.get('row_counts', {})}")

    # Test queries
    print("\n=== TEST QUERIES ===")
    students = repo.get_students()
    print(f"Students: {[s['first_name'] for s in students]}")

    missing = repo.get_missing_assignments()
    print(f"\nMissing assignments: {len(missing)}")
    for m in missing:
        print(f"  - {m['assignment_name']} ({m['course_name']})")

    summary = repo.get_student_summary(current_student_id)
    if summary:
        print("\nStudent summary:")
        print(f"  Name: {summary['student_name']}")
        print(f"  Courses: {summary['course_count']}")
        print(f"  Missing: {summary['missing_assignments']}")

    actions = repo.get_action_items(current_student_id)
    print(f"\nAction items: {len(actions)}")
    for a in actions[:5]:
        print(f"  [{a['priority']}] {a['message']}")

    print("\n=== LOAD COMPLETE ===")


if __name__ == "__main__":
    load_scraped_data()
