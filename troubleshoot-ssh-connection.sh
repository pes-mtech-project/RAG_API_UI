#!/bin/bash

# SSH Connection Troubleshooting Script
# Helps diagnose SSH connectivity issues with AWS EC2 instances

echo "🔍 SSH Connection Troubleshooting"
echo "================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if we have AWS CLI configured
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install AWS CLI first.${NC}"
    exit 1
fi

echo -e "${BLUE}🔍 Checking AWS configuration...${NC}"
if aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${GREEN}✅ AWS CLI is configured${NC}"
else
    echo -e "${RED}❌ AWS CLI not configured or credentials invalid${NC}"
    exit 1
fi

# Target IP and region
TARGET_IP="3.7.241.66"
REGION="ap-south-1"
KEY_FILE="finbert-rag-key-new.pem"

echo -e "${BLUE}🔍 Checking target: $TARGET_IP${NC}"

# Check if this is our Elastic IP
echo -e "${BLUE}🔍 Checking if this is our Elastic IP...${NC}"
ELASTIC_IP=$(aws ec2 describe-addresses --region $REGION --filters "Name=tag:Name,Values=finbert-rag-eip" --query 'Addresses[0].PublicIp' --output text 2>/dev/null || echo "None")

if [ "$ELASTIC_IP" = "$TARGET_IP" ]; then
    echo -e "${GREEN}✅ This is our Elastic IP${NC}"
elif [ "$ELASTIC_IP" = "None" ] || [ "$ELASTIC_IP" = "null" ]; then
    echo -e "${YELLOW}⚠️  No Elastic IP found with tag 'finbert-rag-eip'${NC}"
else
    echo -e "${YELLOW}⚠️  Target IP ($TARGET_IP) doesn't match our Elastic IP ($ELASTIC_IP)${NC}"
fi

# Find the instance associated with this IP
echo -e "${BLUE}🔍 Finding instance associated with $TARGET_IP...${NC}"
INSTANCE_ID=$(aws ec2 describe-instances --region $REGION --filters "Name=ip-address,Values=$TARGET_IP" --query 'Reservations[0].Instances[0].InstanceId' --output text 2>/dev/null || echo "None")

if [ "$INSTANCE_ID" = "None" ] || [ "$INSTANCE_ID" = "null" ]; then
    echo -e "${RED}❌ No instance found with IP $TARGET_IP${NC}"
    
    # Check if we have any running instances
    echo -e "${BLUE}🔍 Checking for any running instances...${NC}"
    RUNNING_INSTANCES=$(aws ec2 describe-instances --region $REGION --filters "Name=instance-state-name,Values=running" --query 'Reservations[].Instances[].[InstanceId,PublicIpAddress,Tags[?Key==`Name`].Value|[0]]' --output table)
    
    if [ -n "$RUNNING_INSTANCES" ]; then
        echo -e "${YELLOW}Running instances found:${NC}"
        echo "$RUNNING_INSTANCES"
    else
        echo -e "${RED}❌ No running instances found${NC}"
        echo "You may need to run the infrastructure workflow to create the instance."
    fi
    exit 1
else
    echo -e "${GREEN}✅ Found instance: $INSTANCE_ID${NC}"
fi

# Check instance state
echo -e "${BLUE}🔍 Checking instance state...${NC}"
INSTANCE_STATE=$(aws ec2 describe-instances --region $REGION --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].State.Name' --output text)
echo -e "${BLUE}Instance state: $INSTANCE_STATE${NC}"

if [ "$INSTANCE_STATE" != "running" ]; then
    echo -e "${RED}❌ Instance is not running (state: $INSTANCE_STATE)${NC}"
    echo "Wait for the instance to reach 'running' state or restart the infrastructure workflow."
    exit 1
fi

# Check instance status checks
echo -e "${BLUE}🔍 Checking instance status checks...${NC}"
INSTANCE_STATUS=$(aws ec2 describe-instance-status --region $REGION --instance-ids $INSTANCE_ID --query 'InstanceStatuses[0].InstanceStatus.Status' --output text 2>/dev/null || echo "None")
SYSTEM_STATUS=$(aws ec2 describe-instance-status --region $REGION --instance-ids $INSTANCE_ID --query 'InstanceStatuses[0].SystemStatus.Status' --output text 2>/dev/null || echo "None")

echo -e "${BLUE}Instance status: $INSTANCE_STATUS${NC}"
echo -e "${BLUE}System status: $SYSTEM_STATUS${NC}"

if [ "$INSTANCE_STATUS" != "ok" ] || [ "$SYSTEM_STATUS" != "ok" ]; then
    echo -e "${YELLOW}⚠️  Instance status checks not passing yet. This may cause SSH issues.${NC}"
    echo "Wait a few minutes for the instance to fully initialize."
fi

# Check security group
echo -e "${BLUE}🔍 Checking security group rules...${NC}"
SECURITY_GROUPS=$(aws ec2 describe-instances --region $REGION --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].SecurityGroups[].GroupId' --output text)

for SG in $SECURITY_GROUPS; do
    echo -e "${BLUE}Checking security group: $SG${NC}"
    
    # Check for SSH rule (port 22)
    SSH_RULE=$(aws ec2 describe-security-groups --region $REGION --group-ids $SG --query 'SecurityGroups[0].IpPermissions[?FromPort==`22`]' --output text)
    
    if [ -n "$SSH_RULE" ]; then
        echo -e "${GREEN}✅ SSH rule (port 22) found in security group${NC}"
        
        # Show the rule details
        aws ec2 describe-security-groups --region $REGION --group-ids $SG --query 'SecurityGroups[0].IpPermissions[?FromPort==`22`]' --output table
    else
        echo -e "${RED}❌ No SSH rule (port 22) found in security group $SG${NC}"
    fi
done

# Check key pair
echo -e "${BLUE}🔍 Checking SSH key pair...${NC}"
if [ ! -f "$KEY_FILE" ]; then
    echo -e "${RED}❌ SSH key file '$KEY_FILE' not found${NC}"
    exit 1
fi

KEY_PERMS=$(stat -f "%A" "$KEY_FILE" 2>/dev/null || stat -c "%a" "$KEY_FILE" 2>/dev/null)
if [ "$KEY_PERMS" = "600" ]; then
    echo -e "${GREEN}✅ SSH key permissions are correct (600)${NC}"
else
    echo -e "${YELLOW}⚠️  SSH key permissions are $KEY_PERMS, should be 600${NC}"
    echo "Run: chmod 600 $KEY_FILE"
fi

# Test network connectivity
echo -e "${BLUE}🔍 Testing network connectivity...${NC}"
if ping -c 1 -W 5 $TARGET_IP > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Host is reachable via ping${NC}"
else
    echo -e "${RED}❌ Host is not reachable via ping${NC}"
fi

# Test port 22 connectivity
echo -e "${BLUE}🔍 Testing SSH port (22) connectivity...${NC}"
if timeout 10 bash -c "</dev/tcp/$TARGET_IP/22" 2>/dev/null; then
    echo -e "${GREEN}✅ Port 22 is open and reachable${NC}"
else
    echo -e "${RED}❌ Port 22 is not reachable or SSH service is not running${NC}"
    echo "This could mean:"
    echo "  • SSH service is not started on the instance"
    echo "  • Security group is blocking port 22"
    echo "  • Instance is still booting up"
fi

# Get instance launch time
echo -e "${BLUE}🔍 Checking instance launch time...${NC}"
LAUNCH_TIME=$(aws ec2 describe-instances --region $REGION --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].LaunchTime' --output text)
echo -e "${BLUE}Instance launched at: $LAUNCH_TIME${NC}"

# Calculate how long ago
if command -v python3 &> /dev/null; then
    MINUTES_AGO=$(python3 -c "
from datetime import datetime, timezone
import sys
try:
    launch = datetime.fromisoformat('$LAUNCH_TIME'.replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    diff = now - launch
    minutes = int(diff.total_seconds() / 60)
    print(f'{minutes} minutes ago')
except:
    print('Unable to calculate')
")
    echo -e "${BLUE}That was: $MINUTES_AGO${NC}"
fi

echo ""
echo -e "${YELLOW}🔧 Troubleshooting Recommendations:${NC}"
echo ""

if [ "$INSTANCE_STATUS" != "ok" ] || [ "$SYSTEM_STATUS" != "ok" ]; then
    echo -e "${YELLOW}1. Wait for status checks:${NC} Instance may still be initializing"
    echo "   Check status: aws ec2 describe-instance-status --region $REGION --instance-ids $INSTANCE_ID"
fi

echo -e "${YELLOW}2. Try different SSH usernames:${NC}"
echo "   • Ubuntu AMI: ssh -i $KEY_FILE ubuntu@$TARGET_IP"
echo "   • Amazon Linux: ssh -i $KEY_FILE ec2-user@$TARGET_IP"
echo "   • Amazon Linux 2023: ssh -i $KEY_FILE ec2-user@$TARGET_IP"

echo -e "${YELLOW}3. Increase SSH timeout:${NC}"
echo "   ssh -i $KEY_FILE -o ConnectTimeout=60 -o ServerAliveInterval=60 ubuntu@$TARGET_IP"

echo -e "${YELLOW}4. Check instance console output:${NC}"
echo "   aws ec2 get-console-output --region $REGION --instance-id $INSTANCE_ID"

echo -e "${YELLOW}5. Restart SSH service via AWS Systems Manager:${NC}"
echo "   (If the instance has SSM agent installed)"

if [ "$INSTANCE_STATUS" = "ok" ] && [ "$SYSTEM_STATUS" = "ok" ]; then
    echo ""
    echo -e "${GREEN}🚀 Instance appears healthy. Try SSH with verbose output:${NC}"
    echo "ssh -i $KEY_FILE -v ubuntu@$TARGET_IP"
fi