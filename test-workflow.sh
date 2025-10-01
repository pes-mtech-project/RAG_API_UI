#!/bin/bash

# Test the fixed infrastructure workflow
echo "🚀 Testing Infrastructure Workflow"
echo "================================="

# Check if we have the latest changes
git status

echo ""
echo "🔍 Validating workflow file..."
if [ -f ".github/workflows/infrastructure.yml" ]; then
    echo "✅ Infrastructure workflow exists"
    
    # Check for key improvements
    if grep -q "al2023-ami.*ap-south-1" .github/workflows/infrastructure.yml; then
        echo "✅ Correct AMI lookup for ap-south-1"
    else
        echo "⚠️ AMI lookup might need verification"
    fi
    
    if grep -q "timeout.*aws ec2 wait" .github/workflows/infrastructure.yml; then
        echo "✅ Timeout protection added"
    else
        echo "⚠️ No timeout protection found"
    fi
    
    if grep -q "Validate.*INSTANCE_ID" .github/workflows/infrastructure.yml; then
        echo "✅ Instance validation present"
    else
        echo "⚠️ Instance validation might be missing" 
    fi
else
    echo "❌ Infrastructure workflow not found!"
    exit 1
fi

echo ""
echo "📋 Ready to test! Next steps:"
echo "1. Commit any changes: git add . && git commit -m 'Infrastructure fixes'"
echo "2. Push to GitHub: git push origin main"
echo "3. Go to GitHub Actions and manually trigger 'Setup AWS Infrastructure'"
echo "4. Monitor the workflow execution"

echo ""
echo "🔗 GitHub Actions URL:"
echo "https://github.com/pes-mtech-project/RAG_API_UI/actions/workflows/infrastructure.yml"

echo ""
echo "Expected results:"
echo "✅ AMI lookup should find correct Amazon Linux 2023 AMI for ap-south-1"
echo "✅ SSH key should be handled properly (create if not exists)"
echo "✅ Instance should launch successfully with t3.micro fallback"
echo "✅ Elastic IP should be associated correctly"
echo "✅ Final validation should confirm running instance"