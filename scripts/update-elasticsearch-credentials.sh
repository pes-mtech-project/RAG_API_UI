#!/bin/bash

# Script to update Elasticsearch credentials in AWS Secrets Manager
# Run this script with the new credentials to update the production environment

set -e

echo "🔐 Update Elasticsearch Credentials in AWS Secrets Manager"
echo "========================================================="

# Configuration
AWS_REGION="ap-south-1"
SECRET_NAME="finbert-rag/elasticsearch/credentials"

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

# Function to update credentials
update_elasticsearch_credentials() {
    log_info "Current Elasticsearch credentials will be updated..."
    
    # Prompt for new credentials
    echo
    log_info "Please provide the new Elasticsearch credentials:"
    echo
    read -p "Elasticsearch Host (e.g., https://cluster.es.region.cloud.es.io:443): " ES_HOST
    read -p "Elasticsearch Index (e.g., news_finbert_embeddings): " ES_INDEX  
    read -s -p "Elasticsearch API Key: " ES_KEY
    echo
    echo
    
    # Validate inputs
    if [ -z "$ES_HOST" ] || [ -z "$ES_INDEX" ] || [ -z "$ES_KEY" ]; then
        log_error "All fields are required!"
        exit 1
    fi
    
    # Create JSON payload
    SECRET_VALUE=$(jq -n \
        --arg host "$ES_HOST" \
        --arg index "$ES_INDEX" \
        --arg key "$ES_KEY" \
        '{
            host: $host,
            index: $index,
            key: $key
        }')
    
    log_info "Updating AWS Secrets Manager..."
    
    # Update the secret
    aws secretsmanager update-secret \
        --secret-id "$SECRET_NAME" \
        --secret-string "$SECRET_VALUE" \
        --region "$AWS_REGION" > /dev/null
    
    if [ $? -eq 0 ]; then
        log_success "Elasticsearch credentials updated successfully!"
    else
        log_error "Failed to update credentials"
        exit 1
    fi
}

# Function to force ECS deployment
force_ecs_deployment() {
    log_info "Forcing ECS service deployment to pick up new credentials..."
    
    aws ecs update-service \
        --cluster finbert-rag-prod-cluster \
        --service finbert-api-prod \
        --force-new-deployment \
        --region "$AWS_REGION" > /dev/null
    
    if [ $? -eq 0 ]; then
        log_success "ECS deployment initiated"
        log_info "Waiting for deployment to complete (this may take 5-10 minutes)..."
        
        aws ecs wait services-stable \
            --cluster finbert-rag-prod-cluster \
            --services finbert-api-prod \
            --region "$AWS_REGION"
        
        log_success "ECS deployment completed!"
    else
        log_error "Failed to initiate ECS deployment"
        exit 1
    fi
}

# Function to test the updated service
test_updated_service() {
    log_info "Testing the updated service..."
    
    ALB_DNS="FinBer-FinBe-CK5al0msPiSr-619953726.ap-south-1.elb.amazonaws.com"
    
    # Test health endpoint
    log_info "Testing health endpoint..."
    HEALTH_RESPONSE=$(curl -s "http://${ALB_DNS}/health" --connect-timeout 10 --max-time 15)
    
    echo "Health Response: $HEALTH_RESPONSE"
    
    # Check if Elasticsearch status improved
    if echo "$HEALTH_RESPONSE" | grep -q '"elasticsearch":"accessible"'; then
        log_success "Elasticsearch connection is now accessible! ✅"
    elif echo "$HEALTH_RESPONSE" | grep -q '"elasticsearch":"red"'; then
        log_warning "Elasticsearch still shows as 'red' - may need to check credentials again"
    else
        log_info "Health check completed, review response above"
    fi
    
    # Test new embedding endpoint
    log_info "Testing new embedding endpoint..."
    
    ENDPOINT_RESPONSE=$(curl -X POST "http://${ALB_DNS}/search/cosine/embedding1155d/" \
        -H "Content-Type: application/json" \
        -d '{"query": "financial markets test", "size": 1}' \
        --connect-timeout 10 --max-time 20 -s -w "%{http_code}")
    
    HTTP_CODE="${ENDPOINT_RESPONSE: -3}"
    RESPONSE_BODY="${ENDPOINT_RESPONSE%???}"
    
    if [ "$HTTP_CODE" = "200" ]; then
        log_success "New embedding endpoint working! ✅"
        echo "Response preview: ${RESPONSE_BODY:0:100}..."
    else
        log_warning "Embedding endpoint returned HTTP $HTTP_CODE"
        if [ -n "$RESPONSE_BODY" ]; then
            echo "Response: $RESPONSE_BODY"
        fi
    fi
}

# Main execution
main() {
    log_info "Starting Elasticsearch credentials update process..."
    echo
    log_warning "This will update production Elasticsearch credentials and restart the service"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Operation cancelled"
        exit 0
    fi
    
    # Execute update process
    update_elasticsearch_credentials
    force_ecs_deployment
    test_updated_service
    
    echo
    log_success "🎉 Elasticsearch credentials update completed!"
    echo
    echo "✅ Updated components:"
    echo "   - AWS Secrets Manager credentials"
    echo "   - ECS service redeployed with new credentials"  
    echo "   - API endpoints tested"
    echo
    echo "🧪 Test the endpoints:"
    echo "   http://${ALB_DNS}/health"
    echo "   http://${ALB_DNS}/search/cosine/embedding384d/"
    echo "   http://${ALB_DNS}/search/cosine/embedding768d/"
    echo "   http://${ALB_DNS}/search/cosine/embedding1155d/"
}

# Execute main function
main "$@"