#!/bin/bash

# SSH Key Troubleshooting Script
echo "🔍 SSH Key Troubleshooting for Instance i-0926d838615d77d92"
echo "=========================================================="
echo ""

export AWS_DEFAULT_REGION=ap-south-1
INSTANCE_ID="i-0926d838615d77d92"
NEW_IP="3.7.241.66"

echo "📋 Instance Information:"
echo "Instance ID: $INSTANCE_ID"
echo "New Public IP: $NEW_IP"
echo "Expected Elastic IP: 3.7.194.20"
echo ""

echo "🔍 Step 1: Check what SSH key the instance is using..."
echo "Running: aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].KeyName' --output text"
INSTANCE_KEY=$(timeout 15 aws ec2 describe-instances --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].KeyName' --output text 2>/dev/null || echo "TIMEOUT")
echo "Instance SSH Key: $INSTANCE_KEY"
echo ""

echo "🔑 Step 2: Check available SSH key pairs..."
echo "Available key pairs:"
timeout 15 aws ec2 describe-key-pairs --query 'KeyPairs[].[KeyName,KeyFingerprint]' --output table 2>/dev/null || echo "Command timed out"
echo ""

echo "📁 Step 3: Check local SSH key files..."
echo "Local .pem files:"
ls -la *.pem 2>/dev/null || echo "No .pem files found in current directory"
echo ""

echo "🔧 Step 4: SSH Key Mismatch Diagnosis..."
if [ "$INSTANCE_KEY" = "finbert-rag-key-new" ]; then
    echo "✅ Instance uses: finbert-rag-key-new"
    if [ -f "finbert-rag-key-new.pem" ]; then
        echo "✅ Local key file: finbert-rag-key-new.pem exists"
        echo "🔍 Testing SSH connection..."
        ssh -i finbert-rag-key-new.pem -o ConnectTimeout=5 -o StrictHostKeyChecking=no ec2-user@$NEW_IP "echo 'SSH Success!'" 2>&1 || echo "SSH failed"
    else
        echo "❌ Local key file: finbert-rag-key-new.pem NOT found"
        echo "🔧 SOLUTION: Download the correct key from AWS or regenerate"
    fi
elif [ "$INSTANCE_KEY" = "finbert-rag-key-new-imported" ]; then
    echo "ℹ️ Instance uses: finbert-rag-key-new-imported (old key)"
    echo "❌ But you're using: finbert-rag-key-new.pem"
    echo "🔧 SOLUTION: Use the imported key or recreate instance with correct key"
else
    echo "❌ Instance uses unknown key: $INSTANCE_KEY"
    echo "🔧 SOLUTION: Check AWS console or recreate instance"
fi
echo ""

echo "🎯 Common Solutions:"
echo ""
echo "Solution 1 - Get the correct SSH key:"
if [ "$INSTANCE_KEY" != "TIMEOUT" ] && [ "$INSTANCE_KEY" != "None" ]; then
    echo "The instance is using key: $INSTANCE_KEY"
    echo "You need the private key file that matches this key pair."
fi
echo ""

echo "Solution 2 - Recreate instance with your existing key:"
echo "aws ec2 terminate-instances --region ap-south-1 --instance-ids $INSTANCE_ID"
echo "# Then run infrastructure workflow again"
echo ""

echo "Solution 3 - Check if Elastic IP is properly associated:"
echo "aws ec2 describe-addresses --region ap-south-1 --query 'Addresses[].[PublicIp,InstanceId]' --output table"
echo ""

echo "Solution 4 - Generate new SSH key pair and recreate instance:"
echo "aws ec2 create-key-pair --region ap-south-1 --key-name finbert-rag-key-new-2 --query 'KeyMaterial' --output text > finbert-rag-key-new-2.pem"
echo "chmod 600 finbert-rag-key-new-2.pem"
echo ""

echo "🔗 Quick Test Commands:"
echo "# Test with current key:"
echo "ssh -i finbert-rag-key-new.pem -o ConnectTimeout=5 -o StrictHostKeyChecking=no ec2-user@$NEW_IP"
echo ""
echo "# Check instance console output for boot errors:"
echo "aws ec2 get-console-output --region ap-south-1 --instance-id $INSTANCE_ID --query 'Output' --output text"
echo ""

echo "🌐 AWS Console Links:"
echo "- EC2 Instances: https://ap-south-1.console.aws.amazon.com/ec2/home?region=ap-south-1#Instances:"
echo "- Key Pairs: https://ap-south-1.console.aws.amazon.com/ec2/home?region=ap-south-1#KeyPairs:"