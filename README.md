# PowerSchool Parent Portal Enhancement

A Python application that scrapes data from PowerSchool parent portals, stores it in SQLite, and exposes it via an MCP server for AI-powered parent engagement and student insights.

## Problem Statement

Parents are too busy to constantly check the clunky PowerSchool portal. They want:
- Proactive alerts about missing assignments, grade drops, and attendance issues
- The ability to ask an AI "How is my kid doing in school?" and get useful answers
- Weekly summaries instead of daily manual checks

## Features

- **Data Scraping**: Automated extraction from PowerSchool parent portals using Playwright
- **SQLite Storage**: Well-designed schema with historical tracking
- **MCP Server**: AI agent interface for querying and analyzing student data
- **Actionable Insights**: Missing assignments, grade trends, attendance patterns
- **CLI Interface**: Quick access to reports and data

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/powerschool-portal.git
cd powerschool-portal

# Install dependencies
pip install -e ".[dev]"

# Install Playwright browsers
playwright install chromium
```

## Quick Start

### 1. Initialize the Database

```bash
powerschool init-db
```

### 2. Seed Test Data (for development)

```bash
python scripts/seed_test_data.py
```

### 3. View Missing Assignments

```bash
powerschool missing
```

### 4. Generate Weekly Report

```bash
powerschool report --student "Delilah"
```

### 5. Start MCP Server

```bash
powerschool serve-mcp
```

## Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Required environment variables:
- `POWERSCHOOL_URL`: Your district's PowerSchool URL
- `POWERSCHOOL_USERNAME`: Parent portal username
- `POWERSCHOOL_PASSWORD`: Parent portal password
- `DATABASE_PATH`: Path to SQLite database (default: `./data/powerschool.db`)

## MCP Tools

The MCP server exposes these tools for AI agents:

### Student Tools
- `list_students()` - List all students
- `get_student_summary(student_name)` - Comprehensive student overview

### Grade Tools
- `get_current_grades(student_name)` - Current quarter/semester grades
- `get_grade_history(student_name, course_name)` - Historical progression
- `calculate_gpa(student_name, term)` - GPA calculation
- `identify_grade_drops(student_name)` - Detect declining grades

### Assignment Tools
- `get_missing_assignments(student_name)` - Missing work
- `get_upcoming_assignments(student_name, days)` - Due soon
- `get_assignment_completion_rates(student_name)` - Completion by course

### Attendance Tools
- `get_attendance_summary(student_name)` - Attendance overview
- `identify_attendance_patterns(student_name)` - Pattern analysis

### Insight Tools
- `generate_weekly_report(student_name)` - Parent-friendly summary
- `get_action_items(student_name)` - Prioritized to-do list
- `prepare_teacher_meeting(student_name, course_name)` - Meeting prep

## Project Structure

```
powerschool-portal/
├── pyproject.toml
├── README.md
├── .env.example
├── src/
│   ├── __init__.py
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── core.py              # PowerSchoolScraper class
│   │   ├── parsers/
│   │   │   ├── assignments.py   # Parse assignment tables
│   │   │   ├── grades.py        # Parse grade tables
│   │   │   └── attendance.py    # Parse attendance data
│   │   └── config.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── schema.sql
│   │   ├── views.sql
│   │   ├── connection.py
│   │   └── repository.py
│   ├── mcp_server/
│   │   ├── __init__.py
│   │   ├── server.py            # Main MCP server
│   │   └── tools/
│   │       ├── students.py
│   │       ├── grades.py
│   │       ├── assignments.py
│   │       ├── attendance.py
│   │       └── insights.py
│   └── cli/
│       └── main.py
├── tests/
│   ├── conftest.py
│   ├── test_parsers.py
│   ├── test_database.py
│   └── test_mcp_tools.py
└── scripts/
    └── seed_test_data.py
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Formatting

```bash
ruff check --fix .
ruff format .
```

## License

MIT License - see LICENSE file for details.
