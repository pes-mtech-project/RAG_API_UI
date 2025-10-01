#!/bin/bash

echo "🚀 Testing Infrastructure Workflow"
echo "=================================="

# Check if we're in the right directory
if [ ! -f ".github/workflows/infrastructure.yml" ]; then
    echo "❌ Not in the correct directory. Please run from the project root."
    exit 1
fi

echo "✅ Found infrastructure workflow file"

# Commit any pending changes
echo "📦 Committing infrastructure fixes..."
git add .github/workflows/infrastructure.yml

if git diff --staged --quiet; then
    echo "ℹ️ No changes to commit"
else
    git commit -m "🔧 Fix AMI lookup and improve instance launch reliability"
    echo "✅ Changes committed"
fi

# Push to GitHub
echo "📤 Pushing to GitHub..."
git push origin main

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to GitHub"
else
    echo "❌ Failed to push to GitHub"
    exit 1
fi

echo ""
echo "🎯 Infrastructure workflow is ready!"
echo ""
echo "📋 Next steps:"
echo "1. Go to GitHub repository: https://github.com/pes-mtech-project/RAG_API_UI"
echo "2. Click on 'Actions' tab"
echo "3. Find 'Setup AWS Infrastructure' workflow"
echo "4. Click 'Run workflow' button"
echo "5. Click the green 'Run workflow' button to trigger"
echo ""
echo "📊 Or use GitHub API (if you have a valid token):"
echo "curl -X POST -H \"Authorization: token YOUR_TOKEN\" \\"
echo "  -H \"Accept: application/vnd.github.v3+json\" \\"
echo "  \"https://api.github.com/repos/pes-mtech-project/RAG_API_UI/actions/workflows/infrastructure.yml/dispatches\" \\"
echo "  -d '{\"ref\":\"main\"}'"
echo ""
echo "⏱️ The workflow should complete in 3-5 minutes"
echo "✅ Look for a running EC2 instance with Elastic IP 3.7.194.20"