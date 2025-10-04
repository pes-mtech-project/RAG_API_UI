#!/bin/bash

# ECS Service Update Script - Manual deployment for new ECR images
# Use this when GitHub Actions fails due to billing limits

set -e

echo "🔄 Manual ECS Service Update with New ECR Images"
echo "================================================"

# Configuration
AWS_REGION="ap-south-1"
CLUSTER_NAME="finbert-rag-prod-cluster"
SERVICE_NAME="finbert-api-prod"
TASK_FAMILY="FinBertRagProdStackFinBertServiceTaskDef7528D272"

# ECR Image URIs (from successful build)
AWS_ACCOUNT_ID="322158030810"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
API_IMAGE="${ECR_REGISTRY}/finbert-rag/api:v2.0.0"
UI_IMAGE="${ECR_REGISTRY}/finbert-rag/ui:v2.0.0"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✅]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠️]${NC} $1"; }
log_error() { echo -e "${RED}[❌]${NC} $1"; }

# Check if ECS service exists
check_ecs_service() {
    log_info "Checking ECS service status..."
    
    if aws ecs describe-services \
        --cluster ${CLUSTER_NAME} \
        --services ${SERVICE_NAME} \
        --region ${AWS_REGION} \
        --query 'services[0].serviceName' \
        --output text 2>/dev/null; then
        log_success "ECS service found: ${SERVICE_NAME}"
        return 0
    else
        log_error "ECS service not found: ${SERVICE_NAME}"
        return 1
    fi
}

# Get current task definition
get_current_task_definition() {
    log_info "Retrieving current task definition..."
    
    # Get the current task definition
    CURRENT_TASK_DEF=$(aws ecs describe-task-definition \
        --task-definition ${TASK_FAMILY} \
        --region ${AWS_REGION} \
        --query 'taskDefinition' \
        --output json)
    
    if [ $? -eq 0 ]; then
        log_success "Current task definition retrieved"
        echo "${CURRENT_TASK_DEF}" > current-task-def.json
    else
        log_error "Failed to retrieve task definition"
        exit 1
    fi
}

# Update task definition with new ECR images
update_task_definition() {
    log_info "Updating task definition with new ECR images..."
    log_info "API Image: ${API_IMAGE}"
    log_info "UI Image: ${UI_IMAGE}"
    
    # Update the task definition with new images
    UPDATED_TASK_DEF=$(echo "${CURRENT_TASK_DEF}" | jq \
        --arg API_IMAGE "${API_IMAGE}" \
        --arg UI_IMAGE "${UI_IMAGE}" \
        '
        .containerDefinitions |= map(
            if .name == "finbert-api" then 
                .image = $API_IMAGE
            elif .name == "finbert-ui" then 
                .image = $UI_IMAGE
            else . end
        ) 
        | del(.taskDefinitionArn, .revision, .status, .requiresAttributes, .placementConstraints, .compatibilities, .registeredAt, .registeredBy)
        ')
    
    # Save updated task definition
    echo "${UPDATED_TASK_DEF}" > updated-task-def.json
    log_success "Task definition updated with new images"
}

# Register new task definition
register_new_task_definition() {
    log_info "Registering new task definition..."
    
    NEW_TASK_DEF_ARN=$(aws ecs register-task-definition \
        --cli-input-json file://updated-task-def.json \
        --region ${AWS_REGION} \
        --query 'taskDefinition.taskDefinitionArn' \
        --output text)
    
    if [ $? -eq 0 ]; then
        log_success "New task definition registered: ${NEW_TASK_DEF_ARN}"
    else
        log_error "Failed to register new task definition"
        exit 1
    fi
}

# Update ECS service
update_ecs_service() {
    log_info "Updating ECS service with new task definition..."
    
    aws ecs update-service \
        --cluster ${CLUSTER_NAME} \
        --service ${SERVICE_NAME} \
        --task-definition "${NEW_TASK_DEF_ARN}" \
        --region ${AWS_REGION} > /dev/null
    
    if [ $? -eq 0 ]; then
        log_success "ECS service update initiated"
    else
        log_error "Failed to update ECS service"
        exit 1
    fi
}

# Wait for deployment to complete
wait_for_deployment() {
    log_info "Waiting for deployment to stabilize..."
    log_warning "This may take 5-10 minutes..."
    
    aws ecs wait services-stable \
        --cluster ${CLUSTER_NAME} \
        --services ${SERVICE_NAME} \
        --region ${AWS_REGION}
    
    if [ $? -eq 0 ]; then
        log_success "Deployment completed successfully!"
    else
        log_error "Deployment failed or timed out"
        exit 1
    fi
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Get service status
    SERVICE_STATUS=$(aws ecs describe-services \
        --cluster ${CLUSTER_NAME} \
        --services ${SERVICE_NAME} \
        --region ${AWS_REGION} \
        --query 'services[0].deployments[0]' \
        --output json)
    
    RUNNING_COUNT=$(echo "${SERVICE_STATUS}" | jq -r '.runningCount')
    DESIRED_COUNT=$(echo "${SERVICE_STATUS}" | jq -r '.desiredCount')
    STATUS=$(echo "${SERVICE_STATUS}" | jq -r '.status')
    
    log_info "Service Status: ${STATUS}"
    log_info "Running Tasks: ${RUNNING_COUNT}/${DESIRED_COUNT}"
    
    if [ "${STATUS}" = "PRIMARY" ] && [ "${RUNNING_COUNT}" -eq "${DESIRED_COUNT}" ]; then
        log_success "Deployment verification successful!"
        return 0
    else
        log_warning "Deployment may still be in progress"
        return 1
    fi
}

# Test API endpoints
test_api_endpoints() {
    log_info "Testing API endpoints..."
    
    # Get load balancer DNS
    ALB_DNS=$(aws elbv2 describe-load-balancers \
        --query 'LoadBalancers[0].DNSName' \
        --output text \
        --region ${AWS_REGION} 2>/dev/null)
    
    if [ -z "${ALB_DNS}" ] || [ "${ALB_DNS}" = "None" ]; then
        log_warning "Could not retrieve load balancer DNS. Manual testing required."
        return 1
    fi
    
    log_info "Load Balancer DNS: ${ALB_DNS}"
    
    # Test health endpoint
    log_info "Testing health endpoint..."
    if curl -f -s --connect-timeout 10 "https://${ALB_DNS}/health" > /dev/null; then
        log_success "Health endpoint responding ✓"
    else
        log_warning "Health endpoint not responding (may still be starting)"
    fi
    
    # Test new embedding endpoints
    log_info "Testing new embedding endpoints..."
    
    for endpoint in "embedding384d" "embedding768d" "embedding1155d"; do
        log_info "Testing ${endpoint}..."
        RESPONSE=$(curl -X POST "https://${ALB_DNS}/search/cosine/${endpoint}/" \
            -H "Content-Type: application/json" \
            -d '{"query": "test deployment", "size": 1}' \
            --connect-timeout 10 --max-time 30 -s -w "%{http_code}")
        
        HTTP_CODE="${RESPONSE: -3}"
        if [ "${HTTP_CODE}" = "200" ]; then
            log_success "${endpoint} endpoint working ✅"
        else
            log_warning "${endpoint} endpoint returned HTTP ${HTTP_CODE}"
        fi
    done
}

# Cleanup temporary files
cleanup() {
    log_info "Cleaning up temporary files..."
    rm -f current-task-def.json updated-task-def.json
    log_success "Cleanup completed"
}

# Main execution
main() {
    log_info "Starting manual ECS service update..."
    
    # Verify prerequisites
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        log_error "jq not found. Install with: brew install jq"
        exit 1
    fi
    
    # Execute deployment steps
    check_ecs_service
    get_current_task_definition
    update_task_definition
    register_new_task_definition
    update_ecs_service
    wait_for_deployment
    
    # Verification
    if verify_deployment; then
        test_api_endpoints
        log_success "🎉 Manual ECS deployment completed successfully!"
        echo
        echo "✅ New ECR images deployed:"
        echo "   API: ${API_IMAGE}"
        echo "   UI: ${UI_IMAGE}"
        echo
        echo "🧪 Test the new endpoints:"
        echo "   https://${ALB_DNS}/search/cosine/embedding384d/"
        echo "   https://${ALB_DNS}/search/cosine/embedding768d/"
        echo "   https://${ALB_DNS}/search/cosine/embedding1155d/"
    else
        log_warning "Deployment completed but verification had issues"
        log_info "Check ECS console for detailed status"
    fi
    
    cleanup
}

# Execute main function
main "$@"