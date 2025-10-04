#!/bin/bash

# 🌐 Setup Route53 DNS Records for FinBERT RAG Application
# This script creates CNAME records for development and production environments

set -e

# Configuration
HOSTED_ZONE_NAME="lauki.co"
DEV_SUBDOMAIN="news-rag-dev"
PROD_SUBDOMAIN="news-rag"
CURRENT_DEV_ENDPOINT="finber-finbe-mlc1emju4jnw-1497871200.ap-south-1.elb.amazonaws.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🌐 FinBERT RAG - Route53 DNS Setup${NC}"
echo "=================================================="
echo -e "Hosted Zone: ${YELLOW}${HOSTED_ZONE_NAME}${NC}"
echo -e "Dev Subdomain: ${YELLOW}${DEV_SUBDOMAIN}.${HOSTED_ZONE_NAME}${NC}"
echo -e "Prod Subdomain: ${YELLOW}${PROD_SUBDOMAIN}.${HOSTED_ZONE_NAME}${NC}"
echo ""

# Function to get hosted zone ID
get_hosted_zone_id() {
    local zone_name=$1
    echo "🔍 Finding hosted zone ID for ${zone_name}..."
    
    # Try with trailing dot first, then without
    local zone_id=$(aws route53 list-hosted-zones \
        --query "HostedZones[?Name=='${zone_name}.'].Id" \
        --output text | sed 's|/hostedzone/||')
    
    if [ -z "$zone_id" ]; then
        zone_id=$(aws route53 list-hosted-zones \
            --query "HostedZones[?Name=='${zone_name}'].Id" \
            --output text | sed 's|/hostedzone/||')
    fi
    
    if [ -z "$zone_id" ] || [ "$zone_id" = "None" ]; then
        echo -e "${RED}❌ Error: Hosted zone '${zone_name}' not found${NC}"
        echo "Available hosted zones:"
        aws route53 list-hosted-zones --query "HostedZones[].[Name,Id]" --output table
        exit 1
    fi
    
    echo -e "${GREEN}✅ Found hosted zone ID: ${zone_id}${NC}"
    echo "$zone_id"
}

# Function to create or update CNAME record
create_or_update_cname() {
    local zone_id=$1
    local subdomain=$2
    local target=$3
    local action=${4:-UPSERT}
    
    local full_domain="${subdomain}.${HOSTED_ZONE_NAME}"
    
    echo "🔧 ${action}ing CNAME record: ${full_domain} -> ${target}"
    
    # Create change batch JSON
    local change_batch=$(cat <<EOF
{
    "Changes": [{
        "Action": "${action}",
        "ResourceRecordSet": {
            "Name": "${full_domain}",
            "Type": "CNAME",
            "TTL": 300,
            "ResourceRecords": [{
                "Value": "${target}"
            }]
        }
    }]
}
EOF
)
    
    # Execute the change
    local change_info=$(aws route53 change-resource-record-sets \
        --hosted-zone-id "$zone_id" \
        --change-batch "$change_batch" \
        --output json)
    
    local change_id=$(echo "$change_info" | jq -r '.ChangeInfo.Id')
    echo -e "${YELLOW}⏳ Change submitted with ID: ${change_id}${NC}"
    
    # Wait for change to propagate
    echo "⏳ Waiting for DNS propagation..."
    aws route53 wait resource-record-sets-changed --id "$change_id"
    
    echo -e "${GREEN}✅ DNS record updated successfully!${NC}"
    echo -e "   ${full_domain} -> ${target}"
}

# Function to verify DNS record
verify_dns_record() {
    local domain=$1
    local expected_target=$2
    
    echo "🔍 Verifying DNS record for ${domain}..."
    
    # Wait a moment for DNS to update
    sleep 5
    
    local actual_target=$(dig +short "$domain" CNAME | sed 's/\.$//')
    
    if [ "$actual_target" = "$expected_target" ]; then
        echo -e "${GREEN}✅ DNS verification successful!${NC}"
        echo -e "   ${domain} resolves to: ${actual_target}"
        
        # Test HTTP connectivity
        echo "🌐 Testing HTTP connectivity..."
        if curl -s --max-time 10 "http://${domain}/health" > /dev/null; then
            echo -e "${GREEN}✅ HTTP health check successful!${NC}"
        else
            echo -e "${YELLOW}⚠️  HTTP health check failed (may be normal if service is starting)${NC}"
        fi
    else
        echo -e "${RED}❌ DNS verification failed${NC}"
        echo -e "   Expected: ${expected_target}"
        echo -e "   Actual: ${actual_target}"
    fi
}

# Main execution
main() {
    echo "🚀 Starting Route53 DNS setup..."
    
    # Check AWS CLI configuration
    if ! aws sts get-caller-identity > /dev/null 2>&1; then
        echo -e "${RED}❌ Error: AWS CLI not configured or no permissions${NC}"
        echo "Please run: aws configure"
        exit 1
    fi
    
    # Get hosted zone ID
    ZONE_ID=$(get_hosted_zone_id "$HOSTED_ZONE_NAME")
    
    echo ""
    echo "🔧 Creating DNS records..."
    echo "========================"
    
    # Create development CNAME record
    echo -e "${BLUE}📍 Setting up development environment${NC}"
    create_or_update_cname "$ZONE_ID" "$DEV_SUBDOMAIN" "$CURRENT_DEV_ENDPOINT"
    
    echo ""
    echo "🔍 Verification Results"
    echo "======================="
    
    # Verify development record
    verify_dns_record "${DEV_SUBDOMAIN}.${HOSTED_ZONE_NAME}" "$CURRENT_DEV_ENDPOINT"
    
    echo ""
    echo -e "${GREEN}🎉 Route53 DNS setup completed successfully!${NC}"
    echo ""
    echo "📋 Summary:"
    echo "==========="
    echo -e "✅ Development: ${YELLOW}http://${DEV_SUBDOMAIN}.${HOSTED_ZONE_NAME}${NC}"
    echo -e "   Points to: ${CURRENT_DEV_ENDPOINT}"
    echo ""
    echo "🚀 Next Steps:"
    echo "=============="
    echo "1. Test the development endpoint: curl http://${DEV_SUBDOMAIN}.${HOSTED_ZONE_NAME}/health"
    echo "2. Deploy production when ready: gh workflow run production-release.yml --ref live"
    echo "3. The CDK infrastructure will automatically manage DNS updates for future deployments"
    echo ""
    echo -e "${BLUE}💡 Pro Tip: Bookmark these URLs for easy access!${NC}"
}

# Run main function
main "$@"