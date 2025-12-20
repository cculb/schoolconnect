# SchoolConnect - Agent Development Guide

## Project Overview

PowerSchool scraper and MCP server for student data access. Python 3.12+, Playwright for browser automation.

## Validation Workflow

**CRITICAL**: After making code changes, always validate your work using the CI pipeline.

### Quick Validation (Fast Feedback)

```bash
# Trigger quick check (lint + unit tests)
gh workflow run "CI Pipeline" --repo cculb/schoolconnect -f agent_task=quick-check

# Wait and check results
sleep 5 && gh run list --repo cculb/schoolconnect --limit 1
```

### Full Validation (Before Completing Task)

```bash
# Trigger full E2E tests
gh workflow run "CI Pipeline" --repo cculb/schoolconnect -f agent_task=full-validation

# Monitor the run
gh run watch $(gh run list --repo cculb/schoolconnect --limit 1 --json databaseId --jq '.[0].databaseId') --repo cculb/schoolconnect
```

### Reading Results

```bash
# Download test summary artifact
gh run download $(gh run list --repo cculb/schoolconnect --limit 1 --json databaseId --jq '.[0].databaseId') \
  --repo cculb/schoolconnect \
  --name agent-results-* \
  --dir /tmp/results

# Read the results
cat /tmp/results/test-summary.json
```

## Development Cycle

1. **Understand** - Read relevant code before making changes
2. **Implement** - Make focused, minimal changes
3. **Local Check** - Run `ruff check src/ tests/` and `pytest tests/unit/ -x`
4. **Push** - Commit and push changes
5. **Validate** - Trigger CI pipeline with `quick-check`
6. **Iterate** - Fix any failures, repeat until passing
7. **Full Validation** - Run `full-validation` before marking complete

## Available CI Tasks

| Task | Use When |
|------|----------|
| `quick-check` | After each change (fast) |
| `unit-only` | Testing isolated logic |
| `integration-only` | Testing component interactions |
| `full-validation` | Final verification |
| `scraper-only` | Changes to scraper code |
| `mcp-only` | Changes to MCP server |

## Project Structure

```
src/
  scraper/       # PowerSchool web scraper
  mcp_server/    # MCP server for Claude access
  models/        # SQLAlchemy models
  repositories/  # Data access layer
tests/
  unit/          # Fast, isolated tests
  integration/   # Component tests
  e2e/           # Full E2E with live PowerSchool
scripts/
  generate_test_summary.py  # Creates agent-readable JSON
  generate_agent_report.py  # Creates detailed reports
```

## Key Files

- `src/scraper/powerschool_scraper.py` - Main scraper logic
- `src/mcp_server/server.py` - MCP server implementation
- `src/repositories/*.py` - Database queries
- `tests/e2e/test_*.py` - E2E test suites

## Environment

Tests use these env vars (set in GitHub secrets):
- `POWERSCHOOL_URL` - PowerSchool portal URL
- `POWERSCHOOL_USERNAME` - Login username
- `POWERSCHOOL_PASSWORD` - Login password (base64)

## Commit Guidelines

- Use conventional commits: `type(scope): description`
- Types: feat, fix, refactor, test, docs, chore
- Keep commits focused and atomic
- Run validation before marking tasks complete
