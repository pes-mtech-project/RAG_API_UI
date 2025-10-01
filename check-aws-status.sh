#!/bin/bash

# Check AWS infrastructure status
echo "🔍 AWS Infrastructure Status Check"
echo "=================================="
echo ""

# Check current AWS region and credentials
echo "📍 AWS Configuration:"
CURRENT_REGION=$(aws configure get region 2>/dev/null || echo "Not set")
CURRENT_USER=$(aws sts get-caller-identity --query 'UserName' --output text 2>/dev/null || echo "Unknown")
echo "Region: $CURRENT_REGION"
echo "User: $CURRENT_USER"
echo ""

# Set region to Mumbai
export AWS_DEFAULT_REGION=ap-south-1
echo "🌏 Checking ap-south-1 (Mumbai) region..."
echo ""

# Check EC2 instances
echo "🖥️ EC2 Instances:"
aws ec2 describe-instances \
    --filters 'Name=tag:Name,Values=finbert-rag-instance' \
    --query 'Reservations[*].Instances[*].[InstanceId,State.Name,InstanceType,PublicIpAddress,KeyName,LaunchTime]' \
    --output table 2>/dev/null || echo "No instances found or access denied"
echo ""

# Check security groups
echo "🔒 Security Group:"
aws ec2 describe-security-groups \
    --filters 'Name=group-name,Values=finbert-rag-sg' \
    --query 'SecurityGroups[0].[GroupId,GroupName,Description]' \
    --output table 2>/dev/null || echo "Security group not found"
echo ""

# Check security group rules
echo "🔓 Security Group Rules:"
aws ec2 describe-security-groups \
    --filters 'Name=group-name,Values=finbert-rag-sg' \
    --query 'SecurityGroups[0].IpPermissions[*].[IpProtocol,FromPort,ToPort,IpRanges[0].CidrIp]' \
    --output table 2>/dev/null || echo "No rules found"
echo ""

# Check Elastic IPs
echo "🌐 Elastic IPs:"
aws ec2 describe-addresses \
    --query 'Addresses[*].[PublicIp,AllocationId,InstanceId,AssociationId]' \
    --output table 2>/dev/null || echo "No Elastic IPs found"
echo ""

# Check SSH key pairs
echo "🔑 SSH Key Pairs:"
aws ec2 describe-key-pairs \
    --query 'KeyPairs[*].[KeyName,KeyFingerprint]' \
    --output table 2>/dev/null || echo "No key pairs found"
echo ""

# Check IAM role
echo "🔐 IAM Role (FinBERT-RAG-EC2-SSM-Role):"
aws iam get-role \
    --role-name FinBERT-RAG-EC2-SSM-Role \
    --query 'Role.[RoleName,CreateDate,Arn]' \
    --output table 2>/dev/null || echo "IAM role not found"

# Check instance profile
echo ""
echo "👤 Instance Profile (FinBERT-RAG-EC2-Profile):"
aws iam get-instance-profile \
    --instance-profile-name FinBERT-RAG-EC2-Profile \
    --query 'InstanceProfile.[InstanceProfileName,CreateDate,Arn]' \
    --output table 2>/dev/null || echo "Instance profile not found"
echo ""

# Check if Session Manager is available
echo "🔧 Session Manager Status:"
INSTANCE_ID=$(aws ec2 describe-instances \
    --filters 'Name=tag:Name,Values=finbert-rag-instance' 'Name=instance-state-name,Values=running' \
    --query 'Reservations[0].Instances[0].InstanceId' \
    --output text 2>/dev/null)

if [ "$INSTANCE_ID" != "None" ] && [ -n "$INSTANCE_ID" ]; then
    echo "Instance ID: $INSTANCE_ID"
    SSM_STATUS=$(aws ssm describe-instance-information \
        --filters "Key=InstanceIds,Values=$INSTANCE_ID" \
        --query 'InstanceInformationList[0].[InstanceId,PingStatus,LastPingDateTime]' \
        --output table 2>/dev/null || echo "Not available")
    echo "$SSM_STATUS"
else
    echo "No running instance found"
fi
echo ""

# Final summary
echo "📋 Quick Status Summary:"
echo "======================="

# Instance status
if [ "$INSTANCE_ID" != "None" ] && [ -n "$INSTANCE_ID" ]; then
    INSTANCE_STATE=$(aws ec2 describe-instances \
        --instance-ids $INSTANCE_ID \
        --query 'Reservations[0].Instances[0].State.Name' \
        --output text)
    PUBLIC_IP=$(aws ec2 describe-instances \
        --instance-ids $INSTANCE_ID \
        --query 'Reservations[0].Instances[0].PublicIpAddress' \
        --output text)
    KEY_NAME=$(aws ec2 describe-instances \
        --instance-ids $INSTANCE_ID \
        --query 'Reservations[0].Instances[0].KeyName' \
        --output text)
    
    echo "✅ Instance: $INSTANCE_ID ($INSTANCE_STATE)"
    echo "🌐 IP: $PUBLIC_IP"
    echo "🔑 Key: $KEY_NAME"
    
    if [ "$INSTANCE_STATE" = "running" ]; then
        echo ""
        echo "🚀 Ready for connection!"
        echo "SSH: ssh -i finbert-rag-key-new.pem ec2-user@$PUBLIC_IP"
        echo "SSM: aws ssm start-session --target $INSTANCE_ID"
    fi
else
    echo "❌ No running instance found"
fi