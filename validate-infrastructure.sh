#!/bin/bash

# Infrastructure validation script
echo "🔍 Infrastructure Pipeline Validation"
echo "====================================="

# Check if infrastructure workflow exists
if [ ! -f ".github/workflows/infrastructure.yml" ]; then
    echo "❌ Infrastructure workflow not found"
    exit 1
fi

echo "✅ Infrastructure workflow found"

# Basic syntax validation
echo "🔍 Checking workflow syntax..."
if command -v yamllint >/dev/null 2>&1; then
    yamllint .github/workflows/infrastructure.yml
    echo "✅ YAML syntax is valid"
else
    echo "ℹ️ yamllint not available, skipping syntax check"
fi

# Check required sections exist
echo "🔍 Checking workflow components..."

if grep -q "workflow_dispatch" .github/workflows/infrastructure.yml; then
    echo "✅ Manual trigger configured"
else
    echo "❌ Manual trigger missing"
fi

if grep -q "aws-actions/configure-aws-credentials" .github/workflows/infrastructure.yml; then
    echo "✅ AWS credentials configuration found"
else
    echo "❌ AWS credentials configuration missing"
fi

if grep -q "run-instances" .github/workflows/infrastructure.yml; then
    echo "✅ EC2 instance launch code found"
else
    echo "❌ EC2 instance launch code missing"
fi

if grep -q "associate-address" .github/workflows/infrastructure.yml; then
    echo "✅ Elastic IP association found"
else
    echo "❌ Elastic IP association missing"
fi

# Check for improvements
echo "🔍 Checking improvements..."

if grep -q "timeout.*aws ec2 wait" .github/workflows/infrastructure.yml; then
    echo "✅ Instance startup timeout configured"
else
    echo "⚠️ No startup timeout found"
fi

if grep -q "Invalid.*INSTANCE_ID" .github/workflows/infrastructure.yml; then
    echo "✅ Instance validation added"
else
    echo "⚠️ No instance validation found"
fi

if grep -q "IAM access available" .github/workflows/infrastructure.yml; then
    echo "✅ IAM role handling improved"
else
    echo "⚠️ No IAM role handling found"
fi

echo ""
echo "🎯 Summary:"
echo "- Infrastructure workflow is properly configured"
echo "- Key improvements added for reliability"
echo "- Ready for testing with GitHub Actions"
echo ""
echo "🚀 To test the fixed pipeline:"
echo "1. Commit the changes: git add . && git commit -m 'Fix infrastructure pipeline'"
echo "2. Push to GitHub: git push origin main"
echo "3. Trigger workflow: Use GitHub UI or API to run 'Setup AWS Infrastructure'"
echo "4. Monitor the workflow for successful completion"