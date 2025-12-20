#!/usr/bin/env python3
"""
Reconnaissance script for PowerSchool Parent Portal.
Logs in and saves raw HTML from all important pages.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bs4 import BeautifulSoup
from playwright.sync_api import Page, sync_playwright

from src.scraper.auth import get_base_url, get_credentials, login

# Configuration
BASE_URL = get_base_url()

# Pages to scrape
PAGES = {
    "home": "/guardian/home.html",
    "assignments": "/guardian/classassignments.html",
    "schedule": "/guardian/myschedule.html",
    "comments_q1": "/guardian/teachercomments.html?fg=Q1",
    "comments_q2": "/guardian/teachercomments.html?fg=Q2",
    "attendance": "/guardian/mba_attendance_monitor/guardian_dashboard.html",
}

# Output directory
RAW_HTML_DIR = Path(__file__).parent.parent / "raw_html"
RAW_HTML_DIR.mkdir(exist_ok=True)


def save_page_html(page: Page, name: str, url_path: str) -> str:
    """Navigate to a page and save its HTML."""
    full_url = f"{BASE_URL}{url_path}"
    print(f"\nFetching {name}: {full_url}")

    try:
        page.goto(full_url, wait_until="networkidle", timeout=30000)

        # Wait a bit for dynamic content
        page.wait_for_timeout(2000)

        # Get HTML content
        html = page.content()

        # Save to file
        output_file = RAW_HTML_DIR / f"{name}.html"
        output_file.write_text(html, encoding="utf-8")
        print(f"  Saved to {output_file} ({len(html):,} bytes)")

        return html
    except Exception as e:
        print(f"  Error fetching {name}: {e}")
        return ""


def extract_student_info(html: str) -> dict:
    """Extract student information from the home page."""
    soup = BeautifulSoup(html, "lxml")
    info = {}

    # Try to find student name
    student_name = soup.select_one("#student-name, .student-name, .studentName")
    if student_name:
        info["student_name"] = student_name.get_text(strip=True)

    # Try header area
    header = soup.select_one(".header-student-info, #header-student")
    if header:
        info["header_text"] = header.get_text(strip=True)[:200]

    return info


def extract_grades_preview(html: str) -> list:
    """Extract grade information from home page."""
    soup = BeautifulSoup(html, "lxml")
    grades = []

    # Look for grade tables
    tables = soup.select("table")
    for table in tables:
        rows = table.select("tr")
        for row in rows:
            cells = row.select("td, th")
            if cells:
                row_data = [cell.get_text(strip=True) for cell in cells]
                if row_data and any(row_data):
                    grades.append(row_data)

    return grades[:20]  # First 20 rows for preview


def extract_assignments_preview(html: str) -> list:
    """Extract assignment information."""
    soup = BeautifulSoup(html, "lxml")
    assignments = []

    # Look for assignment tables or lists
    tables = soup.select("table")
    for table in tables:
        rows = table.select("tr")
        for row in rows:
            cells = row.select("td, th")
            if cells:
                row_data = [cell.get_text(strip=True) for cell in cells]
                if row_data and any(row_data):
                    assignments.append(row_data)

    return assignments[:30]  # First 30 rows


def analyze_page_structure(html: str, name: str) -> dict:
    """Analyze the HTML structure of a page."""
    soup = BeautifulSoup(html, "lxml")

    analysis = {
        "page": name,
        "tables": [],
        "forms": [],
        "key_elements": [],
    }

    # Analyze tables
    tables = soup.select("table")
    for i, table in enumerate(tables):
        table_info = {
            "index": i,
            "id": table.get("id", ""),
            "class": table.get("class", []),
            "rows": len(table.select("tr")),
            "headers": [th.get_text(strip=True) for th in table.select("th")][:10],
        }
        analysis["tables"].append(table_info)

    # Analyze forms
    forms = soup.select("form")
    for form in forms:
        form_info = {
            "id": form.get("id", ""),
            "action": form.get("action", ""),
            "inputs": [inp.get("name", "") for inp in form.select("input")],
        }
        analysis["forms"].append(form_info)

    # Find key elements by common IDs/classes
    key_selectors = [
        "#grades-table", ".grades", "#assignments", ".assignment",
        "#attendance", ".attendance", "#schedule", ".schedule",
        ".student-info", "#student-name", ".course", ".class"
    ]
    for selector in key_selectors:
        elements = soup.select(selector)
        if elements:
            analysis["key_elements"].append({
                "selector": selector,
                "count": len(elements),
                "sample_text": elements[0].get_text(strip=True)[:100] if elements else ""
            })

    return analysis


def run_recon():
    """Main reconnaissance function."""
    print("=" * 60)
    print("PowerSchool Reconnaissance Script")
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)

    try:
        get_credentials()  # Validate credentials are available
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    with sync_playwright() as p:
        # Launch browser in headed mode for visual confirmation
        print("\nLaunching browser (headed mode)...")
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = context.new_page()

        # Login
        if not login(page):
            print("\nLogin failed. Exiting.")
            browser.close()
            sys.exit(1)

        # Save HTML from each page
        all_html = {}
        all_analysis = {}

        for name, url_path in PAGES.items():
            html = save_page_html(page, name, url_path)
            if html:
                all_html[name] = html
                all_analysis[name] = analyze_page_structure(html, name)

        # Close browser
        print("\nClosing browser...")
        browser.close()

    # Save analysis results
    analysis_file = RAW_HTML_DIR / "analysis.json"
    with open(analysis_file, "w") as f:
        json.dump(all_analysis, f, indent=2)
    print(f"\nSaved structure analysis to {analysis_file}")

    # Print summary
    print("\n" + "=" * 60)
    print("RECONNAISSANCE SUMMARY")
    print("=" * 60)

    for name, analysis in all_analysis.items():
        print(f"\n{name.upper()}:")
        print(f"  Tables: {len(analysis['tables'])}")
        for table in analysis["tables"][:3]:
            print(f"    - id='{table['id']}' class={table['class']} rows={table['rows']}")
            if table["headers"]:
                print(f"      headers: {table['headers']}")

        if analysis["key_elements"]:
            print("  Key elements found:")
            for elem in analysis["key_elements"]:
                print(f"    - {elem['selector']}: {elem['count']} elements")

    # Extract and show some sample data
    if "home" in all_html:
        print("\n" + "=" * 60)
        print("SAMPLE DATA EXTRACTION")
        print("=" * 60)

        student_info = extract_student_info(all_html["home"])
        print(f"\nStudent Info: {student_info}")

        grades = extract_grades_preview(all_html["home"])
        print("\nGrades Preview (first 10 rows):")
        for row in grades[:10]:
            print(f"  {row}")

    if "assignments" in all_html:
        assignments = extract_assignments_preview(all_html["assignments"])
        print("\nAssignments Preview (first 10 rows):")
        for row in assignments[:10]:
            print(f"  {row}")

    print("\n" + "=" * 60)
    print("Reconnaissance complete!")
    print(f"HTML files saved to: {RAW_HTML_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    run_recon()
