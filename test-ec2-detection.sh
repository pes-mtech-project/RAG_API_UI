#!/bin/bash

# Test EC2 Instance Detection Logic
# Validates the same logic used in the GitHub Actions workflow

echo "🔍 Testing EC2 Instance Detection"
echo "================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔍 Looking for tagged Elastic IP...${NC}"

# Get Elastic IP details using the tag filter (same as workflow)
INSTANCE_IP=$(aws ec2 describe-addresses --region ap-south-1 --filters "Name=tag:Name,Values=finbert-rag-eip" --query 'Addresses[0].PublicIp' --output text)
INSTANCE_ID=$(aws ec2 describe-addresses --region ap-south-1 --filters "Name=tag:Name,Values=finbert-rag-eip" --query 'Addresses[0].InstanceId' --output text)

if [ "$INSTANCE_IP" = "None" ] || [ "$INSTANCE_IP" = "null" ]; then
  echo -e "${RED}❌ No Elastic IP found with tag 'finbert-rag-eip'${NC}"
  exit 1
fi

if [ "$INSTANCE_ID" = "None" ] || [ "$INSTANCE_ID" = "null" ]; then
  echo -e "${RED}❌ No instance associated with Elastic IP${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Found Elastic IP: $INSTANCE_IP${NC}"
echo -e "${GREEN}✅ Found Instance: $INSTANCE_ID${NC}"

# Verify instance is running
INSTANCE_STATE=$(aws ec2 describe-instances --region ap-south-1 --instance-ids $INSTANCE_ID --query 'Reservations[0].Instances[0].State.Name' --output text)
echo -e "${BLUE}📊 Instance state: $INSTANCE_STATE${NC}"

if [ "$INSTANCE_STATE" = "stopped" ]; then
  echo -e "${YELLOW}⚠️  Instance is stopped but would be started by deployment${NC}"
elif [ "$INSTANCE_STATE" = "running" ]; then
  echo -e "${GREEN}✅ Instance is running and ready for deployment${NC}"
else
  echo -e "${RED}❌ Instance is in unexpected state: $INSTANCE_STATE${NC}"
  exit 1
fi

echo ""
echo -e "${GREEN}🎉 EC2 Instance Detection Test Passed!${NC}"
echo ""
echo -e "${BLUE}📋 Deployment Target:${NC}"
echo "• Instance ID: $INSTANCE_ID"
echo "• Public IP: $INSTANCE_IP"
echo "• State: $INSTANCE_STATE"
echo ""
echo -e "${YELLOW}🚀 The deployment workflow should now work correctly!${NC}"