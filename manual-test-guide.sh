#!/bin/bash

# Manual Testing Guide for SSH Consistency Fix
# Since GitHub CLI is not available, this provides manual testing steps

echo "🧪 Manual Testing Guide for SSH Consistency Fix"
echo "================================================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}📋 Testing Steps:${NC}"
echo ""

echo -e "${YELLOW}Step 1: Trigger Destroy Workflow${NC}"
echo "1. Go to: https://github.com/pes-mtech-project/RAG_API_UI/actions"
echo "2. Click on 'Infrastructure Management'"
echo "3. Click 'Run workflow'"
echo "4. Select branch: main"
echo "5. Select action: destroy"
echo "6. Click 'Run workflow'"
echo ""

echo -e "${YELLOW}Step 2: Monitor Destroy Process${NC}"
echo "• Watch the workflow logs to ensure clean destruction"
echo "• Verify all resources are removed except Elastic IP and key pairs"
echo "• Should complete without dependency errors"
echo ""

echo -e "${YELLOW}Step 3: Trigger Create Workflow${NC}"
echo "1. Go back to workflow page"
echo "2. Click 'Run workflow' again"
echo "3. Select branch: main"
echo "4. Select action: create"
echo "5. Click 'Run workflow'"
echo ""

echo -e "${YELLOW}Step 4: Monitor Create Process${NC}"
echo "• Watch for successful key pair import with your specific public key"
echo "• Verify instance creation and Elastic IP association"
echo "• Note the final Elastic IP address"
echo ""

echo -e "${YELLOW}Step 5: Test SSH Access${NC}"
echo "After the create workflow completes, test SSH with:"
echo ""
echo -e "${GREEN}ssh -i finbert-rag-key-new.pem ubuntu@<ELASTIC_IP>${NC}"
echo ""
echo "Replace <ELASTIC_IP> with the IP shown in workflow output"
echo ""

echo -e "${BLUE}🔍 What to Look For:${NC}"
echo "✅ Destroy workflow completes without dependency errors"
echo "✅ Create workflow imports your hardcoded public key (not generates new)"
echo "✅ SSH connection works immediately after infrastructure creation"
echo "✅ Same Elastic IP is reused from previous deployment"
echo ""

echo -e "${BLUE}🎯 Success Criteria:${NC}"
echo "• No SSH key generation messages in create workflow"
echo "• Message shows 'Key pair finbert-rag-key already exists, importing public key'"
echo "• SSH works without any additional configuration"
echo "• Infrastructure can be destroyed and recreated reliably"
echo ""

echo -e "${YELLOW}⚠️  If SSH Still Fails After This Fix:${NC}"
echo "1. Check workflow logs for key import messages"
echo "2. Verify the public key matches your private key"
echo "3. Ensure AWS region consistency (ap-south-1)"
echo "4. Check security group rules in workflow output"
echo ""

echo -e "${GREEN}🚀 Once SSH is working consistently:${NC}"
echo "We can proceed to Phase 2 - Container Registry setup!"
echo ""

# Display current infrastructure status
echo -e "${BLUE}📊 Current Infrastructure Status:${NC}"
echo "Checking for existing resources..."

# Check for Elastic IP
ELASTIC_IP=$(aws ec2 describe-addresses --filters "Name=tag:Name,Values=finbert-rag-eip" --query 'Addresses[0].PublicIp' --output text 2>/dev/null || echo "None")
if [ "$ELASTIC_IP" != "None" ] && [ "$ELASTIC_IP" != "null" ]; then
    echo -e "${GREEN}✅ Elastic IP exists: $ELASTIC_IP${NC}"
else
    echo -e "${YELLOW}⚠️  No Elastic IP found${NC}"
fi

# Check for running instances
INSTANCE_COUNT=$(aws ec2 describe-instances --filters "Name=tag:Name,Values=finbert-rag-instance" "Name=instance-state-name,Values=running" --query 'length(Reservations[].Instances[])' --output text 2>/dev/null || echo "0")
echo -e "${BLUE}Running instances: $INSTANCE_COUNT${NC}"

echo ""
echo -e "${GREEN}Ready to test! Go to GitHub Actions and start with the destroy workflow.${NC}"