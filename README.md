# SchoolConnect

A Python tool for parents to scrape, store, and analyze student academic data from PowerSchool Parent Portal. Includes CLI tools, a SQLite database, and an MCP (Model Context Protocol) server for AI agent integration.

## Features

- **Data Scraping**: Automated extraction of grades, assignments, and attendance from PowerSchool
- **Local Database**: SQLite storage with views for analysis (grades, missing work, trends)
- **CLI Tools**: Command-line interface for querying and generating reports
- **MCP Server**: AI agent integration via Model Context Protocol (works with Claude, etc.)
- **Weekly Reports**: Automated summary reports for each student

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- Playwright (for browser automation)
- Valid PowerSchool Parent Portal credentials

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd schoolconnect

# Install dependencies with uv
uv sync

# Install Playwright browsers
uv run playwright install chromium
```

## Configuration

Create a `.env` file in the project root with your PowerSchool credentials:

```env
POWERSCHOOL_URL=https://your-school.powerschool.com
POWERSCHOOL_USERNAME=your-username
POWERSCHOOL_PASSWORD=your-password
```

> **Security Note**: The `.env` file is excluded from version control via `.gitignore`. Never commit credentials to git.

## Usage

### Initialize Database

```bash
# Create the database with schema and views
powerschool init-db

# Reset existing database
powerschool init-db --force
```

### Sync Data from PowerSchool

```bash
# Full sync (opens browser, logs in, scrapes all students)
powerschool sync

# Headless mode (no visible browser)
powerschool sync --headless
```

### View Grades

```bash
# Show current grades for a student
powerschool grades -s "StudentName"
```

### Check Missing Assignments

```bash
# Show missing assignments for all students
powerschool missing

# Show for specific student
powerschool missing -s "StudentName"
```

### Generate Reports

```bash
# Generate weekly report for a student
powerschool report -s "StudentName"
```

### Database Status

```bash
# Show database statistics and student overview
powerschool status
```

### MCP Server (AI Integration)

```bash
# Start the MCP server for AI agents
powerschool serve-mcp
```

## Project Structure

```text
schoolconnect/
├── src/
│   ├── cli/              # Command-line interface
│   │   └── main.py       # Click-based CLI commands
│   ├── database/         # SQLite database layer
│   │   ├── connection.py # Connection management
│   │   ├── repository.py # Data access methods
│   │   ├── schema.sql    # Database schema
│   │   └── views.sql     # Analysis views
│   ├── mcp_server/       # MCP server for AI agents
│   │   └── server.py     # MCP protocol implementation
│   └── scraper/          # Web scraping components
│       └── parsers/      # HTML parsing logic
├── scripts/              # Standalone scraping scripts
│   ├── scrape_full.py    # Full data scrape
│   └── load_data.py      # Load scraped data to DB
├── tests/                # Test suite
├── pyproject.toml        # Project configuration
└── .env                  # Credentials (not in git)
```

## Database Views

The database includes pre-built views for common queries:

| View | Description |
|------|-------------|
| `v_current_grades` | Latest grades by student and course |
| `v_missing_assignments` | All missing assignments with details |
| `v_grade_trends` | Grade progression Q1 -> Q2 -> S1 -> Q3 -> Q4 -> S2 |
| `v_attendance_alerts` | Students with attendance below 95% |
| `v_upcoming_assignments` | Assignments due in next 14 days |
| `v_student_summary` | High-level summary per student |
| `v_action_items` | Prioritized parent action items |

## MCP Tools

The MCP server exposes these tools for AI agents:

- `get_students` - List all students
- `get_grades` - Get grades for a student
- `get_missing_assignments` - Get missing work
- `get_attendance` - Get attendance data
- `get_action_items` - Get prioritized action items
- `custom_query` - Run read-only SQL queries (restricted to allowed tables/views)

## Development

```bash
# Install dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Run linter
uv run ruff check src/

# Type checking
uv run mypy src/
```

## Privacy and Security

This tool handles sensitive student data (FERPA protected). Best practices:

- Store `.env` credentials securely and never commit to git
- Database files (`.db`) contain PII - keep them local
- The `raw_html/` directory may contain scraped data - excluded from git
- MCP server custom queries are restricted to read-only operations on allowed tables

## License

MIT License - See [LICENSE](LICENSE) for details.
