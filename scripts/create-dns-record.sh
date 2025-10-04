#!/bin/bash

# 🌐 Simple Route53 CNAME Record Creation
set -e

# Configuration
HOSTED_ZONE_ID="Z0338885B3LPG5PPUGOI"
DOMAIN_NAME="news-rag-dev.lauki.co"
TARGET_ENDPOINT="finber-finbe-mlc1emju4jnw-1497871200.ap-south-1.elb.amazonaws.com"

echo "🌐 Creating CNAME record: $DOMAIN_NAME -> $TARGET_ENDPOINT"

# Create the change batch JSON
cat > /tmp/route53-change.json << EOF
{
    "Changes": [{
        "Action": "UPSERT",
        "ResourceRecordSet": {
            "Name": "$DOMAIN_NAME",
            "Type": "CNAME",
            "TTL": 300,
            "ResourceRecords": [{
                "Value": "$TARGET_ENDPOINT"
            }]
        }
    }]
}
EOF

echo "📋 Change batch:"
cat /tmp/route53-change.json

echo ""
echo "🚀 Submitting DNS change..."

# Submit the change
CHANGE_INFO=$(aws route53 change-resource-record-sets \
    --hosted-zone-id "$HOSTED_ZONE_ID" \
    --change-batch file:///tmp/route53-change.json \
    --output json)

CHANGE_ID=$(echo "$CHANGE_INFO" | jq -r '.ChangeInfo.Id')
echo "✅ Change submitted with ID: $CHANGE_ID"

echo "⏳ Waiting for DNS propagation..."
aws route53 wait resource-record-sets-changed --id "$CHANGE_ID"

echo "✅ DNS record created successfully!"
echo "🌐 Test URL: http://$DOMAIN_NAME/health"

# Cleanup
rm -f /tmp/route53-change.json

echo ""
echo "🔍 Verifying DNS record..."
sleep 10
dig +short "$DOMAIN_NAME" CNAME

echo ""
echo "🎉 Done! Your dev endpoint is now available at: http://$DOMAIN_NAME"