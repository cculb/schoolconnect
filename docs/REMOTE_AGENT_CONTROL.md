# Remote Agent Control from Phone

Control Claude Code agents iterating on this project from your mobile device.

## Quick Reference

| Task | Command/Action |
|------|---------------|
| Quick validation | `quick-check` |
| Unit tests only | `unit-only` |
| Integration tests | `integration-only` |
| Full E2E tests | `full-validation` |
| Scraper tests | `scraper-only` |
| MCP tools tests | `mcp-only` |

## Method 1: GitHub Mobile App (Easiest)

1. Install **GitHub** app on iOS/Android
2. Navigate to: `cculb/schoolconnect` > Actions > "CI Pipeline"
3. Tap **Run workflow**
4. Select task from dropdown
5. Tap **Run workflow**

You'll get push notifications when the workflow completes.

## Method 2: iOS Shortcuts (One-Tap Trigger)

Create a Shortcut for quick triggering:

1. Open **Shortcuts** app
2. Create new Shortcut
3. Add **Get Contents of URL** action:
   - URL: `https://api.github.com/repos/cculb/schoolconnect/actions/workflows/ci.yml/dispatches`
   - Method: POST
   - Headers:
     - `Authorization`: `Bearer YOUR_GITHUB_TOKEN`
     - `Accept`: `application/vnd.github.v3+json`
   - Request Body (JSON):
     ```json
     {
       "ref": "main",
       "inputs": {
         "agent_task": "quick-check",
         "debug_mode": "false"
       }
     }
     ```
4. Add to Home Screen as widget

### Generate a GitHub Token

1. Go to github.com > Settings > Developer Settings > Personal Access Tokens
2. Generate token with `repo` and `workflow` scopes
3. Save token securely

## Method 3: Repository Dispatch (For Agents)

Trigger via API for automated agent workflows:

```bash
curl -X POST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/cculb/schoolconnect/dispatches \
  -d '{
    "event_type": "agent-run",
    "client_payload": {
      "task": "quick"
    }
  }'
```

Available event types:
- `agent-run` - Run specific test suite
- `agent-validate` - Validate ground truth
- `agent-quick-check` - Fast lint + unit tests

## Method 4: Telegram/Discord Bot (Optional)

Set up a bot that monitors workflow status and allows triggering:

1. Create bot on Telegram/Discord
2. Use GitHub webhook for status updates
3. Bot commands: `/run quick`, `/run full`, `/status`

## Checking Results

### From Phone (GitHub App)
- Navigate to Actions > Select run > View logs

### From CLI
```bash
# List recent runs
gh run list --repo cculb/schoolconnect --limit 5

# View specific run logs
gh run view <RUN_ID> --repo cculb/schoolconnect --log

# Download artifacts
gh run download <RUN_ID> --repo cculb/schoolconnect
```

### Agent-Readable Output

Workflows generate `reports/test-summary.json` as an artifact with:
- Test counts (passed, failed, skipped)
- Database stats
- Error details
- Suggested next actions

## Workflow Architecture

```
Phone Trigger --> GitHub Actions --> Test Suite
                        |
                        v
              reports/test-summary.json
                        |
                        v
              Agent reads results & iterates
```

## Claude Code Cloud Agents

### Starting an Agent Session

From Claude.ai or the Claude app, you can tell Claude Code to work on this project:

```text
Work on the schoolconnect project at github.com/cculb/schoolconnect.
Implement [feature description].
Use /validate after each change to verify via CI.
Use /validate-full before completing the task.
```

### Available Agent Commands

The project includes these slash commands for agents:

| Command | Purpose |
|---------|---------|
| `/validate` | Quick CI check (lint + unit tests) |
| `/validate-full` | Full E2E validation |
| `/ci-status` | Check latest CI run status |

### Agent Development Cycle

1. Agent reads CLAUDE.md for project context
2. Agent implements the requested feature
3. Agent runs `/validate` to trigger CI
4. Agent reads test results from artifacts
5. Agent fixes any failures
6. Agent runs `/validate-full` before completing
7. Agent reports completion to you

### Giving Instructions from Phone

From Claude.ai mobile or the Claude app:

```text
Continue working on schoolconnect.
The last CI run failed - check /ci-status and fix the issues.
Run /validate when done.
```

## Example Agent Workflow

1. **You** (from phone): "Implement dark mode for the MCP server dashboard"
2. **Agent** clones repo, reads CLAUDE.md
3. **Agent** implements changes
4. **Agent** runs `/validate` -> CI runs quick-check
5. **Agent** reads test-summary.json, fixes failures
6. **Agent** runs `/validate-full` -> all tests pass
7. **Agent** reports completion, you review on phone

## Troubleshooting

### Pipeline won't trigger
- Check GitHub token has `workflow` scope
- Verify repo name is correct
- Check Actions are enabled in repo settings

### Tests failing
- Download artifacts for detailed logs
- Check `reports/e2e-output.log` for full pytest output
- Verify PowerSchool secrets are configured
