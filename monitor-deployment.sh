#!/bin/bash

# Monitor GitHub Actions deployment and test API endpoints
# This script watches the deployment progress and runs tests when complete

REPO="pes-mtech-project/RAG_API_UI"
API_URL="http://finber-finbe-mlc1emju4jnw-1497871200.ap-south-1.elb.amazonaws.com"

echo "🚀 Monitoring GitHub Actions Deployment Progress"
echo "=================================================="

# Function to check workflow status
check_workflow_status() {
    local workflow_id=$1
    gh run view $workflow_id --repo $REPO --json status,conclusion | jq -r '.status + " - " + (.conclusion // "running")'
}

# Get the latest workflow runs for develop branch
echo "📋 Getting latest workflow runs..."
WORKFLOWS=$(gh run list --repo $REPO --branch develop --limit 3 --json databaseId,name,status,conclusion)

echo "🔍 Current Workflow Status:"
echo "$WORKFLOWS" | jq -r '.[] | "  " + .name + ": " + .status + " (" + (.conclusion // "running") + ")"'

# Monitor until completion
echo ""
echo "⏳ Monitoring deployment progress..."
echo "Press Ctrl+C to stop monitoring"

DEPLOYMENT_COMPLETE=false
CHECK_COUNT=0

while [ "$DEPLOYMENT_COMPLETE" = false ] && [ $CHECK_COUNT -lt 60 ]; do
    sleep 30
    CHECK_COUNT=$((CHECK_COUNT + 1))
    
    echo "📊 Check $CHECK_COUNT - $(date '+%H:%M:%S')"
    
    # Get current status
    CURRENT_WORKFLOWS=$(gh run list --repo $REPO --branch develop --limit 3 --json databaseId,name,status,conclusion)
    
    # Check if all workflows are completed
    RUNNING_COUNT=$(echo "$CURRENT_WORKFLOWS" | jq '[.[] | select(.status == "in_progress")] | length')
    
    if [ "$RUNNING_COUNT" -eq 0 ]; then
        echo "✅ All workflows completed!"
        DEPLOYMENT_COMPLETE=true
        
        # Show final status
        echo ""
        echo "📋 Final Workflow Status:"
        echo "$CURRENT_WORKFLOWS" | jq -r '.[] | "  " + .name + ": " + .status + " (" + (.conclusion // "unknown") + ")"'
        
        # Check for any failures
        FAILED_COUNT=$(echo "$CURRENT_WORKFLOWS" | jq '[.[] | select(.conclusion == "failure")] | length')
        
        if [ "$FAILED_COUNT" -gt 0 ]; then
            echo ""
            echo "❌ Some workflows failed. Check the GitHub Actions page for details."
            echo "🔗 https://github.com/$REPO/actions"
        else
            echo ""
            echo "🎉 All workflows succeeded! Proceeding with API tests..."
        fi
    else
        echo "  Still running: $RUNNING_COUNT workflows"
        
        # Show brief status
        echo "$CURRENT_WORKFLOWS" | jq -r '.[] | select(.status == "in_progress") | "  ⏳ " + .name + ": building..."'
    fi
done

if [ "$DEPLOYMENT_COMPLETE" = false ]; then
    echo ""
    echo "⚠️  Timeout reached after 30 minutes. Deployment may still be in progress."
    echo "🔗 Check status at: https://github.com/$REPO/actions"
fi

# Wait a bit for deployment to propagate
echo ""
echo "⏳ Waiting 60 seconds for deployment to propagate..."
sleep 60

# Test API endpoints
echo ""
echo "🧪 Testing Updated API Endpoints"
echo "================================="

# Test health endpoint
echo "🔍 Testing Health Endpoint..."
HEALTH_RESPONSE=$(curl -s -w "%{http_code}" "$API_URL/health")
HEALTH_CODE="${HEALTH_RESPONSE: -3}"
if [ "$HEALTH_CODE" = "200" ]; then
    echo "✅ Health Check: OK"
else
    echo "❌ Health Check: Failed ($HEALTH_CODE)"
fi

# Test debug search endpoint
echo ""
echo "🔍 Testing Debug Search Endpoint..."
DEBUG_RESPONSE=$(curl -s -w "%{http_code}" -X POST "$API_URL/debug_search" \
    -H "Content-Type: application/json" \
    -d '{"query": "HDFC Bank Finance", "limit": 5, "min_score": 0.2}')
DEBUG_CODE="${DEBUG_RESPONSE: -3}"

if [ "$DEBUG_CODE" = "200" ]; then
    echo "✅ Debug Search: Available"
    echo "📊 Debug Response:"
    echo "${DEBUG_RESPONSE%???}" | jq '.' 2>/dev/null || echo "${DEBUG_RESPONSE%???}"
elif [ "$DEBUG_CODE" = "404" ]; then
    echo "⚠️  Debug Search: Not yet deployed (404)"
else
    echo "❌ Debug Search: Error ($DEBUG_CODE)"
fi

# Test pregenerated search endpoint
echo ""
echo "🔍 Testing Test Search Endpoint..."
TEST_RESPONSE=$(curl -s -w "%{http_code}" -X POST "$API_URL/test_search" \
    -H "Content-Type: application/json" \
    -d '{"use_pregenerated": true}')
TEST_CODE="${TEST_RESPONSE: -3}"

if [ "$TEST_CODE" = "200" ]; then
    echo "✅ Test Search: Available"
    RESULT_COUNT=$(echo "${TEST_RESPONSE%???}" | jq 'length' 2>/dev/null || echo "0")
    echo "📊 Found $RESULT_COUNT results"
elif [ "$TEST_CODE" = "404" ]; then
    echo "⚠️  Test Search: Not yet deployed (404)"
else
    echo "❌ Test Search: Error ($TEST_CODE)"
fi

# Test original search endpoint
echo ""
echo "🔍 Testing Original Search Endpoint..."
SEARCH_RESPONSE=$(curl -s -w "%{http_code}" -X POST "$API_URL/search" \
    -H "Content-Type: application/json" \
    -d '{"query": "HDFC Bank Finance", "limit": 5, "min_score": 0.1}')
SEARCH_CODE="${SEARCH_RESPONSE: -3}"

if [ "$SEARCH_CODE" = "200" ]; then
    echo "✅ Original Search: Available"
    RESULT_COUNT=$(echo "${SEARCH_RESPONSE%???}" | jq 'length' 2>/dev/null || echo "0")
    echo "📊 Found $RESULT_COUNT results"
    
    if [ "$RESULT_COUNT" = "0" ]; then
        echo "⚠️  Still returning empty results - embedding issue may persist"
    else
        echo "🎉 Search is working! Issue appears to be resolved."
    fi
else
    echo "❌ Original Search: Error ($SEARCH_CODE)"
fi

echo ""
echo "🏁 Monitoring and Testing Complete"
echo "=================================="

# Final recommendations
if [ "$DEBUG_CODE" = "404" ] || [ "$TEST_CODE" = "404" ]; then
    echo ""
    echo "💡 Next Steps:"
    echo "1. New endpoints may take additional time to deploy"
    echo "2. Try running python3 test_search_api.py in 5-10 minutes"
    echo "3. Check ECS task logs for any deployment issues"
    echo "4. Monitor at: https://github.com/$REPO/actions"
fi