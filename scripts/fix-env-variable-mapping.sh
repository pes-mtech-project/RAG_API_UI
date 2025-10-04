#!/bin/bash

# Script to fix ECS task definition environment variable mapping
set -e

echo "🔧 Fixing ECS Environment Variable Mapping"
echo "=========================================="

# Configuration
AWS_REGION="ap-south-1"
CLUSTER_NAME="finbert-rag-prod-cluster"
SERVICE_NAME="finbert-api-prod"
TASK_FAMILY="FinBertRagProdStackFinBertServiceTaskDef7528D272"

# ECR Image URIs
AWS_ACCOUNT_ID="322158030810"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
API_IMAGE="${ECR_REGISTRY}/finbert-rag/api:v2.0.0"

# AWS Secrets Manager ARNs
ELASTICSEARCH_SECRET_ARN="arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:finbert-rag/elasticsearch/credentials-whpHeW"
API_TOKENS_SECRET_ARN="arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:finbert-rag/api/tokens-YLBFer"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠️]${NC} $1"; }

echo "The issue: Application expects ES_READONLY_HOST and ES_READONLY_KEY,"
echo "but we configured ES_CLOUD_HOST and ES_CLOUD_KEY in Secrets Manager."
echo
log_info "Fixing environment variable names to match application expectations..."

# Get current task definition
log_info "Getting current task definition..."
CURRENT_TASK_DEF=$(aws ecs describe-task-definition \
    --task-definition ${TASK_FAMILY} \
    --region ${AWS_REGION} \
    --query 'taskDefinition' \
    --output json)

# Update with correct environment variable names
log_info "Updating task definition with correct variable names..."
UPDATED_TASK_DEF=$(echo "${CURRENT_TASK_DEF}" | jq \
    --arg API_IMAGE "${API_IMAGE}" \
    --arg ES_SECRET_ARN "${ELASTICSEARCH_SECRET_ARN}" \
    --arg API_SECRET_ARN "${API_TOKENS_SECRET_ARN}" \
    '
    .containerDefinitions |= map(
        if .name == "finbert-api" then 
            .image = $API_IMAGE |
            .secrets = [
                {
                    "name": "ES_READONLY_HOST",
                    "valueFrom": ($ES_SECRET_ARN + ":host::")
                },
                {
                    "name": "ES_UNRESTRICTED_KEY", 
                    "valueFrom": ($ES_SECRET_ARN + ":key::")
                },
                {
                    "name": "ES_CLOUD_INDEX",
                    "valueFrom": ($ES_SECRET_ARN + ":index::")
                },
                {
                    "name": "HUGGINGFACE_TOKEN",
                    "valueFrom": ($API_SECRET_ARN + ":huggingface_token::")
                }
            ] |
            .environment = ([
                {"name": "API_HOST", "value": "0.0.0.0"},
                {"name": "API_PORT", "value": "8000"},
                {"name": "ENVIRONMENT", "value": "prod"}
            ])
        else . end
    ) 
    | del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .placementConstraints, .compatibilities, .registeredAt, .registeredBy)
    ')

# Save and register new task definition
echo "${UPDATED_TASK_DEF}" > fixed-task-def.json
log_info "Registering new task definition with correct variable names..."

NEW_TASK_DEF_ARN=$(aws ecs register-task-definition \
    --cli-input-json file://fixed-task-def.json \
    --region ${AWS_REGION} \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

if [ $? -eq 0 ]; then
    log_success "New task definition registered: ${NEW_TASK_DEF_ARN}"
else
    echo "Failed to register new task definition"
    exit 1
fi

# Update ECS service
log_info "Updating ECS service..."
aws ecs update-service \
    --cluster ${CLUSTER_NAME} \
    --service ${SERVICE_NAME} \
    --task-definition "${NEW_TASK_DEF_ARN}" \
    --region ${AWS_REGION} > /dev/null

log_success "ECS service update initiated"
log_info "Waiting for deployment to complete..."

# Wait for deployment
aws ecs wait services-stable \
    --cluster ${CLUSTER_NAME} \
    --services ${SERVICE_NAME} \
    --region ${AWS_REGION}

log_success "Deployment completed!"

echo
log_info "Variable mapping fixed:"
echo "  AWS Secrets:     Application Config:"
echo "  ES_CLOUD_HOST  → ES_READONLY_HOST ✓"
echo "  ES_CLOUD_KEY   → ES_UNRESTRICTED_KEY ✓"
echo "  ES_CLOUD_INDEX → ES_CLOUD_INDEX"

# Test the service
log_info "Testing the service..."
sleep 15

HEALTH_RESPONSE=$(curl -s "http://FinBer-FinBe-CK5al0msPiSr-619953726.ap-south-1.elb.amazonaws.com/health" --connect-timeout 10 --max-time 15)

echo "Health Response: $HEALTH_RESPONSE"

if echo "$HEALTH_RESPONSE" | grep -q '"elasticsearch":"accessible"'; then
    log_success "🎉 Success! Elasticsearch is now accessible!"
elif echo "$HEALTH_RESPONSE" | grep -q '"elasticsearch":"red"'; then
    log_warning "Still red - may need a few more minutes for the new task to fully start"
else
    echo "Check the response above"
fi

# Test embedding endpoint
log_info "Testing new embedding endpoint..."
ENDPOINT_TEST=$(curl -X POST "http://FinBer-FinBe-CK5al0msPiSr-619953726.ap-south-1.elb.amazonaws.com/search/cosine/embedding1155d/" \
    -H "Content-Type: application/json" \
    -d '{"query": "financial markets", "size": 1}' \
    --connect-timeout 10 --max-time 20 -s -w "%{http_code}")

HTTP_CODE="${ENDPOINT_TEST: -3}"
if [ "$HTTP_CODE" = "200" ]; then
    log_success "🚀 New embedding endpoint is working!"
else
    log_warning "Endpoint returned HTTP $HTTP_CODE - may still be starting up"
fi

# Cleanup
rm -f fixed-task-def.json

echo
log_success "🎉 Environment variable mapping fix completed!"