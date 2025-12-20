"""Parser for PowerSchool attendance pages."""

from datetime import date, datetime
from typing import Any

from bs4 import BeautifulSoup


def parse_attendance_page(html: str) -> list[dict[str, Any]]:
    """Parse an attendance detail page showing daily attendance records.

    Args:
        html: Raw HTML content from the attendance page

    Returns:
        List of attendance records
    """
    soup = BeautifulSoup(html, "html.parser")
    records = []

    # Find attendance table
    table = soup.find("table", class_=lambda c: c and "attendance" in c.lower())
    if not table:
        tables = soup.find_all("table")
        for t in tables:
            headers = t.find_all("th")
            header_text = " ".join(h.get_text() for h in headers).lower()
            if "date" in header_text and ("status" in header_text or "code" in header_text):
                table = t
                break

    if not table:
        return records

    rows = table.find_all("tr")
    for row in rows[1:]:  # Skip header
        cols = row.find_all("td")
        if len(cols) >= 2:
            try:
                record = {
                    "date": _parse_date(cols[0].get_text(strip=True)),
                    "status": _parse_attendance_status(cols[1]),
                    "code": cols[1].get_text(strip=True),
                    "period": None,
                    "course": None,
                }

                # Check for period-level attendance
                if len(cols) >= 3:
                    record["period"] = cols[2].get_text(strip=True)
                if len(cols) >= 4:
                    record["course"] = cols[3].get_text(strip=True)

                if record["date"]:
                    records.append(record)

            except (IndexError, ValueError):
                continue

    return records


def parse_attendance_dashboard(html: str) -> dict[str, Any]:
    """Parse the attendance analytics dashboard.

    This is typically the mba_attendance_monitor/guardian_dashboard.html page
    which shows attendance rate, charts, and detailed breakdowns.

    Args:
        html: Raw HTML content from the attendance dashboard

    Returns:
        Dictionary with attendance summary data
    """
    soup = BeautifulSoup(html, "html.parser")

    result = {
        "attendance_rate": None,
        "days_enrolled": None,
        "days_present": None,
        "days_absent": None,
        "days_absent_excused": None,
        "days_absent_unexcused": None,
        "tardies": None,
        "tardies_excused": None,
        "tardies_unexcused": None,
    }

    # Look for attendance rate (often prominently displayed)
    rate_elem = soup.find(class_=lambda c: c and "rate" in c.lower())
    if rate_elem:
        rate_text = rate_elem.get_text(strip=True)
        result["attendance_rate"] = _parse_percent(rate_text)

    # Alternative: look for percentage in large text
    if result["attendance_rate"] is None:
        for elem in soup.find_all(["span", "div", "h1", "h2", "h3"]):
            text = elem.get_text(strip=True)
            if "%" in text:
                pct = _parse_percent(text)
                if pct and 50 <= pct <= 100:  # Reasonable attendance range
                    result["attendance_rate"] = pct
                    break

    # Look for summary statistics
    # These are often in a summary table or stat blocks
    stat_table = soup.find("table", class_=lambda c: c and "summary" in c.lower())
    if stat_table:
        rows = stat_table.find_all("tr")
        for row in rows:
            cols = row.find_all(["td", "th"])
            if len(cols) >= 2:
                label = cols[0].get_text(strip=True).lower()
                value = cols[1].get_text(strip=True)

                if "enrolled" in label:
                    result["days_enrolled"] = _parse_int(value)
                elif "present" in label:
                    result["days_present"] = _parse_int(value)
                elif "absent" in label and "excused" not in label and "unexcused" not in label:
                    result["days_absent"] = _parse_int(value)
                elif "excused" in label and "absent" in label:
                    result["days_absent_excused"] = _parse_int(value)
                elif "unexcused" in label and "absent" in label:
                    result["days_absent_unexcused"] = _parse_int(value)
                elif "tardy" in label or "tardie" in label:
                    if "excused" in label:
                        result["tardies_excused"] = _parse_int(value)
                    elif "unexcused" in label:
                        result["tardies_unexcused"] = _parse_int(value)
                    else:
                        result["tardies"] = _parse_int(value)

    # Also look for stat blocks/cards
    stat_blocks = soup.find_all(class_=lambda c: c and ("stat" in c.lower() or "metric" in c.lower()))
    for block in stat_blocks:
        label = ""
        value = ""

        label_elem = block.find(class_=lambda c: c and "label" in c.lower())
        if label_elem:
            label = label_elem.get_text(strip=True).lower()

        value_elem = block.find(class_=lambda c: c and "value" in c.lower())
        if value_elem:
            value = value_elem.get_text(strip=True)

        if not label:
            text = block.get_text(strip=True).lower()
            label = text

        if "present" in label:
            result["days_present"] = _parse_int(value) or _extract_number(label)
        elif "absent" in label:
            result["days_absent"] = _parse_int(value) or _extract_number(label)
        elif "tardy" in label:
            result["tardies"] = _parse_int(value) or _extract_number(label)

    return result


def _parse_date(text: str) -> date | None:
    """Parse a date string."""
    if not text:
        return None

    formats = [
        "%m/%d/%Y",
        "%m/%d/%y",
        "%Y-%m-%d",
        "%m-%d-%Y",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %b %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(text.strip(), fmt).date()
        except ValueError:
            continue

    return None


def _parse_attendance_status(element) -> str:
    """Determine attendance status from cell content."""
    text = element.get_text(strip=True).upper()

    # Map common codes
    code_map = {
        "P": "Present",
        "A": "Absent",
        "T": "Tardy",
        "E": "Excused",
        "U": "Unexcused",
        "AE": "Absent Excused",
        "AU": "Absent Unexcused",
        "TE": "Tardy Excused",
        "TU": "Tardy Unexcused",
    }

    if text in code_map:
        return code_map[text]

    # Check for class-based indicators
    classes = " ".join(element.get("class", [])).lower()
    if "present" in classes:
        return "Present"
    if "absent" in classes:
        return "Absent"
    if "tardy" in classes:
        return "Tardy"

    # Check for color indicators
    style = element.get("style", "").lower()
    if "green" in style:
        return "Present"
    if "red" in style:
        return "Absent"
    if "yellow" in style or "orange" in style:
        return "Tardy"

    return "Unknown"


def _parse_percent(text: str) -> float | None:
    """Parse a percentage string."""
    if not text:
        return None

    # Extract number from text like "88.60%" or "Attendance: 88.60%"
    import re
    match = re.search(r"(\d+\.?\d*)%?", text)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass

    return None


def _parse_int(text: str) -> int | None:
    """Parse an integer string."""
    if not text:
        return None

    # Extract first number from text
    import re
    match = re.search(r"(\d+)", text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass

    return None


def _extract_number(text: str) -> int | None:
    """Extract a number from text."""
    import re
    match = re.search(r"(\d+)", text)
    if match:
        return int(match.group(1))
    return None
