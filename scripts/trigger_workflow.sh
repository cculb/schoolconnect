#!/bin/bash
# Trigger GitHub Actions workflow from anywhere
# Usage: ./trigger_workflow.sh [task] [debug]
#
# Tasks: full-validation, scraper-only, mcp-only, alerts-only, 
#        ground-truth, quick-check, unit-only, integration-only

REPO="cculb/schoolconnect"
WORKFLOW="CI Pipeline"
TASK="${1:-quick-check}"
DEBUG="${2:-false}"

echo "Triggering workflow..."
echo "  Repo: $REPO"
echo "  Task: $TASK"

gh workflow run "$WORKFLOW" \
  --repo "$REPO" \
  -f agent_task="$TASK" \
  -f debug_mode="$DEBUG"

if [ $? -eq 0 ]; then
  echo "✅ Workflow triggered successfully!"
  sleep 2
  echo ""
  echo "Latest run:"
  gh run list --repo "$REPO" --limit 1 --json status,name,url --jq '.[] | "Status: \(.status)\nURL: \(.url)"'
else
  echo "❌ Failed to trigger workflow"
  exit 1
fi
