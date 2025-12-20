#!/usr/bin/env python3
"""
Full PowerSchool scraper that extracts all data including course-level assignments.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bs4 import BeautifulSoup
from playwright.sync_api import Page, sync_playwright

from src.scraper.auth import get_base_url, get_credentials, login

BASE_URL = get_base_url()
RAW_HTML_DIR = Path(__file__).parent.parent / "raw_html"
RAW_HTML_DIR.mkdir(exist_ok=True)


def get_students(page: Page) -> list:
    """Get list of students from the page."""
    html = page.content()
    soup = BeautifulSoup(html, "lxml")

    students = []
    students_list = soup.select_one("#students-list")
    if students_list:
        for a in students_list.select("a"):
            text = a.get_text(strip=True)
            href = a.get("href", "")
            # Extract student ID from javascript:switchStudent(12345)
            match = re.search(r"switchStudent\((\d+)\)", href)
            if match:
                student_id = match.group(1)
                is_selected = "selected" in a.find_parent("li").get("class", [])
                students.append({
                    "name": text,
                    "id": student_id,
                    "selected": is_selected
                })
    return students


def switch_student(page: Page, student_id: str):
    """Switch to a different student."""
    print(f"Switching to student ID: {student_id}")
    page.evaluate(f"switchStudent({student_id})")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)


def scrape_home_grades(page: Page) -> dict:
    """Scrape grades from home page."""
    print("Scraping home page grades...")
    page.goto(f"{BASE_URL}/guardian/home.html", wait_until="networkidle")
    page.wait_for_timeout(2000)

    html = page.content()
    soup = BeautifulSoup(html, "lxml")

    # Get students
    students = get_students(page)
    current_student = next((s for s in students if s.get("selected")), None)

    data = {
        "students": students,
        "current_student": current_student,
        "courses": [],
        "course_links": [],
    }

    # Parse grades table
    tables = soup.select("table.linkDescList.grid")
    if tables:
        table = tables[0]
        rows = table.select("tr")[2:]  # Skip header rows

        for row in rows:
            cells = row.select("td")
            if len(cells) >= 15:
                expression = cells[0].get_text(strip=True)
                course_cell = cells[11]
                course_text = course_cell.get_text(strip=True)

                # Parse course name, teacher, and email
                teacher_email = None
                email_link = course_cell.select_one("a[href^='mailto:']")
                if email_link:
                    teacher_email = email_link.get("href", "").replace("mailto:", "")

                if "Email" in course_text:
                    course_name = course_text.split("Email")[0].strip()
                    teacher_info = course_text.split("Email")[1].strip()
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
                def clean_grade(cell_idx):
                    if len(cells) > cell_idx:
                        grade = cells[cell_idx].get_text(strip=True)
                        if grade in ["[ i ]", "Not available", "-"]:
                            return ""
                        return grade
                    return ""

                q1 = clean_grade(14)
                q2 = clean_grade(15)
                s1 = clean_grade(16)
                q3 = clean_grade(17) if len(cells) > 17 else ""
                q4 = clean_grade(18) if len(cells) > 18 else ""
                s2 = clean_grade(19) if len(cells) > 19 else ""

                # Get absences/tardies (last two columns)
                absences = cells[-2].get_text(strip=True) if len(cells) >= 2 else "0"
                tardies = cells[-1].get_text(strip=True) if len(cells) >= 1 else "0"

                # Get course link
                q1_cell = cells[14] if len(cells) > 14 else None
                course_link = None
                if q1_cell:
                    link = q1_cell.select_one("a")
                    if link:
                        course_link = link.get("href", "")

                course_data = {
                    "expression": expression,
                    "course_name": course_name,
                    "teacher_name": teacher_name,
                    "teacher_email": teacher_email,
                    "room": room,
                    "q1": q1,
                    "q2": q2,
                    "s1": s1,
                    "q3": q3,
                    "q4": q4,
                    "s2": s2,
                    "absences": absences,
                    "tardies": tardies,
                }
                data["courses"].append(course_data)

                if course_link:
                    data["course_links"].append({
                        "course_name": course_name,
                        "link": course_link
                    })

    (RAW_HTML_DIR / "home.html").write_text(html)
    return data


def scrape_course_assignments(page: Page, course_link: str, course_name: str) -> list:
    """Scrape assignments from a specific course page."""
    print(f"  Scraping {course_name}...")
    url = f"{BASE_URL}/guardian/{course_link}"
    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(1500)

    html = page.content()
    soup = BeautifulSoup(html, "lxml")

    assignments = []

    # Find assignments table
    table = soup.select_one("table.linkDescList")
    if table:
        rows = table.select("tr")
        headers = []

        for row in rows:
            header_cells = row.select("th")
            if header_cells:
                headers = [h.get_text(strip=True).lower() for h in header_cells]
                continue

            cells = row.select("td")
            if len(cells) >= 4:
                assignment = {
                    "course": course_name,
                }

                for i, cell in enumerate(cells):
                    text = cell.get_text(strip=True)
                    if i < len(headers):
                        key = headers[i].replace(" ", "_")
                        assignment[key] = text

                # Determine status from flags/codes
                row_html = str(row)
                if "missing" in row_html.lower() or "M" in assignment.get("flags", ""):
                    assignment["status"] = "Missing"
                elif "late" in row_html.lower() or "L" in assignment.get("flags", ""):
                    assignment["status"] = "Late"
                elif "collected" in row_html.lower():
                    assignment["status"] = "Collected"
                else:
                    assignment["status"] = "Submitted"

                if assignment.get("assignment") or assignment.get("name"):
                    assignments.append(assignment)

    return assignments


def scrape_assignments_q2(page: Page) -> list:
    """Scrape assignments page with Q2 term selected."""
    print("Scraping assignments page (Q2 term)...")
    page.goto(f"{BASE_URL}/guardian/classassignments.html", wait_until="networkidle")
    page.wait_for_timeout(2000)

    # Try to select Q2 term
    try:
        # Look for term filter and click Q2
        page.click("text=Q2", timeout=3000)
        page.wait_for_timeout(2000)
    except:
        print("  Could not click Q2 filter, trying dropdown...")
        try:
            # Try to find a term dropdown
            selects = page.locator("select").all()
            for select in selects:
                options = select.locator("option").all()
                for opt in options:
                    text = opt.inner_text()
                    if "Q2" in text:
                        select.select_option(label=text)
                        page.wait_for_timeout(2000)
                        break
        except Exception as e:
            print(f"  Could not select Q2: {e}")

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
                    status = "Unknown"
                    if "Missing" in codes or "M" in codes:
                        status = "Missing"
                    elif "Late" in codes or "L" in codes:
                        status = "Late"
                    elif "Collected" in codes:
                        status = "Collected"

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
                        "status": status
                    }
                    assignments.append(assignment)
                    print(f"  Found: {assignment_name} ({course}) - {status}")

    (RAW_HTML_DIR / "assignments_q2.html").write_text(html)
    print(f"  Total assignments found: {len(assignments)}")
    return assignments


def scrape_attendance_dashboard(page: Page) -> dict:
    """Scrape attendance dashboard."""
    print("Scraping attendance dashboard...")
    page.goto(f"{BASE_URL}/guardian/mba_attendance_monitor/guardian_dashboard.html", wait_until="networkidle")
    page.wait_for_timeout(5000)

    data = {"rate": 0.0, "days_present": 0, "days_absent": 0, "tardies": 0, "total_days": 0}

    # Wait for data to load
    try:
        # Wait for any attendance percentage to appear
        page.wait_for_selector("text=/\\d+\\.?\\d*%/", timeout=10000)
    except:
        print("  Waiting longer for attendance data...")
        page.wait_for_timeout(5000)

    html = page.content()
    soup = BeautifulSoup(html, "lxml")

    # Try to extract from Angular rendered content
    # Look for percentage values
    text_content = soup.get_text()

    # Find attendance rate - look for pattern like "88.6%" or similar
    rate_matches = re.findall(r"(\d+\.?\d*)%", text_content)
    if rate_matches:
        # Filter to reasonable attendance rates (50-100%)
        for rate in rate_matches:
            rate_float = float(rate)
            if 50 <= rate_float <= 100:
                data["rate"] = rate_float
                print(f"  Found attendance rate: {rate_float}%")
                break

    # Look for specific numbers near keywords
    # Try to find numbers in table cells or divs near "Present", "Absent", etc.
    for elem in soup.find_all(["td", "div", "span"]):
        text = elem.get_text(strip=True).lower()
        if "present" in text:
            nums = re.findall(r"\d+", elem.get_text())
            if nums:
                data["days_present"] = int(nums[0])
        elif "absent" in text and "tardy" not in text:
            nums = re.findall(r"\d+", elem.get_text())
            if nums:
                data["days_absent"] = int(nums[0])
        elif "tardy" in text or "tardies" in text:
            nums = re.findall(r"\d+", elem.get_text())
            if nums:
                data["tardies"] = int(nums[0])

    # Try JavaScript evaluation
    try:
        js_data = page.evaluate("""
            () => {
                try {
                    const scope = angular.element(document.body).scope();
                    if (scope && scope.student) {
                        return {
                            rate: scope.student.attendanceRate || scope.student.rate,
                            present: scope.student.daysPresent || scope.student.present,
                            absent: scope.student.daysAbsent || scope.student.absent,
                            tardy: scope.student.tardies || scope.student.tardy
                        };
                    }
                    // Try alternative data sources
                    if (window.attendanceData) {
                        return window.attendanceData;
                    }
                } catch (e) {}
                return null;
            }
        """)
        if js_data:
            if js_data.get("rate"):
                data["rate"] = float(js_data["rate"])
            if js_data.get("present"):
                data["days_present"] = int(js_data["present"])
            if js_data.get("absent"):
                data["days_absent"] = int(js_data["absent"])
            if js_data.get("tardy"):
                data["tardies"] = int(js_data["tardy"])
    except Exception as e:
        print(f"  Could not extract JS data: {e}")

    (RAW_HTML_DIR / "attendance.html").write_text(html)
    print(f"  Attendance: {data['rate']}% - Present: {data['days_present']}, Absent: {data['days_absent']}, Tardies: {data['tardies']}")
    return data


def scrape_schedule(page: Page) -> list:
    """Scrape schedule page."""
    print("Scraping schedule...")
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
            if len(cells) >= 6:
                expression = cells[0].get_text(strip=True)
                if expression and not expression.startswith("Exp"):
                    course = {
                        "expression": expression,
                        "term": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                        "course_section": cells[2].get_text(strip=True) if len(cells) > 2 else "",
                        "course_name": cells[3].get_text(strip=True) if len(cells) > 3 else "",
                        "teacher": cells[4].get_text(strip=True) if len(cells) > 4 else "",
                        "room": cells[5].get_text(strip=True) if len(cells) > 5 else "",
                    }
                    courses.append(course)

    (RAW_HTML_DIR / "schedule.html").write_text(html)
    return courses


def run_full_scrape(headless: bool = False, student_name: str | None = None):
    """Run full scraping operation.
    
    Args:
        headless: Run browser in headless mode (no visible window)
        student_name: Optional student name to filter scraping to (not yet implemented)
    """
    print("=" * 60)
    print("PowerSchool Full Scrape")
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)

    try:
        get_credentials()  # Validate credentials are available
    except ValueError as e:
        print(f"ERROR: Missing credentials - {e}")
        sys.exit(1)

    all_data = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=200)
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()

        if not login(page):
            browser.close()
            sys.exit(1)

        # Scrape home page grades (this also navigates to home page)
        home_data = scrape_home_grades(page)

        # If student_name is provided, switch to that student and re-scrape
        if student_name:
            students = home_data.get("students", [])
            matching_student = None
            for student in students:
                if student_name.lower() in student.get("name", "").lower():
                    matching_student = student
                    break
            
            if matching_student:
                print(f"Switching to student: {matching_student['name']}")
                switch_student(page, matching_student["id"])
                # Re-scrape after switching student
                home_data = scrape_home_grades(page)
            else:
                print(f"WARNING: Student '{student_name}' not found. Available students:")
                for student in students:
                    print(f"  - {student['name']}")
                print("Continuing with default student...")
        all_data["students"] = home_data["students"]
        all_data["current_student"] = home_data["current_student"]
        all_data["courses"] = home_data["courses"]

        print(f"\nFound {len(home_data['courses'])} courses")
        for c in home_data["courses"]:
            print(f"  {c['course_name']}: Q1={c['q1']}, Q2={c['q2']}")

        # Scrape individual course assignments
        print("\n" + "=" * 40)
        print("Scraping course assignments...")
        all_assignments = []
        for link_info in home_data["course_links"][:5]:  # Limit to first 5 for speed
            try:
                assignments = scrape_course_assignments(
                    page, link_info["link"], link_info["course_name"]
                )
                all_assignments.extend(assignments)
            except Exception as e:
                print(f"  Error scraping {link_info['course_name']}: {e}")

        # Also try Q2 assignments page
        print("\n" + "=" * 40)
        q2_assignments = scrape_assignments_q2(page)
        all_assignments.extend(q2_assignments)

        all_data["assignments"] = all_assignments
        print(f"\nTotal assignments collected: {len(all_assignments)}")

        # Find missing assignments
        missing = [a for a in all_assignments if a.get("status") == "Missing"]
        print(f"Missing assignments: {len(missing)}")
        for a in missing:
            print(f"  - {a.get('assignment_name', a.get('assignment', 'Unknown'))} ({a.get('course', '')})")

        # Scrape schedule
        print("\n" + "=" * 40)
        all_data["schedule"] = scrape_schedule(page)

        # Scrape attendance
        print("\n" + "=" * 40)
        all_data["attendance"] = scrape_attendance_dashboard(page)

        browser.close()

    # Save all data
    data_file = RAW_HTML_DIR / "full_data.json"
    with open(data_file, "w") as f:
        json.dump(all_data, f, indent=2)
    print(f"\nSaved all data to {data_file}")

    # Summary
    print("\n" + "=" * 60)
    print("SCRAPE SUMMARY")
    print("=" * 60)
    print(f"Student: {all_data.get('current_student', {}).get('name', 'Unknown')}")
    print(f"Courses: {len(all_data.get('courses', []))}")
    print(f"Assignments: {len(all_data.get('assignments', []))}")
    print(f"Missing: {len([a for a in all_data.get('assignments', []) if a.get('status') == 'Missing'])}")
    att = all_data.get("attendance", {})
    print(f"Attendance: {att.get('rate', 0)}%")

    return all_data


if __name__ == "__main__":
    run_full_scrape()
