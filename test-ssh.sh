#!/bin/bash

# Test SSH connectivity to EC2 instance
# Usage: ./test-ssh.sh [elastic-ip]

ELASTIC_IP=${1:-"3.7.194.20"}
KEY_FILE="finbert-rag-key-new.pem"

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
