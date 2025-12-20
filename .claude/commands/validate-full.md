---
description: Run full E2E validation before completing a task
---

# Full E2E Validation

Run comprehensive E2E tests against live PowerSchool to validate all changes before marking a task complete.

## Steps

1. Ensure all changes are committed and pushed:
```bash
git status
git add -A && git commit -m "feat: ready for validation" 2>/dev/null || true
git push origin $(git branch --show-current)
```

2. Trigger full validation:
```bash
gh workflow run "CI Pipeline" --repo cculb/schoolconnect -f agent_task=full-validation -f debug_mode=false
```

3. Wait for pipeline to start and monitor:
```bash
sleep 5
RUN_ID=$(gh run list --repo cculb/schoolconnect --limit 1 --json databaseId --jq '.[0].databaseId')
echo "Full validation run: https://github.com/cculb/schoolconnect/actions/runs/$RUN_ID"
gh run watch $RUN_ID --repo cculb/schoolconnect --exit-status
```

4. Download detailed results:
```bash
gh run download $RUN_ID --repo cculb/schoolconnect --dir /tmp/full-validation 2>/dev/null || true
```

5. Analyze results:
```bash
# Test summary
cat /tmp/full-validation/*/test-summary.json 2>/dev/null | jq '.' || echo "No summary"

# Agent report
cat /tmp/full-validation/*/agent-report.json 2>/dev/null | jq '.' || echo "No agent report"
```

## Expected Outcome

For a task to be considered complete:
- All lint checks pass
- All unit tests pass
- All integration tests pass
- E2E tests pass or have documented known issues

## If Validation Fails

1. Read the test-summary.json for failure details
2. Check specific test output in the GitHub Actions logs
3. Fix identified issues
4. Run /validate for quick feedback
5. Run /validate-full again when ready
