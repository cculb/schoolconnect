"""Parser for PowerSchool course score detail pages.

This module parses the scores.html page which contains:
- Category weights (e.g., Formative 30%, Summative 70%)
- Detailed assignment information including descriptions, standards, and comments
- Full assignment breakdown with calculated scores

Example page URL: /guardian/scores.html?frn=...
"""

from typing import Any, Optional

from bs4 import BeautifulSoup


def parse_weight(weight_str: Optional[str]) -> Optional[float]:
    """Parse a weight string (e.g., "30%") into a float.

    Args:
        weight_str: Weight string like "30%", "30", or "  30%  "

    Returns:
        Float value (e.g., 30.0) or None if invalid
    """
    if not weight_str:
        return None

    weight_str = weight_str.strip()
    if not weight_str or weight_str in ("--", "N/A", ""):
        return None

    # Remove % sign and parse
    weight_str = weight_str.replace("%", "").strip()

    try:
        return float(weight_str)
    except ValueError:
        return None


def parse_score(score_str: Optional[str]) -> tuple[Optional[float], Optional[float]]:
    """Parse a score string (e.g., "17/20") into earned and possible points.

    Args:
        score_str: Score string like "17/20", "/10", "--", or empty

    Returns:
        Tuple of (points_earned, points_possible), with None for missing values
    """
    if not score_str:
        return None, None

    score_str = score_str.strip()
    if not score_str or score_str == "--":
        return None, None

    # Handle fraction format: "17/20", "/10", etc.
    if "/" in score_str:
        parts = score_str.split("/")
        earned = None
        possible = None

        if len(parts) >= 2:
            # Get earned points (before /)
            if parts[0].strip():
                try:
                    earned = float(parts[0].strip())
                except ValueError:
                    pass

            # Get possible points (after /)
            if parts[1].strip():
                try:
                    possible = float(parts[1].strip())
                except ValueError:
                    pass

        return earned, possible

    # Try to parse as single number
    try:
        return float(score_str), None
    except ValueError:
        return None, None


def parse_percent(percent_str: Optional[str]) -> Optional[float]:
    """Parse a percentage string (e.g., "85%") into a float.

    Args:
        percent_str: Percentage string like "85%", "85", or empty

    Returns:
        Float value (e.g., 85.0) or None if invalid
    """
    if not percent_str:
        return None

    percent_str = percent_str.strip()
    if not percent_str or percent_str in ("--", "N/A", ""):
        return None

    # Remove % sign and parse
    percent_str = percent_str.replace("%", "").strip()

    try:
        return float(percent_str)
    except ValueError:
        return None


def parse_standards(standards_str: Optional[str]) -> list[str]:
    """Parse a standards string into a list of standards.

    Args:
        standards_str: Comma-separated standards like "6.NS.1, 6.NS.2"

    Returns:
        List of standard strings, or empty list if none
    """
    if not standards_str:
        return []

    standards_str = standards_str.strip()
    if not standards_str:
        return []

    # Split by comma and clean up
    standards = [s.strip() for s in standards_str.split(",")]
    return [s for s in standards if s]  # Filter empty strings


def _extract_text(element: Any, default: str = "") -> str:
    """Safely extract text from a BeautifulSoup element.

    Args:
        element: BeautifulSoup element or None
        default: Default value if element is None

    Returns:
        Stripped text content or default
    """
    if element is None:
        return default
    return element.get_text(strip=True)


def _find_by_class(row: Any, class_name: str) -> Optional[str]:
    """Find element by class and extract text.

    Args:
        row: BeautifulSoup row element
        class_name: CSS class to find

    Returns:
        Text content or None
    """
    element = row.find(class_=class_name)
    if element:
        return element.get_text(strip=True)
    return None


def parse_course_scores(html: str) -> dict[str, Any]:
    """Parse a PowerSchool course scores page.

    Extracts:
    - Course name and teacher
    - Category weights with points
    - Assignments with details (description, standards, comments)

    Args:
        html: Raw HTML content of the scores page

    Returns:
        Dictionary with keys:
        - course_name: str
        - teacher_name: str
        - categories: list of dicts with name, weight, points_earned, points_possible
        - assignments: list of dicts with name, category, score, details, etc.
    """
    if not html:
        return {"course_name": "", "teacher_name": "", "categories": [], "assignments": []}

    soup = BeautifulSoup(html, "html.parser")

    # Extract course name from h2 in box-round
    course_name = ""
    course_heading = soup.find("h2")
    if course_heading:
        course_name = course_heading.get_text(strip=True)

    # Extract teacher name
    teacher_name = ""
    teacher_elem = soup.find(class_="teacher") or soup.find(class_="teacher-info")
    if teacher_elem:
        teacher_name = teacher_elem.get_text(strip=True)

    # Parse category weights
    categories = _parse_categories(soup)

    # Parse assignments
    assignments = _parse_assignments(soup)

    return {
        "course_name": course_name,
        "teacher_name": teacher_name,
        "categories": categories,
        "assignments": assignments,
    }


def _parse_categories(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """Parse category weights from the page.

    Args:
        soup: BeautifulSoup object of the page

    Returns:
        List of category dictionaries
    """
    categories = []

    # Look for category weights section
    weights_section = soup.find(class_="category-weights")
    if not weights_section:
        # Try alternative: look for a table with weight column
        weight_tables = soup.find_all("table")
        for table in weight_tables:
            headers = table.find_all("th")
            header_texts = [h.get_text(strip=True).lower() for h in headers]
            if "weight" in header_texts:
                weights_section = table
                break

    if not weights_section:
        return categories

    # Parse rows in the weights table
    rows = weights_section.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        if not cells:
            continue

        # Try to extract category info
        # Look for class-based extraction first
        cat_name = _find_by_class(row, "category-name")
        weight_str = _find_by_class(row, "weight")
        points_earned_str = _find_by_class(row, "points-earned")
        points_possible_str = _find_by_class(row, "points-possible")

        # Fallback to positional extraction
        if not cat_name and len(cells) >= 2:
            cat_name = cells[0].get_text(strip=True)
            weight_str = cells[1].get_text(strip=True)
            if len(cells) >= 3:
                points_earned_str = cells[2].get_text(strip=True)
            if len(cells) >= 4:
                points_possible_str = cells[3].get_text(strip=True)

        if cat_name:
            weight = parse_weight(weight_str) if weight_str else None

            # Parse points
            points_earned = None
            points_possible = None
            if points_earned_str:
                try:
                    points_earned = float(points_earned_str)
                except ValueError:
                    pass
            if points_possible_str:
                try:
                    points_possible = float(points_possible_str)
                except ValueError:
                    pass

            categories.append(
                {
                    "name": cat_name,
                    "weight": weight,
                    "points_earned": points_earned,
                    "points_possible": points_possible,
                }
            )

    return categories


def _parse_assignments(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """Parse assignments from the page.

    Args:
        soup: BeautifulSoup object of the page

    Returns:
        List of assignment dictionaries
    """
    assignments = []

    # Find assignments table (usually has id="scoreTable")
    score_table = soup.find(id="scoreTable")
    if not score_table:
        # Try finding by class
        score_table = soup.find(class_="assignments-detail")
        if score_table:
            score_table = score_table.find("table")

    if not score_table:
        # Last resort: look for table with assignment headers
        tables = soup.find_all("table")
        for table in tables:
            headers = table.find_all("th")
            header_texts = [h.get_text(strip=True).lower() for h in headers]
            if "assignment" in header_texts or "score" in header_texts:
                score_table = table
                break

    if not score_table:
        return assignments

    # Parse assignment rows
    rows = score_table.find_all("tr", class_="assignment-row")
    if not rows:
        # Fallback: get all tr except header
        rows = score_table.find_all("tr")
        rows = [r for r in rows if r.find("td")]  # Skip header rows

    for row in rows:
        assignment = _parse_assignment_row(row)
        if assignment:
            assignments.append(assignment)

    return assignments


def _parse_assignment_row(row: Any) -> Optional[dict[str, Any]]:
    """Parse a single assignment row.

    Args:
        row: BeautifulSoup row element

    Returns:
        Assignment dictionary or None if not a valid assignment row
    """
    cells = row.find_all("td")
    if not cells:
        return None

    # Try class-based extraction
    name_cell = row.find(class_="assignment-name")
    due_date = _find_by_class(row, "due-date")
    category = _find_by_class(row, "category")
    score_str = _find_by_class(row, "score")
    percent_str = _find_by_class(row, "percent")
    letter_grade = _find_by_class(row, "letter-grade")
    codes = _find_by_class(row, "codes")

    # Extract assignment name
    name = ""
    if name_cell:
        # Get the main link text or first text
        link = name_cell.find("a")
        if link:
            name = link.get_text(strip=True)
        else:
            name = name_cell.get_text(strip=True)
    elif len(cells) >= 1:
        name = cells[0].get_text(strip=True)

    if not name:
        return None

    # Parse score
    score = score_str if score_str else None

    # Parse percent
    percent = parse_percent(percent_str)

    # Extract details (description, standards, comments)
    description = ""
    standards = ""
    comments = ""

    if name_cell:
        detail_div = name_cell.find(class_="assignment-detail")
        if detail_div:
            desc_elem = detail_div.find(class_="description")
            if desc_elem:
                description = desc_elem.get_text(strip=True)

            std_elem = detail_div.find(class_="standards")
            if std_elem:
                standards = std_elem.get_text(strip=True)

            comment_elem = detail_div.find(class_="comments")
            if comment_elem:
                comments = comment_elem.get_text(strip=True)

    return {
        "name": name,
        "due_date": due_date or "",
        "category": category or "",
        "score": score,
        "percent": percent,
        "letter_grade": letter_grade or "",
        "codes": codes or "",
        "description": description,
        "standards": standards,
        "comments": comments,
    }
