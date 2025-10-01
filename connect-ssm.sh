#!/bin/bash

# Connect to EC2 instance via AWS Session Manager
# Usage: ./connect-ssm.sh [instance-id]

INSTANCE_ID=${1:-"i-05cf3774f0646b47d"}

echo "🔍 Connecting via AWS Session Manager..."
echo "Instance ID: $INSTANCE_ID"
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity >/dev/null 2>&1; then
    echo "❌ AWS CLI not configured or credentials invalid"
    echo "Please run: aws configure"
    exit 1
fi

# Check if Session Manager plugin is installed
if ! aws ssm start-session --help >/dev/null 2>&1; then
    echo "❌ AWS Session Manager plugin not installed"
    echo ""
    echo "Please install it from:"
    echo "https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html"
    echo ""
    echo "For macOS:"
    echo "curl \"https://s3.amazonaws.com/session-manager-downloads/plugin/latest/mac/sessionmanager-bundle.zip\" -o \"sessionmanager-bundle.zip\""
    echo "unzip sessionmanager-bundle.zip"
    echo "sudo ./sessionmanager-bundle/install -i /usr/local/sessionmanagerplugin -b /usr/local/bin/session-manager-plugin"
    exit 1
fi

# Check if instance exists and is running
echo "🔍 Checking instance status..."
INSTANCE_STATUS=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].State.Name' \
    --output text 2>/dev/null)

if [ -z "$INSTANCE_STATUS" ] || [ "$INSTANCE_STATUS" = "None" ]; then
    echo "❌ Instance not found: $INSTANCE_ID"
    exit 1
fi

if [ "$INSTANCE_STATUS" != "running" ]; then
    echo "❌ Instance is not running. Current state: $INSTANCE_STATUS"
    exit 1
fi

echo "✅ Instance is running"

# Check if Session Manager is available for this instance
echo "🔍 Checking Session Manager availability..."
SSM_STATUS=$(aws ssm describe-instance-information \
    --filters "Key=InstanceIds,Values=$INSTANCE_ID" \
    --query 'InstanceInformationList[0].PingStatus' \
    --output text 2>/dev/null)

if [ -z "$SSM_STATUS" ] || [ "$SSM_STATUS" = "None" ]; then
    echo "❌ Instance not registered with Session Manager"
    echo ""
    echo "This might be because:"
    echo "1. Instance doesn't have the required IAM role"
    echo "2. SSM Agent is not running"
    echo "3. Instance is not connected to the internet"
    echo ""
    echo "Re-run the infrastructure workflow to add the required IAM role."
    exit 1
fi

if [ "$SSM_STATUS" != "Online" ]; then
    echo "⚠️ Instance SSM status: $SSM_STATUS"
    echo "Attempting connection anyway..."
fi

# Start Session Manager session
echo "🚀 Starting Session Manager session..."
echo "Once connected, you can run standard Linux commands."
echo ""

aws ssm start-session --target $INSTANCE_ID

echo ""
echo "✅ Session Manager session ended"