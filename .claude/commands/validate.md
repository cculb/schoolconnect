---
description: Validate work via GitHub Actions CI pipeline
---

# Validate Changes via CI

Run the GitHub Actions pipeline to validate your changes.

## Steps

1. First, check if there are uncommitted changes:
```bash
git status
```

2. If changes exist, commit them:
```bash
git add -A && git commit -m "wip: validation checkpoint"
git push origin $(git branch --show-current)
```

3. Trigger the CI pipeline with quick-check:
```bash
gh workflow run "CI Pipeline" --repo cculb/schoolconnect -f agent_task=quick-check -f debug_mode=false
```

4. Wait for pipeline to start:
```bash
sleep 5
```

5. Get the run ID and monitor:
```bash
RUN_ID=$(gh run list --repo cculb/schoolconnect --limit 1 --json databaseId --jq '.[0].databaseId')
echo "Monitoring run: $RUN_ID"
gh run watch $RUN_ID --repo cculb/schoolconnect --exit-status
```

6. If the run failed, download and analyze the results:
```bash
gh run download $RUN_ID --repo cculb/schoolconnect --dir /tmp/ci-results 2>/dev/null || true
cat /tmp/ci-results/*/test-summary.json 2>/dev/null || echo "No summary available"
```

7. Based on results:
   - **Passed**: Continue with your task or run full-validation
   - **Failed**: Fix the issues and run /validate again

## Quick Reference

```bash
# One-liner to trigger and watch
gh workflow run "CI Pipeline" --repo cculb/schoolconnect -f agent_task=quick-check && \
  sleep 5 && \
  gh run watch $(gh run list --repo cculb/schoolconnect --limit 1 --json databaseId --jq '.[0].databaseId') --repo cculb/schoolconnect
```
