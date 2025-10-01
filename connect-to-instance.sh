#!/bin/bash

# Quick SSH Connection to FinBERT RAG Instance
# This script provides the correct connection details for your AWS instance

echo "🔗 FinBERT RAG AWS Instance Connection"
echo "====================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get current instance details
echo -e "${BLUE}🔍 Getting current instance details...${NC}"

INSTANCE_IP=$(aws ec2 describe-addresses --region ap-south-1 --query 'Addresses[0].PublicIp' --output text 2>/dev/null)
INSTANCE_ID=$(aws ec2 describe-addresses --region ap-south-1 --query 'Addresses[0].InstanceId' --output text 2>/dev/null)

if [ "$INSTANCE_IP" = "None" ] || [ "$INSTANCE_IP" = "null" ] || [ -z "$INSTANCE_IP" ]; then
    echo -e "${YELLOW}⚠️  No Elastic IP found. Checking for running instances...${NC}"
    
    INSTANCE_DETAILS=$(aws ec2 describe-instances --region ap-south-1 --filters "Name=instance-state-name,Values=running" --query 'Reservations[0].Instances[0].[InstanceId,PublicIpAddress]' --output text 2>/dev/null)
    
    if [ "$INSTANCE_DETAILS" != "None" ] && [ -n "$INSTANCE_DETAILS" ]; then
        INSTANCE_ID=$(echo "$INSTANCE_DETAILS" | cut -f1)
        INSTANCE_IP=$(echo "$INSTANCE_DETAILS" | cut -f2)
        echo -e "${YELLOW}Found running instance: $INSTANCE_ID with IP: $INSTANCE_IP${NC}"
    else
        echo -e "${YELLOW}No running instances found. Please run the infrastructure workflow.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Instance ID: $INSTANCE_ID${NC}"
echo -e "${GREEN}✅ Public IP: $INSTANCE_IP${NC}"

# Check key file
KEY_FILE="finbert-rag-key-new.pem"
if [ ! -f "$KEY_FILE" ]; then
    echo -e "${YELLOW}⚠️  SSH key file '$KEY_FILE' not found in current directory${NC}"
    echo "Make sure you're in the right directory or provide the full path to your key file."
    exit 1
fi

echo -e "${GREEN}✅ SSH Key: $KEY_FILE${NC}"

echo ""
echo -e "${BLUE}📋 Connection Commands:${NC}"
echo ""
echo -e "${YELLOW}For Amazon Linux instances (recommended):${NC}"
echo "ssh -i $KEY_FILE ec2-user@$INSTANCE_IP"
echo ""
echo -e "${YELLOW}For Ubuntu instances (if applicable):${NC}"
echo "ssh -i $KEY_FILE ubuntu@$INSTANCE_IP"
echo ""
echo -e "${YELLOW}With connection timeout (recommended):${NC}"
echo "ssh -i $KEY_FILE -o ConnectTimeout=30 -o StrictHostKeyChecking=no ec2-user@$INSTANCE_IP"
echo ""
echo -e "${YELLOW}For file transfer (SCP):${NC}"
echo "scp -i $KEY_FILE local-file ec2-user@$INSTANCE_IP:~/remote-file"
echo ""

echo -e "${BLUE}🚀 Quick Connect:${NC}"
echo "Running SSH connection now..."
echo ""

# Attempt connection
ssh -i "$KEY_FILE" -o ConnectTimeout=30 -o StrictHostKeyChecking=no ec2-user@"$INSTANCE_IP"