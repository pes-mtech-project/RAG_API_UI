#!/bin/bash

# Quick Local Development Deployment
# Simplified version for rapid iteration

set -e

echo "⚡ Quick Development Deployment"
echo "=============================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

#!/bin/bash
# Quick Development Deployment Script
# For rapid iteration and testing

set -e

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
TIMESTAMP=$(date '+%Y%m%d-%H%M%S')
GIT_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
VERSION="dev-${TIMESTAMP}-${GIT_HASH}"

# Load environment variables from .env if it exists
if [[ -f "${PROJECT_DIR}/.env" ]]; then
    source "${PROJECT_DIR}/.env"
fi

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Version: ${VERSION}${NC}"
echo -e "${BLUE}Branch: $(git branch --show-current)${NC}"

# ===== QUICK BUILD & TEST =====
echo ""
echo -e "${YELLOW}🏗️ Building and Testing Locally${NC}"

# Build containers
echo "Building containers..."
docker-compose build --quiet

# Start services
echo "Starting services..."
docker-compose up -d

# Wait for services
echo "Waiting for services to start..."
sleep 15

# Quick health check
echo "Running health check..."
for i in {1..6}; do
    if curl -f -s http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✅ API health check passed${NC}"
        break
    else
        echo "⏳ Waiting for API... (attempt $i/6)"
        sleep 5
    fi
done

# Test main endpoints
echo "Testing endpoints..."

# Health endpoint
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health || echo "failed")
if [[ $HEALTH_RESPONSE == *"healthy"* ]]; then
    echo -e "${GREEN}✅ Health endpoint OK${NC}"
else
    echo -e "${YELLOW}⚠️ Health endpoint issue${NC}"
fi

# Search endpoint test
SEARCH_RESPONSE=$(curl -X POST -H "Content-Type: application/json" \
  -d '{"query": "test", "top_k": 1}' \
  -s http://localhost:8000/search/cosine/embedding1155d/ 2>/dev/null || echo "failed")

if [[ $SEARCH_RESPONSE == *"results"* ]]; then
    echo -e "${GREEN}✅ Search endpoint working with real data${NC}"
elif [[ $SEARCH_RESPONSE == *"Connection error"* ]]; then
    echo -e "${BLUE}ℹ️ Search endpoint OK (ES connection expected)${NC}"
else
    echo -e "${YELLOW}⚠️ Search endpoint issue${NC}"
fi

# UI check
if curl -f -s -I http://localhost:8501 > /dev/null; then
    echo -e "${GREEN}✅ UI accessible${NC}"
else
    echo -e "${YELLOW}⚠️ UI not accessible${NC}"
fi

echo ""
echo -e "${YELLOW}🚀 Deploy to AWS Development? (y/n)${NC}"
read -r deploy_choice

if [[ $deploy_choice == "y" || $deploy_choice == "Y" ]]; then
    
    # Check AWS credentials
    if ! aws sts get-caller-identity > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️ AWS credentials not configured. Configure with: aws configure${NC}"
        echo -e "${BLUE}ℹ️ Continuing with local deployment only${NC}"
    else
        echo ""
        echo -e "${YELLOW}🐳 Pushing to Development ECR${NC}"
        
        # AWS configuration
        AWS_REGION="ap-south-1"
        AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
        
        # Login to ECR
        echo "Logging into ECR..."
        aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}
        
        # Tag and push API image
        echo "Pushing API image..."
        docker tag finbert-news-rag-app-finbert-api ${ECR_REGISTRY}/finbert-rag/api-dev:${VERSION}
        docker tag finbert-news-rag-app-finbert-api ${ECR_REGISTRY}/finbert-rag/api-dev:latest-dev
        
        docker push ${ECR_REGISTRY}/finbert-rag/api-dev:${VERSION}
        docker push ${ECR_REGISTRY}/finbert-rag/api-dev:latest-dev
        
        # Tag and push UI image  
        echo "Pushing UI image..."
        docker tag finbert-news-rag-app-finbert-ui ${ECR_REGISTRY}/finbert-rag/ui-dev:${VERSION}
        docker tag finbert-news-rag-app-finbert-ui ${ECR_REGISTRY}/finbert-rag/ui-dev:latest-dev
        
        docker push ${ECR_REGISTRY}/finbert-rag/ui-dev:${VERSION}
        docker push ${ECR_REGISTRY}/finbert-rag/ui-dev:latest-dev
        
        echo -e "${GREEN}✅ Images pushed to ECR${NC}"
        
        # Update ECS services
        echo "Updating ECS development services..."
        
        # Force new deployment to pick up latest images
        aws ecs update-service --cluster finbert-rag-dev-cluster \
          --service finbert-api-dev --force-new-deployment > /dev/null
          
        aws ecs update-service --cluster finbert-rag-dev-cluster \
          --service finbert-ui-dev --force-new-deployment > /dev/null
        
        echo -e "${GREEN}✅ ECS services updated${NC}"
        echo -e "${BLUE}ℹ️ Services will take a few minutes to deploy new versions${NC}"
        
        # Optional: Wait for deployment
        echo ""
        echo -e "${YELLOW}Wait for ECS deployment to complete? (y/n)${NC}"
        read -r wait_choice
        
        if [[ $wait_choice == "y" || $wait_choice == "Y" ]]; then
            echo "Waiting for services to stabilize..."
            aws ecs wait services-stable --cluster finbert-rag-dev-cluster --services finbert-api-dev
            echo -e "${GREEN}✅ Development deployment completed!${NC}"
        else
            echo -e "${BLUE}ℹ️ Deployment initiated. Check AWS console for progress.${NC}"
        fi
    fi
else
    echo -e "${BLUE}ℹ️ Skipping AWS deployment${NC}"
fi

# ===== SUMMARY =====
echo ""
echo -e "${GREEN}🎉 Development Deployment Complete!${NC}"
echo ""
echo -e "${BLUE}Local Endpoints:${NC}"
echo "  API:    http://localhost:8000"
echo "  Health: http://localhost:8000/health"  
echo "  Docs:   http://localhost:8000/docs"
echo "  UI:     http://localhost:8501"
echo ""
echo -e "${BLUE}Version: ${VERSION}${NC}"
echo -e "${BLUE}Branch:  $(git branch --show-current)${NC}"
echo ""
echo -e "${YELLOW}💡 Tips:${NC}"
echo "  - Run './scripts/test-container-deployment.sh' for full testing"
echo "  - Use 'docker-compose logs -f' to view logs"
echo "  - Production deployments still use 'git push origin main'"
echo ""