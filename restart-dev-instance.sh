#!/bin/bash

# Script to restart Development EC2 instance and trigger redeployment

set -e

echo "🚧 Restarting Development EC2 Instance and Redeploying..."

# Get development instance ID
INSTANCE_ID=$(aws ec2 describe-instances \
    --filters 'Name=tag:Name,Values=finbert-rag-dev-instance' \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text)

if [ "$INSTANCE_ID" = "None" ] || [ "$INSTANCE_ID" = "null" ]; then
    echo "❌ Development instance not found!"
    echo "   Expected tag: Name=finbert-rag-dev-instance"
    echo "   Creating development instance via GitHub Actions..."
    
    # Trigger GitHub Actions workflow to create development instance
    gh workflow run containers-develop.yml --ref develop
    
    echo "✅ Development deployment triggered!"
    echo "📍 Monitor: https://github.com/pes-mtech-project/RAG_API_UI/actions"
    exit 0
fi

echo "📋 Development Instance ID: $INSTANCE_ID"

# Stop the instance
echo "🛑 Stopping development instance..."
aws ec2 stop-instances --instance-ids $INSTANCE_ID

# Wait for instance to stop
echo "⏳ Waiting for development instance to stop..."
aws ec2 wait instance-stopped --instance-ids $INSTANCE_ID

# Start the instance
echo "▶️ Starting development instance..."
aws ec2 start-instances --instance-ids $INSTANCE_ID

# Wait for instance to be running
echo "⏳ Waiting for development instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get new IP (might change after restart)
NEW_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "🌐 Development IP Address: $NEW_IP"

# Wait a bit for SSH to be ready
echo "⏳ Waiting for SSH to be available..."
sleep 30

# Trigger GitHub Actions workflow to redeploy development
echo "🚀 Triggering development deployment..."
gh workflow run containers-develop.yml --ref develop

echo "✅ Development instance restarted and deployment triggered!"
echo "📍 Monitor deployment: https://github.com/pes-mtech-project/RAG_API_UI/actions"
echo "🔗 Development endpoints will be available at:"
echo "   API: http://$NEW_IP:8010"
echo "   UI:  http://$NEW_IP:8511"
echo "   API Docs: http://$NEW_IP:8010/docs"

# Test SSH connectivity
echo ""
echo "🔍 Testing SSH connectivity..."
sleep 60  # Give more time for SSH to start

if ssh -i finbert-rag-key-new.pem -o ConnectTimeout=10 -o StrictHostKeyChecking=no ec2-user@$NEW_IP "echo 'Development SSH working'" 2>/dev/null; then
    echo "✅ Development SSH is working!"
else
    echo "❌ Development SSH still not working - may need manual intervention"
    echo "Try: ./test-ssh-dev.sh $NEW_IP"
fi