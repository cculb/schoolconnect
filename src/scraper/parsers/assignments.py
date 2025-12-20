"""Parser for PowerSchool assignments page."""

from datetime import date, datetime
from typing import Any

from bs4 import BeautifulSoup


def parse_assignments_page(html: str) -> list[dict[str, Any]]:
    """Parse the Class Assignments Summary page.

    Expected table structure:
    - Teacher, Course, Term, Due Date, Category, Assignment Name,
      Score, Percent, Letter Grade, Codes

    Args:
        html: Raw HTML content from the assignments page

    Returns:
        List of assignment dictionaries
    """
    soup = BeautifulSoup(html, "html.parser")
    assignments = []

    # Find the main assignment table
    # PowerSchool typically uses class "linkDescList" or similar
    table = soup.find("table", class_="linkDescList")
    if not table:
        # Try alternative selectors
        table = soup.find("table", id="assignments-table")
    if not table:
        # Look for any table with assignment-like headers
        tables = soup.find_all("table")
        for t in tables:
            headers = t.find_all("th")
            header_text = " ".join(h.get_text() for h in headers).lower()
            if "assignment" in header_text or "due date" in header_text:
                table = t
                break

    if not table:
        return assignments

    rows = table.find_all("tr")
    if not rows:
        return assignments

    # Skip header row
    for row in rows[1:]:
        cols = row.find_all("td")
        if len(cols) < 6:
            continue

        try:
            assignment = {
                "teacher": _clean_text(cols[0]),
                "course": _clean_text(cols[1]),
                "term": _clean_text(cols[2]),
                "due_date": _parse_date(cols[3]),
                "category": _clean_text(cols[4]),
                "assignment_name": _clean_text(cols[5]),
                "score": None,
                "max_score": None,
                "percent": None,
                "letter_grade": None,
                "status": "Unknown",
            }

            # Parse score if available (column 6)
            if len(cols) > 6:
                score_text = _clean_text(cols[6])
                assignment["score"], assignment["max_score"] = _parse_score(score_text)

            # Parse percent if available (column 7)
            if len(cols) > 7:
                assignment["percent"] = _parse_percent(cols[7])

            # Parse letter grade if available (column 8)
            if len(cols) > 8:
                assignment["letter_grade"] = _clean_text(cols[8])

            # Parse status from codes column (column 9)
            if len(cols) > 9:
                assignment["status"] = _parse_status(cols[9])

            assignments.append(assignment)

        except Exception:
            # Skip malformed rows
            continue

    return assignments


def _clean_text(element) -> str:
    """Extract and clean text from an element."""
    if element is None:
        return ""
    return element.get_text(strip=True)


def _parse_date(element) -> date | None:
    """Parse a date from an element."""
    text = _clean_text(element)
    if not text:
        return None

    # Try common date formats
    formats = [
        "%m/%d/%Y",
        "%m/%d/%y",
        "%Y-%m-%d",
        "%m-%d-%Y",
        "%B %d, %Y",
        "%b %d, %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    return None


def _parse_score(text: str) -> tuple[float | None, float | None]:
    """Parse a score like '8/10' or '85' into (score, max_score)."""
    if not text:
        return None, None

    # Handle "score/max" format
    if "/" in text:
        parts = text.split("/")
        try:
            score = float(parts[0].strip())
            max_score = float(parts[1].strip())
            return score, max_score
        except (ValueError, IndexError):
            pass

    # Handle standalone score
    try:
        return float(text), None
    except ValueError:
        return None, None


def _parse_percent(element) -> float | None:
    """Parse a percentage from an element."""
    text = _clean_text(element)
    if not text:
        return None

    # Remove % sign and convert
    text = text.replace("%", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def _parse_status(element) -> str:
    """Parse the status/codes column to determine assignment status."""
    # Check for specific icons or images
    if element.find("img", alt="Collected"):
        return "Collected"
    if element.find("img", alt="Missing"):
        return "Missing"
    if element.find("img", alt="Late"):
        return "Late"
    if element.find("img", alt="Exempt"):
        return "Exempt"

    # Check for status-indicating classes
    classes = element.get("class", [])
    class_str = " ".join(classes).lower()
    if "missing" in class_str:
        return "Missing"
    if "collected" in class_str:
        return "Collected"
    if "late" in class_str:
        return "Late"

    # Check for text content
    text = _clean_text(element).lower()
    if "missing" in text:
        return "Missing"
    if "collected" in text or "complete" in text:
        return "Collected"
    if "late" in text:
        return "Late"
    if "exempt" in text:
        return "Exempt"

    # Check for colored icons (red = missing, green = collected)
    red_icon = element.find(["i", "span"], class_=lambda c: c and "red" in c.lower())
    if red_icon:
        return "Missing"

    green_icon = element.find(["i", "span"], class_=lambda c: c and "green" in c.lower())
    if green_icon:
        return "Collected"

    return "Unknown"
