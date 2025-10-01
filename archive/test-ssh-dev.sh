#!/bin/bash

# SSH connectivity test script for Development EC2 instance
# Usage: ./test-ssh-dev.sh [elastic_ip_address]
# If no IP provided, automatically detects development instance IP using AWS CLI

KEY_FILE="finbert-rag-key-new.pem"

# Function to get development EC2 instance IP automatically
get_dev_instance_ip() {
    # Try to get IP from tagged development instance
    INSTANCE_IP=$(aws ec2 describe-instances \
        --filters 'Name=tag:Name,Values=finbert-rag-dev-instance' 'Name=instance-state-name,Values=running' \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text 2>/dev/null)
    
    if [ "$INSTANCE_IP" != "None" ] && [ "$INSTANCE_IP" != "null" ] && [ ! -z "$INSTANCE_IP" ]; then
        echo "$INSTANCE_IP"
    else
        echo "No development instance found"
    fi
}

# Get IP address (from parameter or auto-detect)
if [ -z "$1" ]; then
    echo "🔍 Detecting development EC2 instance IP address..."
    ELASTIC_IP=$(get_dev_instance_ip)
    if [ "$ELASTIC_IP" = "No development instance found" ]; then
        echo "❌ Could not find development instance"
        echo "   Make sure the development instance exists and is running"
        echo "   Instance should be tagged with Name=finbert-rag-dev-instance"
        exit 1
    else
        echo "✅ Found development instance IP: $ELASTIC_IP"
    fi
else
    ELASTIC_IP=$1
    echo "🎯 Using provided IP address: $ELASTIC_IP"
fi

echo ""
echo "🔍 Testing SSH connectivity to development instance..."
echo "IP: $ELASTIC_IP"
echo "Key: $KEY_FILE"

# Check if SSH key exists
if [ ! -f "$KEY_FILE" ]; then
    echo "❌ SSH key file not found: $KEY_FILE"
    echo "Please ensure the SSH key file exists in the current directory."
    exit 1
fi

# Fix SSH key permissions
chmod 600 "$KEY_FILE" 2>/dev/null

echo ""
echo "🔑 Testing SSH connection..."

# Test SSH connection with timeout and enhanced security
ssh -i "$KEY_FILE" \
    -o ConnectTimeout=10 \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    ubuntu@$ELASTIC_IP \
    "echo '✅ SSH connection successful to DEVELOPMENT instance!' && whoami && uptime && echo '🚧 Environment: Development (Branch: develop)'"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Development SSH test completed successfully!"
    echo "You can now connect using:"
    echo "ssh -i $KEY_FILE ubuntu@$ELASTIC_IP"
    
    # Show development instance details if we auto-detected
    if [ -z "$1" ]; then
        echo ""
        echo "📋 Development Instance Details:"
        aws ec2 describe-instances \
            --filters 'Name=tag:Name,Values=finbert-rag-dev-instance' 'Name=instance-state-name,Values=running' \
            --query 'Reservations[0].Instances[0].[InstanceId,InstanceType,State.Name,PublicIpAddress,KeyName]' \
            --output table 2>/dev/null || echo "   Could not fetch instance details"
        
        echo ""
        echo "🚧 Development Endpoints:"
        echo "   API: http://$ELASTIC_IP:8010"
        echo "   UI:  http://$ELASTIC_IP:8511"
        echo "   API Docs: http://$ELASTIC_IP:8010/docs"
    fi
else
    echo ""
    echo "❌ SSH connection failed!"
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Verify the Elastic IP: $ELASTIC_IP"
    echo "2. Ensure security group allows SSH (port 22)"
    echo "3. Check if development instance is running"
    echo "4. Verify SSH key is correctly associated with the instance"
    echo ""
    echo "To check development instance status:"
    echo "aws ec2 describe-instances --filters 'Name=tag:Name,Values=finbert-rag-dev-instance' --query 'Reservations[0].Instances[0].[InstanceId,State.Name,PublicIpAddress,KeyName]' --output table"
fi