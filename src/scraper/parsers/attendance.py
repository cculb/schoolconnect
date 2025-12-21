"""Daily attendance parser for PowerSchool HTML.

This module provides functions to parse daily attendance records from
PowerSchool's HTML attendance grid and detect attendance patterns.

Typical PowerSchool attendance grid structure:
    - Table with M/T/W/H/F (or M/T/W/Th/F) columns
    - Each cell contains a status code (., A, T, E, etc.)
    - Cell classes indicate status (att-present, att-absent, etc.)
    - Cells have data-date attribute for the specific date

Status codes:
    . = Present
    A = Absent (unexcused)
    E = Excused absence
    T = Tardy
    P = Present (alternative)
"""

import re
from datetime import datetime
from typing import Dict, List, Optional

from bs4 import BeautifulSoup


def parse_daily_attendance(html: str) -> List[Dict[str, str]]:
    """Parse daily attendance records from PowerSchool HTML.

    Args:
        html: Raw HTML string containing attendance grid

    Returns:
        List of attendance records, each containing:
            - date: Date in YYYY-MM-DD format
            - status: Normalized status (Present, Absent, Tardy, Excused, Unknown)
            - code: Original attendance code from PowerSchool
    """
    if not html or not html.strip():
        return []

    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return []

    records = []

    # Strategy 1: Look for attendance grid table with data-date attributes
    records = _parse_attendance_grid_table(soup)
    if records:
        return records

    # Strategy 2: Look for attendance-day divs (alternative format)
    records = _parse_attendance_day_divs(soup)
    if records:
        return records

    # Strategy 3: Look for any table with attendance-like structure
    records = _parse_generic_attendance_table(soup)

    return records


def _parse_attendance_grid_table(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """Parse attendance from grid table with data-date attributes."""
    records = []

    # Find cells with data-date attribute
    cells = soup.find_all(attrs={"data-date": True})

    for cell in cells:
        date_str = cell.get("data-date", "")
        if not date_str:
            continue

        parsed_date = parse_attendance_date(date_str)
        if not parsed_date:
            continue

        # Get the code from the cell content
        code_elem = cell.find("span", class_="code")
        if code_elem:
            code = code_elem.get_text(strip=True)
        else:
            code = cell.get_text(strip=True)

        # Get class names for status detection
        cell_class = " ".join(cell.get("class", []))

        status = normalize_attendance_status(code, cell_class)

        records.append({"date": parsed_date, "status": status, "code": code})

    return records


def _parse_attendance_day_divs(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """Parse attendance from day-based div structure."""
    records = []

    # Find attendance-day divs
    day_divs = soup.find_all("div", class_="attendance-day")

    for day_div in day_divs:
        date_str = day_div.get("data-date", "")
        if not date_str:
            continue

        parsed_date = parse_attendance_date(date_str)
        if not parsed_date:
            continue

        # Find status element
        status_elem = day_div.find("span", class_="status")
        if status_elem:
            status_class = " ".join(status_elem.get("class", []))
            status_text = status_elem.get_text(strip=True)
            status = normalize_attendance_status(status_text, status_class)
        else:
            status = "Unknown"

        # Find code element
        code_elem = day_div.find("span", class_="code")
        code = code_elem.get_text(strip=True) if code_elem else ""

        records.append({"date": parsed_date, "status": status, "code": code})

    return records


def _parse_generic_attendance_table(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """Parse attendance from generic table structure."""
    records = []

    # Look for attendance grid table
    table = soup.find("table", class_=re.compile(r"attendance", re.I))
    if not table:
        table = soup.find("table", id=re.compile(r"attendance", re.I))

    if not table:
        return records

    # Find all table rows in tbody
    tbody = table.find("tbody")
    if not tbody:
        return records

    rows = tbody.find_all("tr")

    for row in rows:
        cells = row.find_all("td")
        # Skip header-like rows
        if not cells or len(cells) < 2:
            continue

        # Skip week label cell
        for cell in cells[1:]:  # Skip first cell (week label)
            date_str = cell.get("data-date", "")
            if not date_str:
                continue

            parsed_date = parse_attendance_date(date_str)
            if not parsed_date:
                continue

            code_elem = cell.find("span", class_="code")
            code = code_elem.get_text(strip=True) if code_elem else cell.get_text(strip=True)
            cell_class = " ".join(cell.get("class", []))

            status = normalize_attendance_status(code, cell_class)
            records.append({"date": parsed_date, "status": status, "code": code})

    return records


def normalize_attendance_status(code: str, css_class: str = "") -> str:
    """Normalize attendance status from code and CSS class.

    Args:
        code: Attendance code (., A, T, E, P, etc.)
        css_class: CSS class string from the element

    Returns:
        Normalized status string: Present, Absent, Tardy, Excused, or Unknown
    """
    code = (code or "").strip().upper()
    css_class = (css_class or "").lower()

    # Check CSS class first (more reliable)
    if "present" in css_class:
        return "Present"
    if "absent" in css_class:
        return "Absent"
    if "tardy" in css_class:
        return "Tardy"
    if "excused" in css_class:
        return "Excused"

    # Check code
    if code in (".", "P", "PRESENT"):
        return "Present"
    if code in ("A", "ABSENT"):
        return "Absent"
    if code in ("T", "TARDY"):
        return "Tardy"
    if code in ("E", "EX", "EXCUSED"):
        return "Excused"

    # Default to Unknown
    return "Unknown"


def parse_attendance_date(date_str: Optional[str]) -> Optional[str]:
    """Parse various date formats into ISO format (YYYY-MM-DD).

    Args:
        date_str: Date string in various formats

    Returns:
        Date in YYYY-MM-DD format, or None if invalid
    """
    if not date_str:
        return None

    date_str = date_str.strip()

    # Common date formats to try
    formats = [
        "%Y-%m-%d",  # ISO: 2024-12-15
        "%m/%d/%Y",  # US: 12/15/2024
        "%m/%d/%y",  # US short: 12/15/24
        "%d/%m/%Y",  # EU: 15/12/2024
        "%B %d, %Y",  # Full: December 15, 2024
        "%b %d, %Y",  # Short: Dec 15, 2024
    ]

    for fmt in formats:
        try:
            parsed = datetime.strptime(date_str, fmt)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return None


def detect_attendance_patterns(records: List[Dict[str, str]]) -> Dict:
    """Detect attendance patterns from daily records.

    Analyzes attendance records to identify:
    - Day of week patterns (e.g., "frequently absent on Mondays")
    - Absence streaks
    - Overall statistics

    Args:
        records: List of attendance records from parse_daily_attendance()

    Returns:
        Dictionary containing:
            - by_day_of_week: Dict mapping day names to counts
            - longest_absence_streak: Max consecutive absent days
            - total_present: Count of present days
            - total_absent: Count of absent days
            - total_tardy: Count of tardy days
            - attendance_rate: Percentage attendance
    """
    result = {
        "by_day_of_week": {
            "Monday": {
                "absence_count": 0,
                "tardy_count": 0,
                "present_count": 0,
                "total_records": 0,
            },
            "Tuesday": {
                "absence_count": 0,
                "tardy_count": 0,
                "present_count": 0,
                "total_records": 0,
            },
            "Wednesday": {
                "absence_count": 0,
                "tardy_count": 0,
                "present_count": 0,
                "total_records": 0,
            },
            "Thursday": {
                "absence_count": 0,
                "tardy_count": 0,
                "present_count": 0,
                "total_records": 0,
            },
            "Friday": {
                "absence_count": 0,
                "tardy_count": 0,
                "present_count": 0,
                "total_records": 0,
            },
            "Saturday": {
                "absence_count": 0,
                "tardy_count": 0,
                "present_count": 0,
                "total_records": 0,
            },
            "Sunday": {
                "absence_count": 0,
                "tardy_count": 0,
                "present_count": 0,
                "total_records": 0,
            },
        },
        "longest_absence_streak": 0,
        "total_present": 0,
        "total_absent": 0,
        "total_tardy": 0,
        "total_excused": 0,
        "attendance_rate": 100.0,
    }

    if not records:
        return result

    # Sort records by date for streak detection
    sorted_records = sorted(records, key=lambda r: r.get("date", ""))

    current_streak = 0
    max_streak = 0

    for record in sorted_records:
        status = record.get("status", "Unknown")
        date_str = record.get("date", "")

        # Count by status
        if status == "Present":
            result["total_present"] += 1
            current_streak = 0
        elif status == "Absent":
            result["total_absent"] += 1
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        elif status == "Tardy":
            result["total_tardy"] += 1
            current_streak = 0
        elif status == "Excused":
            result["total_excused"] += 1
            current_streak = 0
        else:
            current_streak = 0

        # Count by day of week
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                day_name = date_obj.strftime("%A")

                if day_name in result["by_day_of_week"]:
                    result["by_day_of_week"][day_name]["total_records"] += 1
                    if status == "Absent":
                        result["by_day_of_week"][day_name]["absence_count"] += 1
                    elif status == "Tardy":
                        result["by_day_of_week"][day_name]["tardy_count"] += 1
                    elif status == "Present":
                        result["by_day_of_week"][day_name]["present_count"] += 1
            except ValueError:
                pass

    result["longest_absence_streak"] = max_streak

    # Calculate attendance rate (Present / (Present + Absent + Tardy))
    total = result["total_present"] + result["total_absent"] + result["total_tardy"]
    if total > 0:
        # Consider both present and tardy as "attended"
        attended = result["total_present"] + result["total_tardy"]
        result["attendance_rate"] = round(100.0 * attended / total, 1)

    return result


def format_patterns_for_display(patterns: Dict) -> str:
    """Format attendance patterns into human-readable text.

    Args:
        patterns: Result from detect_attendance_patterns()

    Returns:
        Formatted string for display
    """
    lines = []

    # Overall stats
    lines.append("## Attendance Statistics")
    lines.append(f"- Days Present: {patterns['total_present']}")
    lines.append(f"- Days Absent: {patterns['total_absent']}")
    lines.append(f"- Days Tardy: {patterns['total_tardy']}")
    lines.append(f"- Days Excused: {patterns['total_excused']}")
    lines.append(f"- Attendance Rate: {patterns['attendance_rate']}%")
    lines.append("")

    # Absence streaks
    if patterns["longest_absence_streak"] > 1:
        lines.append(f"**Longest Absence Streak**: {patterns['longest_absence_streak']} days")
        lines.append("")

    # Day of week patterns
    problem_days = []
    for day_name, counts in patterns["by_day_of_week"].items():
        if counts["total_records"] > 0:
            absence_rate = counts["absence_count"] / counts["total_records"]
            if absence_rate >= 0.3:  # 30% or more absence rate
                problem_days.append(
                    (day_name, counts["absence_count"], counts["total_records"], absence_rate)
                )

    if problem_days:
        lines.append("## Concerning Patterns")
        for day, absences, total, rate in sorted(problem_days, key=lambda x: -x[3]):
            lines.append(
                f"- Frequently absent on **{day}**: {absences}/{total} ({rate * 100:.0f}%)"
            )
        lines.append("")

    return "\n".join(lines)
