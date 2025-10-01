#!/bin/bash

# Comprehensive diagnostic script for EC2 instance and endpoints

echo "🔍 EC2 Instance Diagnostic Report"
echo "=================================="
echo "Generated: $(date)"
echo ""

# Get instance details
echo "📋 Instance Details:"
aws ec2 describe-instances \
    --filters 'Name=tag:Name,Values=finbert-rag-instance' \
    --query 'Reservations[0].Instances[0].[InstanceId,State.Name,PublicIpAddress,LaunchTime,InstanceType]' \
    --output table

INSTANCE_ID=$(aws ec2 describe-instances \
    --filters 'Name=tag:Name,Values=finbert-rag-instance' \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text)

IP_ADDRESS=$(aws ec2 describe-instances \
    --filters 'Name=tag:Name,Values=finbert-rag-instance' \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

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
echo "🌐 Network Connectivity Tests:"
echo "Testing IP: $IP_ADDRESS"

# Test SSH
echo -n "SSH (port 22): "
if timeout 5 nc -z $IP_ADDRESS 22 2>/dev/null; then
    echo "✅ OPEN"
else
    echo "❌ CLOSED/TIMEOUT"
fi

# Test API port
echo -n "API (port 8000): "
if timeout 5 nc -z $IP_ADDRESS 8000 2>/dev/null; then
    echo "✅ OPEN"
else
    echo "❌ CLOSED/TIMEOUT"
fi

# Test UI port
echo -n "UI (port 8501): "
if timeout 5 nc -z $IP_ADDRESS 8501 2>/dev/null; then
    echo "✅ OPEN"
else
    echo "❌ CLOSED/TIMEOUT"
fi

echo ""
echo "🔍 HTTP Endpoint Tests:"
echo -n "API Health: "
if curl -s --connect-timeout 5 http://$IP_ADDRESS:8000/health >/dev/null 2>&1; then
    echo "✅ RESPONDING"
else
    echo "❌ NOT RESPONDING"
fi

echo -n "UI Service: "
if curl -s --connect-timeout 5 http://$IP_ADDRESS:8501 >/dev/null 2>&1; then
    echo "✅ RESPONDING"
else
    echo "❌ NOT RESPONDING"
fi

echo ""
echo "📊 Instance System Status:"
aws ec2 describe-instance-status \
    --instance-ids $INSTANCE_ID \
    --query 'InstanceStatuses[0].[SystemStatus.Status,InstanceStatus.Status]' \
    --output table

echo ""
echo "📝 Recent Console Output (last 20 lines):"
echo "----------------------------------------"
aws ec2 get-console-output \
    --instance-id $INSTANCE_ID \
    --query 'Output' \
    --output text | tail -20

echo ""
echo "🔧 Recommended Actions:"
echo "1. If SSH is not working: Run ./restart-instance.sh"
echo "2. If endpoints not responding: Check if deployment completed successfully"
echo "3. Monitor GitHub Actions: https://github.com/pes-mtech-project/RAG_API_UI/actions"
echo "4. Manual SSH test: ./test-ssh.sh"