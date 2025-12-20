---
description: Check CI pipeline status and results
---

# Check CI Status

Check the status of recent CI runs without triggering a new one.

## View Recent Runs

```bash
gh run list --repo cculb/schoolconnect --limit 5
```

## Check Latest Run Status

```bash
gh run list --repo cculb/schoolconnect --limit 1 --json status,conclusion,name,createdAt --jq '.[] | "Status: \(.status)\nConclusion: \(.conclusion)\nWorkflow: \(.name)\nStarted: \(.createdAt)"'
```

## View Logs of Latest Run

```bash
RUN_ID=$(gh run list --repo cculb/schoolconnect --limit 1 --json databaseId --jq '.[0].databaseId')
gh run view $RUN_ID --repo cculb/schoolconnect --log
```

## Download Latest Results

```bash
RUN_ID=$(gh run list --repo cculb/schoolconnect --limit 1 --json databaseId --jq '.[0].databaseId')
gh run download $RUN_ID --repo cculb/schoolconnect --dir /tmp/latest-results 2>/dev/null || true
cat /tmp/latest-results/*/test-summary.json 2>/dev/null | jq '.' || echo "No results available"
```

## Check Specific Run

```bash
# Replace RUN_ID with actual run ID
gh run view <RUN_ID> --repo cculb/schoolconnect
```
