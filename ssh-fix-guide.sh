#!/bin/bash

# Manual SSH Key Fix Guide
echo "🔧 Manual SSH Key Fix Solution"
echo "============================="
echo ""

echo "❌ PROBLEM IDENTIFIED:"
echo "- New instance created with wrong SSH key association"
echo "- Your local key file doesn't match the instance key"
echo "- AWS CLI is timing out (connection issues)"
echo ""

echo "✅ SOLUTION: Use Infrastructure Workflow to Fix"
echo ""

echo "📋 Step-by-step fix:"
echo ""
echo "1. 🛑 DESTROY current instance:"
echo "   - Go to: https://github.com/pes-mtech-project/RAG_API_UI/actions"
echo "   - Click 'Setup AWS Infrastructure'"
echo "   - Click 'Run workflow'"
echo "   - ✅ Check 'Destroy infrastructure'"  
echo "   - Click 'Run workflow'"
echo "   - Wait for completion (should work with our fixes)"
echo ""

echo "2. 🔧 FIX the SSH key issue in workflow:"
echo "   The problem is the workflow creates new keys instead of using existing ones."
echo "   We need to fix the infrastructure.yml file."
echo ""

echo "3. 🚀 RECREATE infrastructure:"
echo "   - Run infrastructure workflow again (without destroy)"
echo "   - Should create instance with correct SSH key"
echo ""

echo "🔍 ROOT CAUSE:"
echo "The infrastructure workflow has this logic:"
echo "if aws ec2 describe-key-pairs --key-names finbert-rag-key-new >/dev/null 2>&1; then"
echo "  echo 'SSH key pair already exists: finbert-rag-key-new'"
echo "else"
echo "  # Create new key pair"
echo ""
echo "But it's creating a NEW key pair instead of using the existing one properly."
echo ""

echo "🔧 IMMEDIATE FIX NEEDED:"
echo "Update the infrastructure workflow to ensure it uses the existing key file."
echo ""

read -p "Should I fix the infrastructure workflow now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔧 I'll fix the infrastructure workflow to handle SSH keys properly..."
    echo "This will ensure the instance is created with the correct key association."
else
    echo ""
    echo "🔧 Manual steps to fix:"
    echo "1. Go to AWS Console: https://ap-south-1.console.aws.amazon.com/ec2/home?region=ap-south-1#KeyPairs:"
    echo "2. Check what key pairs exist"
    echo "3. Download the correct private key for the instance"
    echo "4. Or delete the instance and recreate with correct key"
    echo ""
    echo "🎯 The cleanest solution is to fix the workflow and recreate the infrastructure."
fi