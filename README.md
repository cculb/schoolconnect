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

## Streamlit Chat Interface (SchoolPulse)

The project includes a Streamlit-based chat interface for interacting with student data using Claude AI.

### Streamlit Installation

```bash
# Navigate to the streamlit-chat directory
cd streamlit-chat

# Install dependencies (if not already installed via uv sync)
pip install streamlit anthropic python-dotenv
```

### Environment Setup

Create a `.env` file in the project root or `streamlit-chat/` directory:

```env
# Required for AI chat features
ANTHROPIC_API_KEY=your-anthropic-api-key

# Optional: Specify database path (defaults to ./powerschool.db)
DATABASE_PATH=/path/to/powerschool.db
```

### Running the App

```bash
# From the streamlit-chat directory
cd streamlit-chat
streamlit run app.py

# Or from project root
streamlit run streamlit-chat/app.py
```

The app will be available at `http://localhost:8501`.

### Streamlit Configuration Options

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key for Claude | Required for AI features |
| `DATABASE_PATH` | Path to SQLite database | `./powerschool.db` |

### Streamlit Features

- **Quick Actions**: One-click buttons for common queries (missing assignments, grades, attendance)
- **AI Chat**: Natural language conversation with Claude about student data
- **Model Selection**: Choose between Claude Opus, Sonnet, or Haiku models
- **Student Summary**: At-a-glance view of attendance rate, missing work, and course count

### Demo Mode

For testing without a real database, seed the database with test data:

```bash
cd streamlit-chat
python seed_data.py
```

Default demo credentials: `demo` / `demo123`

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

## Troubleshooting

### Common Issues

**Database errors:**

```bash
# Reset database
powerschool init-db --force
```

**Playwright browser errors:**

```bash
# Reinstall browsers
uv run playwright install chromium
```

**Login failures:**

- Verify credentials in `.env` file
- Check PowerSchool URL format (must include https://)
- Try running with visible browser: `powerschool sync` (without --headless)

**Import errors:**

```bash
# Ensure all dependencies are installed
uv sync
```

### Getting Help

1. Check existing issues: [GitHub Issues](https://github.com/cculb/schoolconnect/issues)
2. Review documentation in `docs/` directory
3. For agent development, see `CLAUDE.md`

## Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes following our code style (use `ruff check` and `ruff format`)
4. Write tests for new features
5. Ensure all tests pass: `pytest tests/`
6. Submit a pull request

See `CLAUDE.md` for agent-assisted development workflow.

## Roadmap

**Current Features:**

- Core data scraping (grades, assignments, attendance)
- CLI tools and MCP server
- Streamlit chat interface

**Planned Features:**

- Teacher comments extraction
- Daily attendance records
- Bilingual interface (English/Spanish)
- WhatsApp/SMS notifications
- Voice interface
- Document translation (OCR + translate)

See `COMPREHENSIVE_DATA_REPORT.md` for detailed vision and market analysis.

## License

MIT License - See [LICENSE](LICENSE) for details.

## Acknowledgments

Built with:

- [Playwright](https://playwright.dev/) for browser automation
- [MCP](https://modelcontextprotocol.io/) for AI agent integration
- [Claude](https://www.anthropic.com/claude) for conversational AI
- [Streamlit](https://streamlit.io/) for the web interface
