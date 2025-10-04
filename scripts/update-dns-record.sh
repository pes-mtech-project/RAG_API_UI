#!/bin/bash

# 🔄 Update Route53 DNS Record for FinBERT RAG Deployment
# This script updates the CNAME record to point to the latest ALB endpoint

set -e

# Script parameters
ENVIRONMENT=${1:-"dev"}
ALB_DNS_NAME=${2:-""}
HOSTED_ZONE_ID="Z0338885B3LPG5PPUGOI"
HOSTED_ZONE_NAME="lauki.co"

# Configuration based on environment
if [ "$ENVIRONMENT" = "dev" ]; then
    SUBDOMAIN="news-rag-dev"
elif [ "$ENVIRONMENT" = "prod" ]; then
    SUBDOMAIN="news-rag"
else
    echo "❌ Error: Environment must be 'dev' or 'prod'"
    exit 1
fi

FULL_DOMAIN="${SUBDOMAIN}.${HOSTED_ZONE_NAME}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 Route53 DNS Update for FinBERT RAG${NC}"
echo "================================================"
echo -e "Environment: ${YELLOW}${ENVIRONMENT}${NC}"
echo -e "Domain: ${YELLOW}${FULL_DOMAIN}${NC}"
echo -e "Target: ${YELLOW}${ALB_DNS_NAME}${NC}"
echo ""

# Validation
if [ -z "$ALB_DNS_NAME" ]; then
    echo -e "${RED}❌ Error: ALB DNS name is required${NC}"
    echo "Usage: $0 <environment> <alb-dns-name>"
    echo "Example: $0 dev my-alb-123456789.ap-south-1.elb.amazonaws.com"
    exit 1
fi

# Check AWS CLI access
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: AWS CLI not configured or no permissions${NC}"
    exit 1
fi

# Get current DNS record (if exists)
echo "🔍 Checking current DNS record..."
CURRENT_TARGET=$(aws route53 list-resource-record-sets \
    --hosted-zone-id "$HOSTED_ZONE_ID" \
    --query "ResourceRecordSets[?Name=='${FULL_DOMAIN}.' && Type=='CNAME'].ResourceRecords[0].Value" \
    --output text 2>/dev/null || echo "None")

if [ "$CURRENT_TARGET" = "None" ] || [ -z "$CURRENT_TARGET" ]; then
    echo -e "${YELLOW}⚠️  No existing CNAME record found${NC}"
    ACTION="CREATE"
else
    echo -e "Current target: ${CURRENT_TARGET}"
    if [ "$CURRENT_TARGET" = "$ALB_DNS_NAME" ]; then
        echo -e "${GREEN}✅ DNS record is already up to date!${NC}"
        exit 0
    fi
    ACTION="UPSERT"
fi

# Create change batch
echo "🔧 ${ACTION}ing DNS record..."
CHANGE_BATCH=$(cat <<EOF
{
    "Changes": [{
        "Action": "${ACTION}",
        "ResourceRecordSet": {
            "Name": "${FULL_DOMAIN}",
            "Type": "CNAME",
            "TTL": 300,
            "ResourceRecords": [{
                "Value": "${ALB_DNS_NAME}"
            }]
        }
    }]
}
EOF
)

# Submit the change
CHANGE_INFO=$(aws route53 change-resource-record-sets \
    --hosted-zone-id "$HOSTED_ZONE_ID" \
    --change-batch "$CHANGE_BATCH" \
    --output json)

CHANGE_ID=$(echo "$CHANGE_INFO" | jq -r '.ChangeInfo.Id')
echo -e "${YELLOW}⏳ Change submitted with ID: ${CHANGE_ID}${NC}"

# Wait for propagation
echo "⏳ Waiting for DNS propagation..."
aws route53 wait resource-record-sets-changed --id "$CHANGE_ID"

echo -e "${GREEN}✅ DNS record updated successfully!${NC}"
echo ""

# Verification
echo "🔍 Verifying DNS record..."
sleep 5
VERIFIED_TARGET=$(dig +short "$FULL_DOMAIN" CNAME | sed 's/\.$//')

if [ "$VERIFIED_TARGET" = "$ALB_DNS_NAME" ]; then
    echo -e "${GREEN}✅ DNS verification successful!${NC}"
    echo -e "   ${FULL_DOMAIN} -> ${VERIFIED_TARGET}"
else
    echo -e "${YELLOW}⚠️  DNS propagation may still be in progress${NC}"
    echo -e "   Expected: ${ALB_DNS_NAME}"
    echo -e "   Current: ${VERIFIED_TARGET}"
fi

echo ""
echo -e "${GREEN}🎉 DNS update completed!${NC}"
echo -e "🌐 Test URL: ${BLUE}http://${FULL_DOMAIN}/health${NC}"

# Optional: Test HTTP connectivity
if command -v curl > /dev/null 2>&1; then
    echo ""
    echo "🌐 Testing HTTP connectivity..."
    if curl -s --max-time 10 "http://${FULL_DOMAIN}/health" > /dev/null; then
        echo -e "${GREEN}✅ HTTP health check successful!${NC}"
    else
        echo -e "${YELLOW}⚠️  HTTP health check failed (service may be starting up)${NC}"
    fi
fi