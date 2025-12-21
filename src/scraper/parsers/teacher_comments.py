"""Parser for PowerSchool teacher comments HTML page.

This module parses the teacher comments page (/guardian/teachercomments.html)
which displays teacher comments organized by course for a specific term.

The HTML structure consists of a table with columns:
- Exp. (Expression/Period)
- Course #
- Course
- Teacher (with email link)
- Comment (in a <pre> tag)
"""

import re
from typing import Dict, List, Optional

from bs4 import BeautifulSoup


def parse_teacher_comments(
    html: str,
    comments_only: bool = False,
) -> List[Dict[str, Optional[str]]]:
    """Parse teacher comments from PowerSchool HTML.

    Args:
        html: Raw HTML from the teacher comments page.
        comments_only: If True, only return entries with non-empty comments.
                      If False (default), return all courses including those
                      without comments.

    Returns:
        List of dictionaries, each containing:
            - expression: Period/block expression (e.g., "1/6(A-B)")
            - course_number: Course number (e.g., "54436")
            - course_name: Name of the course
            - teacher_name: Teacher's name (extracted from email link)
            - teacher_email: Teacher's email address
            - comment: The actual comment text (may be empty string)

    Example:
        >>> html = '<table class="grid linkDescList">...</table>'
        >>> comments = parse_teacher_comments(html)
        >>> for c in comments:
        ...     print(f"{c['course_name']}: {c['comment']}")
    """
    if not html or not html.strip():
        return []

    soup = BeautifulSoup(html, "html.parser")

    # Find the teacher comments table
    table = soup.find("table", class_="grid")
    if not table:
        # Try alternative selectors
        table = soup.find("table", class_="linkDescList")
    if not table:
        return []

    results: List[Dict[str, Optional[str]]] = []

    # Find all data rows (skip header row)
    rows = table.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 5:
            # Not a data row (header or incomplete)
            continue

        # Extract data from each cell
        expression = _extract_text(cells[0])
        course_number = _extract_text(cells[1])
        course_name = _extract_text(cells[2])

        # Teacher cell contains email link
        teacher_name, teacher_email = _extract_teacher_info(cells[3])

        # Comment is in a <pre> tag in the last cell
        comment = _extract_comment(cells[4])

        # Build the result dictionary
        entry = {
            "expression": expression,
            "course_number": course_number,
            "course_name": course_name,
            "teacher_name": teacher_name,
            "teacher_email": teacher_email,
            "comment": comment,
        }

        # Filter based on comments_only flag
        if comments_only:
            if comment and comment.strip():
                results.append(entry)
        else:
            results.append(entry)

    return results


def _extract_text(cell) -> str:
    """Extract and clean text content from a table cell.

    Args:
        cell: BeautifulSoup Tag object for a table cell.

    Returns:
        Cleaned text content, stripped of whitespace.
    """
    if cell is None:
        return ""

    # Get text content, handling nested elements
    text = cell.get_text(strip=True)

    # Remove HTML comments (like <!-- 3501 161117 -->)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    return text.strip()


def _extract_teacher_info(cell) -> tuple:
    """Extract teacher name and email from the teacher cell.

    The cell typically contains:
    - An optional info button link with title containing teacher name
    - An email link with "Email Teacher, Name" text

    Args:
        cell: BeautifulSoup Tag object for the teacher cell.

    Returns:
        Tuple of (teacher_name, teacher_email).
    """
    teacher_name = ""
    teacher_email = ""

    if cell is None:
        return teacher_name, teacher_email

    # Look for email link first
    email_link = cell.find("a", href=lambda x: x and x.startswith("mailto:"))
    if email_link:
        # Extract email from href
        href = email_link.get("href", "")
        if href.startswith("mailto:"):
            teacher_email = href.replace("mailto:", "").strip()

        # Extract name from link text (format: "Email Teacher, Name")
        link_text = email_link.get_text(strip=True)
        if link_text.startswith("Email "):
            teacher_name = link_text[6:].strip()  # Remove "Email " prefix

    # Also check for info button with title attribute
    if not teacher_name:
        info_link = cell.find("a", title=True)
        if info_link:
            title = info_link.get("title", "")
            # Title format: "Details about Teacher, Name"
            if "Details about" in title:
                teacher_name = title.replace("Details about", "").strip()

    return teacher_name, teacher_email


def _extract_comment(cell) -> str:
    """Extract comment text from the comment cell.

    Comments are typically wrapped in a <pre> tag.

    Args:
        cell: BeautifulSoup Tag object for the comment cell.

    Returns:
        The comment text, stripped of whitespace.
    """
    if cell is None:
        return ""

    # Look for <pre> tag
    pre_tag = cell.find("pre")
    if pre_tag:
        return pre_tag.get_text(strip=True)

    # Fallback to cell text
    return cell.get_text(strip=True)


def get_student_name_from_html(html: str) -> Optional[str]:
    """Extract student name from the page header.

    The page title/header typically contains:
    "Teacher Comments: LastName, FirstName MiddleName"

    Args:
        html: Raw HTML from the teacher comments page.

    Returns:
        Student name if found, None otherwise.
    """
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    # Try h1 tag first
    h1 = soup.find("h1")
    if h1:
        text = h1.get_text(strip=True)
        if "Teacher Comments:" in text:
            return text.replace("Teacher Comments:", "").strip()

    # Try title tag
    title = soup.find("title")
    if title:
        text = title.get_text(strip=True)
        if "Teacher Comments" in text:
            # Title might just be "Teacher Comments"
            return None

    return None
