"""Parser for PowerSchool grades page."""

from typing import Any

from bs4 import BeautifulSoup


def parse_grades_page(html: str) -> dict[str, Any]:
    """Parse the home.html page which contains grades and attendance overview.

    This page typically shows a table with:
    - Course name
    - Teacher
    - Q1, Q2, Q3, Q4 grades
    - S1, S2 semester grades
    - Absences and Tardies

    Args:
        html: Raw HTML content from the home page

    Returns:
        Dictionary with 'courses' and 'attendance' data
    """
    soup = BeautifulSoup(html, "html.parser")

    result = {
        "courses": [],
        "attendance_summary": [],
    }

    # Find the grades table
    # PowerSchool typically uses a table with class containing 'grid' or 'grades'
    table = soup.find("table", id="quickLookup")
    if not table:
        table = soup.find("table", class_=lambda c: c and ("grid" in c.lower() or "grades" in c.lower()))
    if not table:
        # Try finding by header content
        tables = soup.find_all("table")
        for t in tables:
            headers = t.find_all("th")
            header_text = " ".join(h.get_text() for h in headers).lower()
            if "course" in header_text and ("q1" in header_text or "grade" in header_text):
                table = t
                break

    if not table:
        return result

    rows = table.find_all("tr")
    if len(rows) < 2:
        return result

    # Parse header to find column indices
    header_row = rows[0]
    headers = [th.get_text(strip=True).upper() for th in header_row.find_all(["th", "td"])]

    # Map column names to indices
    col_indices = {}
    term_columns = ["Q1", "Q2", "Q3", "Q4", "S1", "S2", "Y1"]
    for i, header in enumerate(headers):
        header_upper = header.upper()
        if "COURSE" in header_upper:
            col_indices["course"] = i
        elif "TEACHER" in header_upper or "EXP" in header_upper:
            col_indices["teacher"] = i
        elif header_upper in term_columns:
            col_indices[header_upper] = i
        elif "ABS" in header_upper:
            col_indices["absences"] = i
        elif "TAR" in header_upper:
            col_indices["tardies"] = i

    # Parse data rows
    for row in rows[1:]:
        cols = row.find_all(["td", "th"])
        if not cols:
            continue

        course_data = {
            "course_name": None,
            "teacher_name": None,
            "grades": {},
            "absences": None,
            "tardies": None,
        }

        for col_name, col_idx in col_indices.items():
            if col_idx >= len(cols):
                continue

            cell = cols[col_idx]
            text = cell.get_text(strip=True)

            if col_name == "course":
                course_data["course_name"] = text
                # Check for teacher email link
                link = cell.find("a")
                if link:
                    course_data["course_link"] = link.get("href", "")
            elif col_name == "teacher":
                course_data["teacher_name"] = text
            elif col_name in term_columns:
                course_data["grades"][col_name] = _parse_grade(text)
            elif col_name == "absences":
                course_data["absences"] = _parse_int(text)
            elif col_name == "tardies":
                course_data["tardies"] = _parse_int(text)

        if course_data["course_name"]:
            result["courses"].append(course_data)

    return result


def parse_grade_history_page(html: str) -> list[dict[str, Any]]:
    """Parse the grade history page showing historical grades.

    Args:
        html: Raw HTML content from the grade history page

    Returns:
        List of historical grade entries
    """
    soup = BeautifulSoup(html, "html.parser")
    history = []

    # Find grade history table
    table = soup.find("table", class_=lambda c: c and "history" in c.lower())
    if not table:
        tables = soup.find_all("table")
        for t in tables:
            if t.find(text=lambda x: x and "grade" in x.lower()):
                table = t
                break

    if not table:
        return history

    rows = table.find_all("tr")
    for row in rows[1:]:  # Skip header
        cols = row.find_all("td")
        if len(cols) >= 4:
            try:
                entry = {
                    "term": cols[0].get_text(strip=True),
                    "course_name": cols[1].get_text(strip=True),
                    "letter_grade": cols[2].get_text(strip=True),
                    "percent": _parse_percent(cols[3].get_text(strip=True)),
                }
                history.append(entry)
            except (IndexError, ValueError):
                continue

    return history


def _parse_grade(text: str) -> dict[str, Any] | None:
    """Parse a grade cell which may contain letter grade and/or percentage."""
    if not text or text in ("--", "-", ""):
        return None

    result = {"letter_grade": None, "percent": None, "gpa_points": None}

    # Handle grades like "A 95%" or just "A" or just "95%"
    text = text.strip()

    # Check if it's a letter grade
    letter_grades = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F", "P", "I", "W"]
    numeric_grades = ["4", "3", "2", "1", "0"]  # For standards-based grading

    parts = text.split()
    for part in parts:
        clean_part = part.strip()
        if clean_part in letter_grades:
            result["letter_grade"] = clean_part
            result["gpa_points"] = _letter_to_gpa(clean_part)
        elif clean_part in numeric_grades:
            result["letter_grade"] = clean_part
            result["gpa_points"] = float(clean_part)
        elif "%" in clean_part:
            result["percent"] = _parse_percent(clean_part)
        else:
            try:
                # Maybe it's just a number
                val = float(clean_part)
                if val <= 4:  # Probably GPA scale
                    result["letter_grade"] = clean_part
                    result["gpa_points"] = val
                else:  # Probably percentage
                    result["percent"] = val
            except ValueError:
                pass

    if result["letter_grade"] is None and result["percent"] is None:
        # Just use the raw text as letter grade
        result["letter_grade"] = text

    return result


def _parse_percent(text: str) -> float | None:
    """Parse a percentage string."""
    if not text:
        return None
    text = text.replace("%", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def _parse_int(text: str) -> int | None:
    """Parse an integer string."""
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _letter_to_gpa(letter: str) -> float:
    """Convert letter grade to GPA points."""
    gpa_map = {
        "A+": 4.0,
        "A": 4.0,
        "A-": 3.7,
        "B+": 3.3,
        "B": 3.0,
        "B-": 2.7,
        "C+": 2.3,
        "C": 2.0,
        "C-": 1.7,
        "D+": 1.3,
        "D": 1.0,
        "D-": 0.7,
        "F": 0.0,
        "P": None,  # Pass - no GPA impact
        "I": None,  # Incomplete
        "W": None,  # Withdrawn
    }
    return gpa_map.get(letter)
