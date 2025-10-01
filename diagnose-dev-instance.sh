#!/bin/bash

# Comprehensive diagnostic script for Development EC2 instance

echo "🚧 Development EC2 Instance Diagnostic Report"
echo "=============================================="
echo "Generated: $(date)"
echo "Environment: Development (Branch: develop)"
echo ""

# Get development instance details
echo "📋 Development Instance Details:"
aws ec2 describe-instances \
    --filters 'Name=tag:Name,Values=finbert-rag-dev-instance' \
    --query 'Reservations[0].Instances[0].[InstanceId,State.Name,PublicIpAddress,LaunchTime,InstanceType]' \
    --output table

INSTANCE_ID=$(aws ec2 describe-instances \
    --filters 'Name=tag:Name,Values=finbert-rag-dev-instance' \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text)

IP_ADDRESS=$(aws ec2 describe-instances \
    --filters 'Name=tag:Name,Values=finbert-rag-dev-instance' \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

if [ "$INSTANCE_ID" = "None" ] || [ "$INSTANCE_ID" = "null" ]; then
    echo ""
    echo "❌ Development instance not found!"
    echo "   Expected tag: Name=finbert-rag-dev-instance"
    echo "   Use GitHub Actions workflow to create development instance"
    exit 1
fi

echo ""
echo "🔒 Security Group Rules:"
SG_ID=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].SecurityGroups[0].GroupId' \
    --output text)

aws ec2 describe-security-groups \
    --group-ids $SG_ID \
    --query 'SecurityGroups[0].IpPermissions[*].[IpProtocol,FromPort,ToPort,IpRanges[0].CidrIp]' \
    --output table

echo ""
echo "🌐 Development Network Connectivity Tests:"
echo "Testing IP: $IP_ADDRESS"

# Test SSH
echo -n "SSH (port 22): "
if timeout 5 nc -z $IP_ADDRESS 22 2>/dev/null; then
    echo "✅ OPEN"
else
    echo "❌ CLOSED/TIMEOUT"
fi

# Test Development API port
echo -n "Dev API (port 8010): "
if timeout 5 nc -z $IP_ADDRESS 8010 2>/dev/null; then
    echo "✅ OPEN"
else
    echo "❌ CLOSED/TIMEOUT"
fi

# Test Development UI port
echo -n "Dev UI (port 8511): "
if timeout 5 nc -z $IP_ADDRESS 8511 2>/dev/null; then
    echo "✅ OPEN"
else
    echo "❌ CLOSED/TIMEOUT"
fi

echo ""
echo "🔍 Development HTTP Endpoint Tests:"
echo -n "Dev API Health: "
if curl -s --connect-timeout 5 http://$IP_ADDRESS:8010/health >/dev/null 2>&1; then
    echo "✅ RESPONDING"
    # Show health status
    echo "   Status: $(curl -s http://$IP_ADDRESS:8010/health | jq -r '.status // "unknown"')"
else
    echo "❌ NOT RESPONDING"
fi

echo -n "Dev UI Service: "
if curl -s --connect-timeout 5 http://$IP_ADDRESS:8511 >/dev/null 2>&1; then
    echo "✅ RESPONDING"
else
    echo "❌ NOT RESPONDING"
fi

echo ""
echo "📊 Development Instance System Status:"
aws ec2 describe-instance-status \
    --instance-ids $INSTANCE_ID \
    --query 'InstanceStatuses[0].[SystemStatus.Status,InstanceStatus.Status]' \
    --output table

# Check if we can SSH to get container status
echo ""
echo "🐳 Development Container Status:"
if ssh -i finbert-rag-key-new.pem -o ConnectTimeout=5 -o StrictHostKeyChecking=no ec2-user@$IP_ADDRESS "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'" 2>/dev/null; then
    echo ""
else
    echo "❌ Could not connect via SSH to check containers"
fi

echo ""
echo "📝 Recent Console Output (last 20 lines):"
echo "----------------------------------------"
aws ec2 get-console-output \
    --instance-id $INSTANCE_ID \
    --query 'Output' \
    --output text | tail -20

echo ""
echo "🔧 Development Environment Info:"
echo "🌍 Branch: develop"
echo "🚧 Environment: Development"
echo "📍 API Endpoint: http://$IP_ADDRESS:8010"
echo "📍 UI Endpoint: http://$IP_ADDRESS:8511"
echo "📖 API Docs: http://$IP_ADDRESS:8010/docs"

echo ""
echo "🛠️ Development Recommended Actions:"
echo "1. SSH access: ./test-ssh-dev.sh"
echo "2. Restart development instance: ./restart-dev-instance.sh"
echo "3. Check development containers: ssh and run 'docker ps'"
echo "4. Monitor development deployment: https://github.com/pes-mtech-project/RAG_API_UI/actions"
echo "5. Compare with production: ./diagnose-instance.sh"