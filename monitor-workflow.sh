#!/bin/bash

# GitHub Workflow Monitor Script
REPO="pes-mtech-project/RAG_API_UI"
WORKFLOW_ID="194271601"

echo "🔍 Monitoring ECS Deployment Workflow..."
echo "Repository: $REPO"
echo "Workflow ID: $WORKFLOW_ID"
echo ""

# Get latest workflow runs
echo "📊 Latest Workflow Runs:"
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/$REPO/actions/workflows/$WORKFLOW_ID/runs?per_page=3" | \
  jq -r '.workflow_runs[] | "🔸 Run \(.id): \(.status) (\(.conclusion // "running")) - \(.head_branch) - \(.created_at)"'

echo ""

# Get the latest run details
LATEST_RUN_ID=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/$REPO/actions/workflows/$WORKFLOW_ID/runs?per_page=1" | \
  jq -r '.workflow_runs[0].id')

echo "🎯 Latest Run ID: $LATEST_RUN_ID"
echo "🔗 View logs: https://github.com/$REPO/actions/runs/$LATEST_RUN_ID"

# Get job status
echo ""
echo "📋 Job Status:"
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/$REPO/actions/runs/$LATEST_RUN_ID/jobs" | \
  jq -r '.jobs[] | "🔸 \(.name): \(.status) (\(.conclusion // "running"))"'

echo ""
echo "✅ Monitoring complete. Check the URL above for detailed logs."