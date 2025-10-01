#!/bin/bash

# Quick SSH Key Fix
echo "🔧 Quick SSH Key Fix for New Instance"
echo "===================================="
echo ""

NEW_IP="3.7.241.66"
echo "Testing SSH connection to: $NEW_IP"
echo ""

echo "🔍 Method 1: Test with existing key file..."
if [ -f "finbert-rag-key-new.pem" ]; then
    echo "✅ Found: finbert-rag-key-new.pem"
    chmod 600 finbert-rag-key-new.pem
    
    echo "🔑 Testing SSH connection..."
    if timeout 10 ssh -i finbert-rag-key-new.pem -o ConnectTimeout=5 -o StrictHostKeyChecking=no ec2-user@$NEW_IP "echo 'SSH Success!'" 2>/dev/null; then
        echo "🎉 SSH SUCCESS with finbert-rag-key-new.pem!"
        echo ""
        echo "✅ Working SSH command:"
        echo "ssh -i finbert-rag-key-new.pem ec2-user@$NEW_IP"
        exit 0
    else
        echo "❌ SSH failed with finbert-rag-key-new.pem"
    fi
else
    echo "❌ finbert-rag-key-new.pem not found"
fi

echo ""
echo "🔍 Method 2: Check for other key files..."
for keyfile in *.pem; do
    if [ -f "$keyfile" ]; then
        echo "🔑 Testing with: $keyfile"
        chmod 600 "$keyfile"
        if timeout 10 ssh -i "$keyfile" -o ConnectTimeout=5 -o StrictHostKeyChecking=no ec2-user@$NEW_IP "echo 'SSH Success!'" 2>/dev/null; then
            echo "🎉 SSH SUCCESS with $keyfile!"
            echo ""
            echo "✅ Working SSH command:"
            echo "ssh -i $keyfile ec2-user@$NEW_IP"
            exit 0
        fi
    fi
done

echo ""
echo "❌ SSH failed with all available keys"
echo ""
echo "🔧 SOLUTION: Create a new key pair and recreate the instance"
echo ""

read -p "Create new SSH key pair and recreate instance? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔑 Creating new SSH key pair..."
    
    # Generate timestamp for unique key name
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    NEW_KEY_NAME="finbert-rag-key-$TIMESTAMP"
    
    if timeout 30 aws ec2 create-key-pair --region ap-south-1 --key-name $NEW_KEY_NAME --query 'KeyMaterial' --output text > $NEW_KEY_NAME.pem 2>/dev/null; then
        chmod 600 $NEW_KEY_NAME.pem
        echo "✅ New key created: $NEW_KEY_NAME.pem"
        echo ""
        echo "🛑 Now terminating current instance..."
        if timeout 30 aws ec2 terminate-instances --region ap-south-1 --instance-ids i-0926d838615d77d92 >/dev/null 2>&1; then
            echo "✅ Instance termination initiated"
            echo ""
            echo "🚀 Next steps:"
            echo "1. Wait 2-3 minutes for instance to terminate"
            echo "2. Update infrastructure workflow to use: $NEW_KEY_NAME"
            echo "3. Run infrastructure workflow again"
            echo "4. SSH with: ssh -i $NEW_KEY_NAME.pem ec2-user@<new-ip>"
        else
            echo "❌ Failed to terminate instance - do it manually in AWS console"
        fi
    else
        echo "❌ Failed to create new key pair"
    fi
else
    echo ""
    echo "🔧 Manual fix options:"
    echo "1. Check AWS Console for the correct key pair name"
    echo "2. Download the matching private key"
    echo "3. Or recreate the instance with the correct key"
    echo ""
    echo "🌐 AWS Console: https://ap-south-1.console.aws.amazon.com/ec2/home?region=ap-south-1#KeyPairs:"
fi