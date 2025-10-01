#!/bin/bash

# Script to restart EC2 instance and trigger redeployment

set -e

echo "🔄 Restarting EC2 Instance and Redeploying..."

# Get instance ID
INSTANCE_ID=$(aws ec2 describe-instances \
    --filters 'Name=tag:Name,Values=finbert-rag-instance' \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text)

echo "📋 Instance ID: $INSTANCE_ID"

# Stop the instance
echo "🛑 Stopping instance..."
aws ec2 stop-instances --instance-ids $INSTANCE_ID

# Wait for instance to stop
echo "⏳ Waiting for instance to stop..."
aws ec2 wait instance-stopped --instance-ids $INSTANCE_ID

# Start the instance
echo "▶️ Starting instance..."
aws ec2 start-instances --instance-ids $INSTANCE_ID

# Wait for instance to be running
echo "⏳ Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID

# Get new IP (might change after restart)
NEW_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "🌐 New IP Address: $NEW_IP"

# Wait a bit for SSH to be ready
echo "⏳ Waiting for SSH to be available..."
sleep 30

# Trigger GitHub Actions workflow to redeploy
echo "🚀 Triggering GitHub Actions deployment..."
gh workflow run containers.yml --ref main

echo "✅ Instance restarted and deployment triggered!"
echo "📍 Monitor deployment: https://github.com/pes-mtech-project/RAG_API_UI/actions"
echo "🔗 New endpoints will be available at:"
echo "   API: http://$NEW_IP:8000"
echo "   UI:  http://$NEW_IP:8501"

# Test SSH connectivity
echo ""
echo "🔍 Testing SSH connectivity..."
sleep 60  # Give more time for SSH to start

if ssh -i finbert-rag-key-new.pem -o ConnectTimeout=10 -o StrictHostKeyChecking=no ec2-user@$NEW_IP "echo 'SSH working'" 2>/dev/null; then
    echo "✅ SSH is working!"
else
    echo "❌ SSH still not working - may need manual intervention"
    echo "Try: ./test-ssh.sh $NEW_IP"
fi