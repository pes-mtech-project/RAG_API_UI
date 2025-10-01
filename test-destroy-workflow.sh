#!/bin/bash

# Safe Infrastructure Destroy Test
echo "🧹 Infrastructure Destroy Workflow Test"
echo "======================================="
echo ""

echo "⚠️  IMPORTANT: This will destroy your current infrastructure!"
echo "Current running instance: i-0926d838615d77d92 (3.7.194.20)"
echo ""
echo "📋 What the fixed destroy workflow will do:"
echo "1. ✅ Find and terminate ALL instances (including test ones)"
echo "2. ✅ Wait for proper instance termination"
echo "3. ✅ Wait for network interfaces to detach (30 seconds)"
echo "4. ✅ Clean up any remaining network interfaces"
echo "5. ✅ Delete security group with retries (up to 5 attempts)"
echo "6. ✅ Clean up IAM roles and instance profiles"
echo "7. ✅ Preserve Elastic IP and SSH keys for reuse"
echo ""

echo "🔧 Fixes applied to destroy workflow:"
echo "- ✅ Proper instance termination wait"
echo "- ✅ Network interface cleanup"
echo "- ✅ Security group deletion with retries"
echo "- ✅ Additional wait times for dependencies"
echo "- ✅ Better error handling"
echo ""

echo "🚀 To test the destroy workflow:"
echo ""
echo "Option 1 - GitHub UI:"
echo "1. Go to: https://github.com/pes-mtech-project/RAG_API_UI/actions"
echo "2. Find 'Setup AWS Infrastructure' workflow"
echo "3. Click 'Run workflow'"
echo "4. Check 'Destroy infrastructure' checkbox"
echo "5. Click 'Run workflow' button"
echo ""

echo "Option 2 - API (if you have a valid token):"
echo "curl -X POST \\"
echo "  -H 'Authorization: token \$GITHUB_TOKEN' \\"
echo "  -H 'Accept: application/vnd.github.v3+json' \\"
echo "  'https://api.github.com/repos/pes-mtech-project/RAG_API_UI/actions/workflows/infrastructure.yml/dispatches' \\"
echo "  -d '{\"ref\":\"main\", \"inputs\":{\"destroy\":\"true\"}}'"
echo ""

echo "📊 Expected Results:"
echo "✅ All instances terminated properly"
echo "✅ Security group deleted without dependency errors"
echo "✅ IAM roles cleaned up"
echo "✅ Elastic IP preserved for future use"
echo "✅ SSH keys preserved for future use"
echo ""

echo "🔄 After successful destroy, you can:"
echo "1. Run the infrastructure workflow again (without destroy checkbox)"
echo "2. It will recreate everything using existing Elastic IP and SSH keys"
echo "3. SSH access will work immediately"
echo ""

read -p "Ready to test the destroy workflow? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Triggering destroy workflow..."
    
    if [ -n "$GITHUB_TOKEN" ]; then
        curl -X POST \
          -H "Authorization: token $GITHUB_TOKEN" \
          -H "Accept: application/vnd.github.v3+json" \
          "https://api.github.com/repos/pes-mtech-project/RAG_API_UI/actions/workflows/infrastructure.yml/dispatches" \
          -d '{"ref":"main", "inputs":{"destroy":"true"}}'
        
        echo ""
        echo "✅ Destroy workflow triggered!"
        echo "Monitor at: https://github.com/pes-mtech-project/RAG_API_UI/actions"
    else
        echo "❌ GITHUB_TOKEN not set. Please use the GitHub UI method."
    fi
else
    echo "ℹ️ Destroy workflow test cancelled."
fi