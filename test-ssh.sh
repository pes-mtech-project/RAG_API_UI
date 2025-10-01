#!/bin/bash

# Test SSH connectivity to EC2 instance
# Usage: ./test-ssh.sh [elastic-ip]
# If no IP provided, automatically detects instance IP using AWS CLI

KEY_FILE="finbert-rag-key-new.pem"

# Function to get EC2 instance IP automatically
get_instance_ip() {
    # Try to get IP from tagged instance
    INSTANCE_IP=$(aws ec2 describe-instances \
        --filters 'Name=tag:Name,Values=finbert-rag-instance' 'Name=instance-state-name,Values=running' \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text 2>/dev/null)
    
    if [ "$INSTANCE_IP" != "None" ] && [ "$INSTANCE_IP" != "null" ] && [ ! -z "$INSTANCE_IP" ]; then
        echo "$INSTANCE_IP"
    else
        echo "3.7.194.20"
    fi
}

# Get IP address (from parameter or auto-detect)
if [ -z "$1" ]; then
    echo "🔍 Detecting EC2 instance IP address..."
    ELASTIC_IP=$(get_instance_ip)
    if [ "$ELASTIC_IP" = "3.7.194.20" ]; then
        echo "❌ Could not detect instance IP automatically - using fallback"
        echo "   Make sure AWS CLI is configured and instance is running"
    else
        echo "✅ Found running instance IP: $ELASTIC_IP"
    fi
else
    ELASTIC_IP=$1
    echo "🎯 Using provided IP address: $ELASTIC_IP"
fi

echo ""
echo "🔍 Testing SSH connectivity..."
echo "IP: $ELASTIC_IP"
echo "Key: $KEY_FILE"
echo ""

# Check if key file exists
if [ ! -f "$KEY_FILE" ]; then
    echo "❌ SSH key file not found: $KEY_FILE"
    echo "Please ensure the key file is in the current directory"
    exit 1
fi

# Check key file permissions
KEY_PERMS=$(stat -f "%OLp" "$KEY_FILE" 2>/dev/null || stat -c "%a" "$KEY_FILE" 2>/dev/null)
if [ "$KEY_PERMS" != "600" ]; then
    echo "🔧 Fixing key file permissions..."
    chmod 600 "$KEY_FILE"
fi

# Test SSH connection
echo "🔑 Testing SSH connection..."
ssh -i "$KEY_FILE" \
    -o ConnectTimeout=10 \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    ec2-user@$ELASTIC_IP \
    "echo '✅ SSH connection successful!' && whoami && uptime"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SSH test completed successfully!"
    echo "You can now connect using:"
    echo "ssh -i $KEY_FILE ec2-user@$ELASTIC_IP"
    
    # Show instance details if we auto-detected
    if [ -z "$1" ]; then
        echo ""
        echo "📋 Instance Details:"
        aws ec2 describe-instances \
            --filters 'Name=tag:Name,Values=finbert-rag-instance' 'Name=instance-state-name,Values=running' \
            --query 'Reservations[0].Instances[0].[InstanceId,InstanceType,State.Name,PublicIpAddress,KeyName]' \
            --output table 2>/dev/null || echo "   Could not fetch instance details"
    fi
else
    echo ""
    echo "❌ SSH connection failed!"
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Verify the Elastic IP: $ELASTIC_IP"
    echo "2. Ensure security group allows SSH (port 22)"
    echo "3. Check if instance is running"
    echo "4. Verify SSH key is correctly associated with the instance"
    echo ""
    echo "To check instance status:"
    echo "aws ec2 describe-instances --filters 'Name=tag:Name,Values=finbert-rag-instance' --query 'Reservations[0].Instances[0].[InstanceId,State.Name,PublicIpAddress,KeyName]' --output table"
fi
