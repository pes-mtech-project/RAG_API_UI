#!/bin/bash

# Quick Infrastructure Test Script
# This script avoids long-running commands that cause hanging

echo "🚀 Infrastructure Workflow Test"
echo "==============================="

# Set timeout for all AWS commands
export AWS_CLI_READ_TIMEOUT=30
export AWS_CLI_CONNECT_TIMEOUT=10

# Check basic AWS connectivity
echo "1. Testing AWS connectivity..."
if timeout 10 aws sts get-caller-identity --query 'UserId' --output text >/dev/null 2>&1; then
    echo "✅ AWS connection OK"
else
    echo "❌ AWS connection failed"
    exit 1
fi

# Check if we can access ap-south-1
echo "2. Testing ap-south-1 region access..."
if timeout 15 aws ec2 describe-regions --region-names ap-south-1 --query 'Regions[0].RegionName' --output text >/dev/null 2>&1; then
    echo "✅ ap-south-1 region accessible"
else
    echo "❌ ap-south-1 region access failed"
    exit 1
fi

# Check current instance count (quick check)
echo "3. Checking current instances..."
INSTANCE_COUNT=$(timeout 20 aws ec2 describe-instances --region ap-south-1 --query 'length(Reservations[].Instances[])' --output text 2>/dev/null || echo "0")
echo "Current instances: $INSTANCE_COUNT"

# Test AMI lookup (this was causing issues before)
echo "4. Testing AMI lookup for ap-south-1..."
AMI_ID=$(timeout 20 aws ec2 describe-images \
  --region ap-south-1 \
  --owners amazon \
  --filters 'Name=name,Values=al2023-ami-*-x86_64' 'Name=state,Values=available' \
  --query 'Images | sort_by(@, &CreationDate) | [-1].ImageId' \
  --output text 2>/dev/null)

if [ -n "$AMI_ID" ] && [ "$AMI_ID" != "None" ]; then
    echo "✅ AMI lookup successful: $AMI_ID"
else
    echo "❌ AMI lookup failed"
    exit 1
fi

echo ""
echo "🎉 All basic tests passed!"
echo "Infrastructure workflow should work properly now."
echo ""
echo "To run the infrastructure workflow:"
echo "1. Go to GitHub Actions in your repository"
echo "2. Find 'Setup AWS Infrastructure' workflow"
echo "3. Click 'Run workflow' button"
echo "4. Monitor the progress in the Actions tab"
echo ""
echo "Or trigger via API (if you have a valid GitHub token):"
echo "curl -X POST -H 'Authorization: token \$GITHUB_TOKEN' \\"
echo "  'https://api.github.com/repos/pes-mtech-project/RAG_API_UI/actions/workflows/infrastructure.yml/dispatches' \\"
echo "  -d '{\"ref\":\"main\"}'"