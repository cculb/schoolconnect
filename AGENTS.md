# Agent Development Guide

## MANDATORY: Validate All Changes via CI

**You MUST trigger CI validation before completing any task.**
Do not rely solely on PR-triggered CI.

### Why Manual CI Dispatch is Required

| Trigger | What Runs | What's Skipped |
|---------|-----------|----------------|
| **Pull Request** | Lint, Unit, Integration | E2E Tests, Agent Dev Cycle |
| **Push to main** | Lint, Unit, Integration, E2E | Agent Dev Cycle |
| **Manual Dispatch** | Everything you select | Nothing |

> **Key insight**: PR CI is fast feedback only. E2E tests require manual
> dispatch to avoid hammering PowerSchool on every PR.

---

## Validating Features via CI

### After Adding Any Feature

```bash
# Quick validation (lint + unit tests)
gh workflow run "CI Pipeline" --repo cculb/schoolconnect -f agent_task=quick-check

# Check results
sleep 60 && gh run list --repo cculb/schoolconnect --limit 1
```

### After Adding UI Features

```bash
# UI-specific validation
gh workflow run "CI Pipeline" --repo cculb/schoolconnect -f agent_task=ui-only

# Full validation (includes UI)
gh workflow run "CI Pipeline" --repo cculb/schoolconnect -f agent_task=full-validation
```

### Reading Test Results

```bash
# Get run ID
RUN_ID=$(gh run list --repo cculb/schoolconnect --limit 1 --json databaseId --jq '.[0].databaseId')

# Download results
gh run download $RUN_ID --repo cculb/schoolconnect --name agent-results-* --dir /tmp/results

# Read summary
cat /tmp/results/test-summary.json
```

## UI Testing Patterns

### Streamlit Selectors

Use `data-testid` attributes (most reliable):

| Element | Selector |
|---------|----------|
| App container | `[data-testid="stApp"]` |
| Sidebar | `[data-testid="stSidebar"]` |
| Button | `[data-testid="stButton"]` |
| Text input | `[data-testid="stTextInput"]` |
| Selectbox | `[data-testid="stSelectbox"]` |
| Chat input | `[data-testid="stChatInput"]` |
| Chat message | `[data-testid="stChatMessage"]` |
| Info box | `[data-testid="stAlert"]` |

### Example: Adding a New Button Test

```python
def test_my_new_button(self, streamlit_page: Page):
    # Find button by text
    button = streamlit_page.locator('button:has-text("My Button")')
    expect(button).to_be_visible()

    # Click and verify response
    button.click()
    streamlit_page.wait_for_load_state("networkidle")
    expect(streamlit_page.locator('[data-testid="stChatMessage"]')).to_be_visible()
```

### Selector Strategies (Priority Order)

1. **`data-testid` attributes** (Most reliable)
   - Streamlit provides these for most elements
   - Example: `[data-testid="stButton"]`, `[data-testid="stChatInput"]`

2. **Role-based selectors with text** (Semantic)
   - Example: `page.get_by_role("button", name="Missing Work")`
   - Example: `page.get_by_role("textbox", name="Student Name")`

3. **Text content selectors** (Readable)
   - Example: `page.locator('button:has-text("Clear Chat")')`
   - Example: `page.get_by_text("SchoolPulse")`

4. **CSS selectors** (Fallback)
   - Use only when above methods fail
   - Avoid deeply nested selectors

## Available CI Tasks

| Task | Use When |
|------|----------|
| `quick-check` | After any change (fast feedback) |
| `unit-only` | Testing isolated logic |
| `integration-only` | Testing component interactions |
| `ui-only` | Changes to Streamlit UI |
| `scraper-only` | Changes to scraper code |
| `mcp-only` | Changes to MCP server |
| `full-validation` | Before completing a task |

## Test File Locations

| Area | Test File |
|------|-----------|
| Unit tests | `tests/unit/*.py` |
| Integration | `tests/integration/*.py` |
| Scraper E2E | `tests/e2e/test_scraper.py` |
| MCP server | `tests/e2e/test_mcp_tools.py` |
| Alerts | `tests/e2e/test_alerts.py` |
| UI (Streamlit) | `tests/e2e/test_streamlit_ui.py` |

## UI Test Classes

| Class | Purpose |
|-------|---------|
| TestPageLoad | Initial render, title, no errors |
| TestSidebarSettings | API key, model dropdown, student name |
| TestQuickActions | 4 quick action buttons |
| TestWelcomeInfoBox | Student summary display |
| TestConversationStarters | Dynamic starter buttons |
| TestChatInterface | Chat input and messages |

## Debugging Failed Tests

1. **View screenshots**: Check `reports/screenshots/` after failed CI run
2. **Run with visible browser**: `PWDEBUG=1 pytest ... -k "failing_test"`
3. **Add debug logging**: Use `page.screenshot(path="debug.png")`
4. **Check Streamlit logs**: Review CI output for server errors

## Feature Validation Checklist

**Before marking ANY task complete**, verify:

- [ ] Local lint passes: `ruff check src/ tests/`
- [ ] Local unit tests pass: `pytest tests/unit/ -x`
- [ ] **CI `quick-check` passes** (manual dispatch)
- [ ] **CI `full-validation` passes** (REQUIRED before task completion)

### Task Completion Requirements

1. Push your changes to the branch
2. Trigger CI: `gh workflow run "CI Pipeline" --repo cculb/schoolconnect -f agent_task=full-validation`
3. Wait for CI: `gh run watch $(gh run list --repo cculb/schoolconnect --limit 1 --json databaseId --jq '.[0].databaseId')`
4. Verify all tests pass before marking task complete
5. If tests fail, fix and repeat from step 1
