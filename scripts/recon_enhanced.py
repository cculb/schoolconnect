#!/usr/bin/env python3
"""
Enhanced reconnaissance script that handles dynamic content and extracts actual data.
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.sync_api import sync_playwright, Page
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

BASE_URL = os.getenv("POWERSCHOOL_URL")
if not BASE_URL:
    raise ValueError("POWERSCHOOL_URL environment variable is required")
USERNAME = os.getenv("POWERSCHOOL_USERNAME")
PASSWORD = os.getenv("POWERSCHOOL_PASSWORD")

RAW_HTML_DIR = Path(__file__).parent.parent / "raw_html"
RAW_HTML_DIR.mkdir(exist_ok=True)


def login(page: Page) -> bool:
    """Login to PowerSchool parent portal."""
    print(f"Navigating to {BASE_URL}/public/home.html")
    page.goto(f"{BASE_URL}/public/home.html", wait_until="networkidle")
    page.wait_for_selector("#fieldAccount", timeout=10000)

    print(f"Logging in as {USERNAME}...")
    page.fill("#fieldAccount", USERNAME)
    page.fill("#fieldPassword", PASSWORD)
    page.click("#btn-enter-sign-in")

    try:
        page.wait_for_url("**/guardian/**", timeout=15000)
        print("Login successful!")
        return True
    except Exception as e:
        print(f"Login failed: {e}")
        return False


def get_student_info(page: Page) -> dict:
    """Extract current student information."""
    info = {}

    # Look for student name in header
    try:
        # Try multiple selectors
        selectors = [
            "#userName",
            ".student-name",
            "#student-name",
            "span.studentName"
        ]
        for sel in selectors:
            elem = page.query_selector(sel)
            if elem:
                info["student_name"] = elem.inner_text().strip()
                break

        # Look for grade level
        header_text = page.locator("header").inner_text()
        if "Grade" in header_text:
            match = re.search(r"Grade\s*(\d+)", header_text)
            if match:
                info["grade_level"] = match.group(1)
    except Exception as e:
        print(f"  Warning: Could not extract student info: {e}")

    return info


def scrape_home_page(page: Page) -> dict:
    """Scrape the home page for grades and attendance summary."""
    print("\n=== SCRAPING HOME PAGE ===")
    page.goto(f"{BASE_URL}/guardian/home.html", wait_until="networkidle")
    page.wait_for_timeout(2000)

    data = {"courses": [], "attendance_weekly": {}}

    # Get student info
    student_info = get_student_info(page)
    data["student"] = student_info
    print(f"  Student: {student_info}")

    # Parse grades table
    html = page.content()
    soup = BeautifulSoup(html, "lxml")

    # Find the main grades table (first table with class linkDescList and grid)
    tables = soup.select("table.linkDescList.grid")
    if tables:
        table = tables[0]
        rows = table.select("tr")

        # Skip header rows (first 2)
        for row in rows[2:]:
            cells = row.select("td")
            if len(cells) >= 15:
                # Extract course data
                expression = cells[0].get_text(strip=True)
                course_cell = cells[11]  # Course column

                # Parse course name and teacher
                course_text = course_cell.get_text(strip=True)
                course_link = course_cell.select_one("a")

                # Extract course name (before "Email")
                if "Email" in course_text:
                    course_name = course_text.split("Email")[0].strip()
                    teacher_info = course_text.split("Email")[1].strip()
                    # Parse teacher name and room
                    teacher_parts = teacher_info.split("-")
                    teacher_name = teacher_parts[0].strip() if teacher_parts else ""
                    room = ""
                    if len(teacher_parts) > 1:
                        room_match = re.search(r"Rm:(\S+)", teacher_parts[-1])
                        if room_match:
                            room = room_match.group(1)
                else:
                    course_name = course_text
                    teacher_name = ""
                    room = ""

                # Extract grades
                q1 = cells[14].get_text(strip=True) if len(cells) > 14 else ""
                q2 = cells[15].get_text(strip=True) if len(cells) > 15 else ""
                s1 = cells[16].get_text(strip=True) if len(cells) > 16 else ""

                # Extract absences/tardies
                absences = cells[18].get_text(strip=True) if len(cells) > 18 else "0"
                tardies = cells[19].get_text(strip=True) if len(cells) > 19 else "0"

                # Clean up grades (remove "[ i ]" indicators)
                for grade in [q1, q2, s1]:
                    if grade == "[ i ]" or grade == "Not available":
                        grade = ""

                course_data = {
                    "expression": expression,
                    "course_name": course_name,
                    "teacher_name": teacher_name,
                    "room": room,
                    "q1": q1 if q1 not in ["[ i ]", "Not available"] else "",
                    "q2": q2 if q2 not in ["[ i ]", "Not available"] else "",
                    "s1": s1 if s1 not in ["[ i ]", "Not available"] else "",
                    "absences": absences,
                    "tardies": tardies,
                }
                data["courses"].append(course_data)
                print(f"  Course: {course_name} - Q1: {q1}, Q2: {q2}, Teacher: {teacher_name}")

    # Save HTML
    (RAW_HTML_DIR / "home.html").write_text(html)
    return data


def scrape_assignments_page(page: Page, show_all: bool = True) -> list:
    """Scrape the assignments page."""
    print("\n=== SCRAPING ASSIGNMENTS PAGE ===")

    # Navigate to base assignments page first
    url = f"{BASE_URL}/guardian/classassignments.html"
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(2000)

    # Check if there are any filter dropdowns we can manipulate
    try:
        # Look for term/filter dropdowns and select "All"
        selects = page.locator("select").all()
        for select in selects:
            options = select.locator("option").all()
            for opt in options:
                text = opt.inner_text().lower()
                if "all" in text or text == "":
                    try:
                        select.select_option(label=opt.inner_text())
                        page.wait_for_timeout(500)
                    except:
                        pass
                    break
    except Exception as e:
        print(f"  Note: Could not manipulate filters: {e}")

    page.wait_for_timeout(2000)

    # Parse assignments
    html = page.content()
    soup = BeautifulSoup(html, "lxml")

    assignments = []
    table = soup.select_one("#results")

    if table:
        rows = table.select("tbody tr, tr")
        for row in rows:
            cells = row.select("td")
            if len(cells) >= 10:
                teacher = cells[0].get_text(strip=True)
                course = cells[1].get_text(strip=True)
                term = cells[2].get_text(strip=True)
                due_date = cells[3].get_text(strip=True)
                category = cells[4].get_text(strip=True)
                assignment_name = cells[5].get_text(strip=True)
                score = cells[6].get_text(strip=True)
                percent = cells[7].get_text(strip=True)
                letter_grade = cells[8].get_text(strip=True)
                codes = cells[9].get_text(strip=True)

                if teacher and teacher != "No Assignments Found.":
                    assignment = {
                        "teacher": teacher,
                        "course": course,
                        "term": term,
                        "due_date": due_date,
                        "category": category,
                        "assignment_name": assignment_name,
                        "score": score,
                        "percent": percent,
                        "letter_grade": letter_grade,
                        "codes": codes,
                        "status": "Missing" if "Missing" in codes else "Collected" if "Collected" in codes else "Unknown"
                    }
                    assignments.append(assignment)
                    print(f"  Assignment: {assignment_name} ({course}) - Score: {score}, Status: {codes}")

    print(f"  Found {len(assignments)} assignments")

    # Save HTML
    (RAW_HTML_DIR / "assignments.html").write_text(html)
    return assignments


def scrape_schedule_page(page: Page) -> list:
    """Scrape the schedule page for detailed course info."""
    print("\n=== SCRAPING SCHEDULE PAGE ===")
    page.goto(f"{BASE_URL}/guardian/myschedule.html", wait_until="networkidle")
    page.wait_for_timeout(2000)

    html = page.content()
    soup = BeautifulSoup(html, "lxml")

    courses = []
    table = soup.select_one("#results")

    if table:
        rows = table.select("tbody tr, tr")
        for row in rows:
            cells = row.select("td")
            if len(cells) >= 8:
                expression = cells[0].get_text(strip=True)
                term = cells[1].get_text(strip=True)
                course_section = cells[2].get_text(strip=True)
                course_name = cells[3].get_text(strip=True)
                teacher = cells[4].get_text(strip=True)
                room = cells[5].get_text(strip=True)
                enroll = cells[6].get_text(strip=True)
                leave = cells[7].get_text(strip=True)

                if expression and not expression.startswith("Exp"):
                    course = {
                        "expression": expression,
                        "term": term,
                        "course_section": course_section,
                        "course_name": course_name,
                        "teacher": teacher,
                        "room": room,
                        "enroll_date": enroll,
                        "leave_date": leave,
                    }
                    courses.append(course)
                    print(f"  Schedule: {course_name} - {teacher} (Rm: {room})")

    print(f"  Found {len(courses)} courses in schedule")

    # Save HTML
    (RAW_HTML_DIR / "schedule.html").write_text(html)
    return courses


def scrape_attendance_dashboard(page: Page) -> dict:
    """Scrape the attendance dashboard for detailed attendance data."""
    print("\n=== SCRAPING ATTENDANCE DASHBOARD ===")
    page.goto(f"{BASE_URL}/guardian/mba_attendance_monitor/guardian_dashboard.html", wait_until="networkidle")

    # Wait for Angular app to load data
    page.wait_for_timeout(5000)

    data = {"rate": 0, "days_present": 0, "days_absent": 0, "tardies": 0}

    # Try to extract data from the rendered page
    try:
        # Look for attendance rate - often in a large display element
        html = page.content()

        # Search for percentage patterns
        rate_match = re.search(r"(\d+\.?\d*)\s*%", html)
        if rate_match:
            data["rate"] = float(rate_match.group(1))
            print(f"  Attendance rate found: {data['rate']}%")

        # Try to find specific labels with numbers
        soup = BeautifulSoup(html, "lxml")

        # Look for text that contains attendance statistics
        for text in soup.stripped_strings:
            text_lower = text.lower()
            if "present" in text_lower and any(c.isdigit() for c in text):
                nums = re.findall(r"\d+", text)
                if nums:
                    data["days_present"] = int(nums[0])
            elif "absent" in text_lower and any(c.isdigit() for c in text):
                nums = re.findall(r"\d+", text)
                if nums:
                    data["days_absent"] = int(nums[0])
            elif "tard" in text_lower and any(c.isdigit() for c in text):
                nums = re.findall(r"\d+", text)
                if nums:
                    data["tardies"] = int(nums[0])

        # Try using page.evaluate to get data from Angular scope
        try:
            angular_data = page.evaluate("""
                () => {
                    const scope = angular.element(document.body).scope();
                    if (scope && scope.student) {
                        return {
                            rate: scope.student.attendanceRate,
                            present: scope.student.daysPresent,
                            absent: scope.student.daysAbsent,
                            tardy: scope.student.tardies
                        };
                    }
                    return null;
                }
            """)
            if angular_data:
                print(f"  Angular data: {angular_data}")
                if angular_data.get("rate"):
                    data["rate"] = float(angular_data["rate"])
                if angular_data.get("present"):
                    data["days_present"] = int(angular_data["present"])
                if angular_data.get("absent"):
                    data["days_absent"] = int(angular_data["absent"])
                if angular_data.get("tardy"):
                    data["tardies"] = int(angular_data["tardy"])
        except Exception as e:
            print(f"  Note: Could not extract Angular data: {e}")

        print(f"  Attendance: Rate={data['rate']}%, Present={data['days_present']}, Absent={data['days_absent']}, Tardies={data['tardies']}")

    except Exception as e:
        print(f"  Error extracting attendance: {e}")

    # Save HTML
    (RAW_HTML_DIR / "attendance.html").write_text(page.content())
    return data


def scrape_course_grades(page: Page, course_name: str, frn: str = None) -> list:
    """Scrape individual course grade page for detailed assignment breakdown."""
    # This would navigate to individual course pages
    # URL pattern: /guardian/scores.html?frn=...
    pass


def run_enhanced_recon():
    """Run enhanced reconnaissance with data extraction."""
    print("=" * 60)
    print("Enhanced PowerSchool Reconnaissance")
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)

    if not USERNAME or not PASSWORD:
        print("ERROR: Missing credentials. Check .env file.")
        sys.exit(1)

    all_data = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = context.new_page()

        if not login(page):
            browser.close()
            sys.exit(1)

        # Scrape each page with error handling
        try:
            all_data["home"] = scrape_home_page(page)
        except Exception as e:
            print(f"Error scraping home: {e}")
            all_data["home"] = {"error": str(e)}

        try:
            all_data["schedule"] = scrape_schedule_page(page)
        except Exception as e:
            print(f"Error scraping schedule: {e}")
            all_data["schedule"] = []

        try:
            all_data["assignments"] = scrape_assignments_page(page)
        except Exception as e:
            print(f"Error scraping assignments: {e}")
            all_data["assignments"] = []

        try:
            all_data["attendance"] = scrape_attendance_dashboard(page)
        except Exception as e:
            print(f"Error scraping attendance: {e}")
            all_data["attendance"] = {}

        browser.close()

    # Save extracted data
    data_file = RAW_HTML_DIR / "extracted_data.json"
    with open(data_file, "w") as f:
        json.dump(all_data, f, indent=2)
    print(f"\nSaved extracted data to {data_file}")

    # Summary
    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)

    if "home" in all_data:
        print(f"\nStudent: {all_data['home'].get('student', {})}")
        print(f"Courses found: {len(all_data['home'].get('courses', []))}")
        for c in all_data["home"].get("courses", [])[:5]:
            print(f"  - {c['course_name']}: Q1={c['q1']}, Q2={c['q2']}")

    if "schedule" in all_data:
        print(f"\nSchedule entries: {len(all_data['schedule'])}")

    if "assignments" in all_data:
        print(f"\nAssignments: {len(all_data['assignments'])}")
        missing = [a for a in all_data["assignments"] if a.get("status") == "Missing"]
        print(f"  Missing assignments: {len(missing)}")
        for a in missing[:5]:
            print(f"  - {a['assignment_name']} ({a['course']})")

    if "attendance" in all_data:
        att = all_data["attendance"]
        print(f"\nAttendance: {att.get('rate', 'N/A')}%")
        print(f"  Days present: {att.get('days_present', 'N/A')}")
        print(f"  Days absent: {att.get('days_absent', 'N/A')}")
        print(f"  Tardies: {att.get('tardies', 'N/A')}")

    print("\n" + "=" * 60)
    print("Enhanced reconnaissance complete!")
    print("=" * 60)

    return all_data


if __name__ == "__main__":
    run_enhanced_recon()
